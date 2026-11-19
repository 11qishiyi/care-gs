"""Dump per-view grey renders / residuals for every scene x variant  (GPU node).

This is the *only* heavy step of the revision pipeline.  It renders every
held-out view once per variant with the same call the paper's main table uses
(``calib.gsrender.render``, chunk 4, gsplat 1.5.3, factor=4 images) and writes one
small ``.npz`` per scene.  Everything downstream (coverage, threshold sweeps,
the second task, region granularities) is pure-CPU numpy recomputation from those
artifacts, so the GPU node is needed for minutes, not hours.

Variants (all applied to the same released checkpoint, so nothing is retrained)

    clean     released ``point_cloud.ply``
    prune50   opacity top-50 % (the paper's baseline pruning rule)
    prune30   opacity top-30 %
    pup30     PUP / Fisher-diagonal top-30 %  (``make_pup_variant.py``)
    shdeg1    SH degree 1: bands >= 2 dropped at render time (a compression edit)
    quant8    every float attribute uniformly quantised to 8 bits (a storage edit)

``VARIANTS`` (above) is the published default and is deliberately **frozen**: the
default profile, the ``--profile`` presets and every existing artifact stay
exactly as they were.  The dose-sweep variants below are opt-in only (they need an
explicit ``--variants``), which is what the 2026-11 extension run uses:

    quant6    same uniform quantiser at 6 bits   (between quant8 and quant4)
    quant4    same uniform quantiser at 4 bits   (the aggressive corner)
    shdeg2    SH degree 2: only band 3 dropped at render time

Why this is safe for the paper's negative control: all quantisation goes through
the *one* function ``_quantize_splats(sp, torch, bits)``, so ``quant8`` keeps its
previous code path and its previous numbers bit for bit
(``tests/test_extend_eval.py`` pins the 8-bit output against a frozen
transcription of the pre-extension implementation).  The map is also idempotent on
every attribute except the quaternion -- there the post-quantisation
renormalisation means a second pass can move a quat by less than one 8-bit step,
which is the same in the published 8-bit run -- so re-quantising an 8-bit asset
does not walk away from it.  ``quant4``/``quant6`` therefore measure *dose* on the
same edit family instead of introducing a new mechanism.

Per scene the artifact holds

    gray_render (V,m,H,W) f16   channel-mean render, [0,1]-ish
    resid       (V,m,H,W) f16   channel-mean ABS residual |render-gt|  (paper residual)
    gray_gt     (m,H,W)   f16   channel-mean ground truth (shared by all variants)
    views       (m,)      i32   index of the camera in the archive's camera list
    c2w, K      (m,4,4),(m,3,3) cameras of those views (for world-space voxels)
    prim_means  (n,3) f32       decimated CLEAN primitive centres (voxel regions)
    prim_opacity(n,)  f32
    variant_names (V,)
    meta        json string: scene, factor, W/H, alpha, n_primitives, edit notes

``--dry-run`` runs the whole path on CPU with synthetic arrays (no torch import at
all) so the schema, file sizes and summary can be validated on the workstation.

Usage on the node
-----------------
    # the published 6-variant run (unchanged)
    python experiments/dump_artifacts.py --archive /workspace/data/out3dgs \
        --out /workspace/data/rev_dump --pup-dir /workspace/data/rev_dump/pup

    # the 2026-11 dose sweep: 7 variants, no PUP ply needed, no --profile
    python experiments/dump_artifacts.py --archive /workspace/data \
        --scenes flowers,bicycle,treehill,stump \
        --variants clean,prune50,prune30,shdeg1,quant8,quant4,quant6 \
        --out /workspace/res/dump --device cuda --budget-mb 45

See ``experiments/RUNBOOK_2026-11.md`` for the full node sequence, the size /
VRAM / transfer budget, and the three traps that cost the most time.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

VARIANTS = ["clean", "prune50", "prune30", "pup30", "shdeg1", "quant8"]

#: Opt-in dose-sweep variants.  Never enabled by ``VARIANTS``, ``--profile`` or the
#: defaults -- they must be named explicitly in ``--variants`` so that the archived
#: artifacts of the published run remain reproducible.
DOSE_VARIANTS = ["quant6", "quant4", "shdeg2"]

EDIT_NOTES = {
    "clean": "released checkpoint",
    "prune50": "opacity top-50%",
    "prune30": "opacity top-30%",
    "pup30": "PUP Fisher-diagonal top-30% (make_pup_variant.py)",
    "shdeg1": "SH degree 1: bands >=2 dropped at render time",
    "quant8": "all float attributes uniformly quantised to 8 bits",
    # dose sweep (opt-in, see DOSE_VARIANTS)
    "quant6": "all float attributes uniformly quantised to 6 bits",
    "quant4": "all float attributes uniformly quantised to 4 bits",
    "shdeg2": "SH degree 2: band 3 dropped at render time",
}

#: Alias: the task notes and ``RUNBOOK_2026-11.md`` call this table ``VARIANT_NOTES``.
VARIANT_NOTES = EDIT_NOTES


def variant_family(name: str) -> str:
    """Edit family of a variant name: ``clean``/``prune``/``pup``/``sh``/``quant``.

    Used by ``extend_eval.py`` to order the appendix tables by family and by the
    runbook to explain which variant is a *dose* of which edit.
    """
    for prefix, fam in (("prune", "prune"), ("pup", "pup"),
                        ("shdeg", "sh"), ("quant", "quant")):
        if name.startswith(prefix):
            return fam
    return "clean" if name == "clean" else "other"


def variant_dose(name: str) -> float:
    """Severity parameter inside a family (bits / SH degree / kept fraction).

    Only used for ordering and for the dose-response column of the extension
    tables; bigger is *more severe* for ``quant``/``shdeg`` (fewer bits, lower SH
    degree) and for ``prune``/``pup`` (smaller kept fraction).
    """
    fam = variant_family(name)
    if fam == "quant" or fam == "sh":
        return float(name[5:])
    if fam == "prune":
        return float(name[5:]) / 100.0
    if fam == "pup":
        return float(name[3:]) / 100.0
    return 1.0


_VARIANT_RE = re.compile(r"^(clean|pup30|prune\d{1,2}|shdeg\d|quant\d{1,2})$")


def _validate_variants(variants) -> None:
    """Fail fast, *before* the expensive PLY loads, on a mis-spelt ``--variants``."""
    bad = [v for v in variants if not _VARIANT_RE.match(v)]
    if bad:
        raise SystemExit(
            f"unknown variant(s) {bad}\n"
            f"  legal: clean, prune<1-99>, pup30, shdeg<0-9> (must be below the "
            f"asset's own SH degree), quant<2-24>\n"
            f"  default VARIANTS: {','.join(VARIANTS)}\n"
            f"  opt-in dose variants: {','.join(DOSE_VARIANTS)}")
    dup = sorted({v for v in variants if variants.count(v) > 1})
    if dup:
        raise SystemExit(f"duplicate variant(s) in --variants: {dup}")
    for v in variants:
        if v.startswith("quant") and not 2 <= int(v[5:]) <= 24:
            raise SystemExit(f"{v}: quantiser bits must be in 2..24")
    if not variants:
        raise SystemExit("--variants is empty")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Dump per-view grey renders/residuals per scene x variant (GPU).",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--archive", default="/workspace/data/out3dgs",
                    help="root of the released 3DGS output archive")
    ap.add_argument("--scenes", default="flowers,bicycle,treehill,stump")
    ap.add_argument("--out", default=C.default_out("dump"),
                    help="output dir for <scene>.npz + dump_summary.json")
    ap.add_argument("--variants", default=",".join(VARIANTS),
                    help="comma list; default is the frozen VARIANTS ("
                         + ",".join(VARIANTS) + "). Opt-in dose variants: "
                         + ",".join(DOSE_VARIANTS) + " (explicit only), plus any "
                         "prune<1-99>/shdeg<0-3>/quant<2-24>")
    ap.add_argument("--profile", default="full",
                    choices=["full", "core", "compact"],
                    help="convenience preset that overrides --variants/--downsample: "
                         "full = 6 variants at archive resolution (measured ~38MB/scene); "
                         "core = clean/prune50/prune30/pup30 (~26MB/scene); "
                         "compact = 6 variants with --downsample 2 (~10MB/scene)")
    ap.add_argument("--ply-pattern",
                    default="{archive}/output/{scene}/point_cloud/iteration_40000/point_cloud.ply")
    ap.add_argument("--pup-dir", default=None,
                    help="dir holding <scene>_pup30.ply from make_pup_variant.py"
                         " (default: <out>/pup)")
    ap.add_argument("--factor", type=int, default=4, help="image downscale of the archive")
    ap.add_argument("--alpha", type=float, default=C.ALPHA, help="conformal level (meta only)")
    ap.add_argument("--gt-convention", default="normalized", choices=["normalized", "archive"],
                    help="photometric convention for the ground truth: normalized = per-view "
                         "brightness equalisation (the v3 pass), archive = stored GT unchanged "
                         "(the v4 main tables, e.g. bicycle 22.2 dB)")
    ap.add_argument("--cal-frac", type=float, default=0.5,
                    help="cal/deployment fraction stored in meta (splits are redrawn on CPU)")
    ap.add_argument("--downsample", type=int, default=1,
                    help="extra box-downsample of the stored maps (1 = archive factor only)")
    ap.add_argument("--prim-sample", type=int, default=200_000,
                    help="how many clean primitive centres to ship for world-space voxels")
    ap.add_argument("--no-compress", action="store_true", help="np.savez instead of savez_compressed")
    ap.add_argument("--budget-mb", type=float, default=30.0, help="per-scene artifact budget")
    ap.add_argument("--max-views", type=int, default=0, help="cap held-out views (0 = all)")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--seed", type=int, default=C.RNG_SEED)
    ap.add_argument("--fidelity", action="store_true",
                    help="also compute SSIM and LPIPS per view (needs scikit-image and "
                         "the lpips package); off by default so the default artifact is "
                         "byte-identical to previous campaigns")
    ap.add_argument("--lpips-net", default="alex", choices=["alex", "vgg"],
                    help="backbone for LPIPS; the choice moves the score, so record it")
    # dry-run
    ap.add_argument("--dry-run", action="store_true",
                    help="CPU-only synthetic smoke test of the whole write path (no torch)")
    ap.add_argument("--dry-run-scenes", default="dryrun_alpha,dryrun_beta")
    ap.add_argument("--dry-run-hw", default="259,389",
                    help="H,W of the synthetic maps (default = factor-4 Mip-NeRF360 size)")
    ap.add_argument("--dry-run-views", type=int, default=18)
    ap.add_argument("--dry-run-ply-prims", type=int, default=20_000)
    ap.add_argument("--dry-run-out", default=None,
                    help="where dry-run artifacts go (default <out>/dryrun)")
    return ap


def _variants(args):
    return [v.strip() for v in args.variants.split(",") if v.strip()]


PROFILES = {
    # measured on the synthetic full-size dry run (259x389, 18 views)
    "full":    dict(variants=list(VARIANTS), downsample=1),                       # ~38 MB/scene
    "core":    dict(variants=["clean", "prune50", "prune30", "pup30"], downsample=1),  # ~26 MB/scene
    "compact": dict(variants=list(VARIANTS), downsample=2),                       # ~10 MB/scene
}
# NOTE: no profile ever enables DOSE_VARIANTS -- a dose run always passes --variants
# explicitly *and* leaves --profile at its default (anything but "full" overwrites
# --variants, see apply_profile).


def apply_profile(args):
    """``--profile`` only fills in what the user left at the default."""
    prof = PROFILES[args.profile]
    if args.profile != "full":
        args.variants = ",".join(prof["variants"])
        args.downsample = int(prof["downsample"])
    C.log(f"[{C.stamp()}] profile={args.profile} variants={args.variants} "
          f"downsample={args.downsample} (budget {args.budget_mb:.0f}MB/scene)")
    return args


def _scenes(args):
    return [s.strip() for s in args.scenes.split(",") if s.strip()]


# ---------------------------------------------------------------------------
# shared: pack + save
# ---------------------------------------------------------------------------


def pack_and_save(out_dir, scene, variants, grays, resids, gt_gray, views, c2w, K,
                  stats, meta, prim_means, prim_opac, args):
    """Downsample (optionally), write ``<scene>.npz`` and return the scene summary row."""
    f = int(args.downsample)
    h0, w0 = int(grays.shape[-2]), int(grays.shape[-1])
    if f > 1:
        grays = C.downsample_mean(grays, f)
        resids = C.downsample_mean(resids, f)
        gt_gray = C.downsample_mean(gt_gray, f)
        c2w_s, K_s = c2w, C.scale_K(K, f)
    else:
        c2w_s, K_s = c2w, np.asarray(K, np.float32)
    h, w = int(grays.shape[-2]), int(grays.shape[-1])

    meta = dict(meta)
    meta.update(scene=scene, variants=list(variants), factor=int(args.factor),
                downsample=f, height=h, width=w, height_raw=h0, width_raw=w0,
                alpha=float(args.alpha), cal_frac=float(args.cal_frac),
                views=[int(v) for v in np.asarray(views).tolist()],
                n_views=int(len(views)), n_variants=int(len(variants)))

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{scene}.npz")
    payload = dict(
        gray_render=np.asarray(grays, np.float16),
        resid=np.asarray(resids, np.float16),
        gray_gt=np.asarray(gt_gray, np.float16),
        views=np.asarray(views, np.int32),
        c2w=np.asarray(c2w_s, np.float32),
        K=np.asarray(K_s, np.float32),
        prim_means=np.asarray(prim_means, np.float32),
        prim_opacity=np.asarray(prim_opac, np.float32),
        variant_names=np.asarray(variants),
        meta=json.dumps(meta),
    )
    t0 = time.time()
    if args.no_compress:
        np.savez(path, **payload)
    else:
        np.savez_compressed(path, **payload)
    nbytes = os.path.getsize(path)
    raw = sum(int(np.asarray(v).nbytes) for v in payload.values() if isinstance(v, np.ndarray))
    C.log(f"[{C.stamp()}] {scene}: wrote {path} "
          f"{C.sizeof_fmt(nbytes)} (raw {C.sizeof_fmt(raw)}, "
          f"{100.0 * nbytes / max(raw, 1):.0f}% of raw) in {time.time() - t0:.1f}s"
          f"  shapes m={len(views)} H={h} W={w} V={len(variants)}")
    if nbytes > args.budget_mb * 1e6:
        C.log(f"  [warn] {scene} is {C.sizeof_fmt(nbytes)} > budget "
              f"{args.budget_mb:.0f}MB -> rerun with --downsample 2 or fewer --variants")

    row = dict(scene=scene, npz=path, bytes=int(nbytes), raw_bytes=int(raw),
               within_budget=bool(nbytes <= args.budget_mb * 1e6),
               bytes_per_view=float(nbytes / max(1, len(views))),
               height=h, width=w, n_views=int(len(views)), variants={})
    for vi, v in enumerate(variants):
        st = stats[v]
        row["variants"][v] = dict(
            n_primitives=int(st["n_primitives"]),
            note=EDIT_NOTES.get(v, ""),
            psnr=st["psnr"],
            mean_alpha=st["mean_alpha"],
            resid_median=st["resid_median"],     # per-view median of the per-view median
            resid_mean=st["resid_mean"],
            per_view=[dict(view=int(views[i]), psnr=st["psnr_views"][i],
                           resid_mean=st["resid_mean_views"][i],
                           resid_median=st["resid_median_views"][i],
                           alpha=st["alpha_views"][i]) for i in range(len(views))],
        )
    return row, path


# ---------------------------------------------------------------------------
# real (GPU) path
# ---------------------------------------------------------------------------


def _quantize_splats(sp, torch, bits: int = 8):
    """Per-coefficient SH quantisation with a per-primitive, per-channel scale.

    This is the **published** edit, copied from ``certificate_audit.quantize_sh``
    (see ``tools/patch_quant.py``): only the spherical-harmonic coefficients are
    touched, and every primitive-channel triple carries its own scale
    ``max|coef| / qmax``.  The perturbation is therefore *relative* and, at 8 bits,
    about two orders of magnitude below the residual itself — which is why the
    8-bit row is an exact no-op in the paper and doubles as the estimator noise
    floor.  ``bits=6/4`` move along the same family (coarser grid, larger
    relative perturbation) and are the new dose points.

    Do **not** quantise means/scales/quats/opacities here: a global min-max grid on
    world-space means destroys the geometry (8-bit on means alone costs ~7 dB) and
    would silently replace the paper's storage edit with a different one.
    """
    qmax = 2 ** (bits - 1) - 1
    for name in ("sh0", "shN"):
        t = getattr(sp, name)
        if t is None or t.numel() == 0:
            continue
        scale = t.abs().amax(dim=(1, 2), keepdim=True).clamp_min(1e-8) / qmax
        setattr(sp, name, torch.round(t / scale).clamp(-qmax - 1, qmax) * scale)
    return sp


def backbone_candidates(fname: str) -> list:
    """Every place torchvision may have put a backbone checkpoint, most specific first.

    A missing weight file is the difference between a table with a LPIPS column and one with a column of
    Nones, and the search path is environment-dependent (TORCH_HOME, XDG_CACHE_HOME, the login home, and on
    container images a bare /root).  Returning the list lets the error message name all of them.
    """
    roots = []
    th = os.environ.get("TORCH_HOME")
    if th:
        roots.append(th)
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        roots.append(os.path.join(xdg, "torch"))
    roots.append(os.path.expanduser("~/.cache/torch"))
    roots.append("/root/.cache/torch")
    seen, out = set(), []
    for r in roots:
        p = os.path.join(r, "hub", "checkpoints", fname)
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _fidelity_stats(colors, gt_v, args):
    """SSIM and LPIPS for one variant, per view plus the mean.

    ``colors`` is (m, H, W, 3) in [0, 1] on the CPU, ``gt_v`` is (m, 3, H, W) on the
    device.  Both metrics are optional: a missing package degrades to ``None`` with a
    loud log line rather than to a silent zero, because a table cell full of zeros is
    worse than an empty one.
    """
    out = {}
    c = np.clip(colors.numpy().astype(np.float32), 0.0, 1.0)
    g = np.clip(gt_v.permute(0, 2, 3, 1).cpu().numpy().astype(np.float32), 0.0, 1.0)
    try:
        from skimage.metrics import structural_similarity as _ssim
        per = [float(_ssim(g[i], c[i], channel_axis=-1, data_range=1.0))
               for i in range(c.shape[0])]
        out.update(ssim=float(np.mean(per)), ssim_views=per)
    except Exception as exc:                                # pragma: no cover
        C.log(f"  [warn] SSIM unavailable ({exc.__class__.__name__}: {exc})")
        out.update(ssim=None, ssim_views=None)
    try:
        import torch
        import lpips
        cands = backbone_candidates(
            "alexnet-owt-7be5be79.pth" if getattr(args, "lpips_net", "alex") == "alex"
            else "vgg16-397923af.pth")
        if not any(os.path.exists(p) for p in cands):
            # Downloading the backbone is a hidden network dependency that can stall a
            # whole campaign on a throttled link; refuse instead of hanging.  Round 54:
            # the old check looked only under $TORCH_HOME (or ~/.cache/torch) and missed
            # the copy torchvision writes when TORCH_HOME points elsewhere, which cost a
            # whole node round of LPIPS=null columns.
            raise FileNotFoundError(
                "backbone weights missing; looked in " + ", ".join(cands)
                + "; pre-place the file or drop --fidelity")
        if getattr(_fidelity_stats, "_net", None) is None:
            net = lpips.LPIPS(net=getattr(args, "lpips_net", "alex"), verbose=False)
            net = net.to(gt_v.device).eval()
            _fidelity_stats._net = net
        net = _fidelity_stats._net
        a = torch.from_numpy(c).permute(0, 3, 1, 2) * 2 - 1
        b = torch.from_numpy(g).permute(0, 3, 1, 2) * 2 - 1
        try:
            with torch.no_grad():
                per = net(a.to(gt_v.device), b.to(gt_v.device)).reshape(-1).detach().cpu().numpy().tolist()
        except torch.cuda.OutOfMemoryError:
            # Round 54: a 6.1 M-primitive render already holds ~32 GB of a 40 GB card, so the VGG
            # backbone (6 GB) cannot join it.  LPIPS on 25 full-resolution views costs ~40 s on CPU,
            # which is far cheaper than the node round a null column costs.
            C.log("  [warn] LPIPS fell back to CPU after a CUDA OOM")
            torch.cuda.empty_cache()
            net = net.to("cpu")
            _fidelity_stats._net = net
            with torch.no_grad():
                per = net(a, b).reshape(-1).detach().cpu().numpy().tolist()
        out.update(lpips=float(np.mean(per)), lpips_views=[float(x) for x in per])
    except Exception as exc:                                # pragma: no cover
        C.log(f"  [warn] LPIPS unavailable ({exc.__class__.__name__}: {exc})")
        out.update(lpips=None, lpips_views=None)
    return out


def dump_real(args) -> dict:
    C.add_code_root()
    import torch
    from calib.archive_only import load_archive_only_scene
    from calib.gsrender import load_splats, render
    from calib.colmap_io import load_images, normalize_exposure

    torch.manual_seed(args.seed)
    variants = _variants(args)
    _validate_variants(variants)
    scenes = _scenes(args)
    out_dir = args.out
    pup_dir = args.pup_dir or os.path.join(out_dir, "pup")
    os.makedirs(out_dir, exist_ok=True)

    # fail loudly *before* the long run if a PUP ply is missing
    needed = {}
    for sc in scenes:
        path = os.path.join(pup_dir, f"{sc}_pup30.ply")
        if "pup30" in variants and not os.path.isfile(path):
            raise FileNotFoundError(
                f"missing {path}; run make_pup_variant.py first or pass --pup-dir")
        needed[sc] = path

    rows = []
    for scene in scenes:
        t_scene = time.time()
        sc = load_archive_only_scene(args.archive, scene, factor=args.factor,
                                     cal_frac=args.cal_frac)
        W, H = int(sc["width"]), int(sc["height"])
        _gt = load_images(sc["image_paths"], args.factor, (W, H))
        gt_np = normalize_exposure(_gt) if args.gt_convention == "normalized" \
            else (_gt.astype(np.float32) / 255.0)
        gt = torch.from_numpy(gt_np).float()
        c2w_all = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K_all = torch.from_numpy(sc["Ks"]).to(args.device)
        views = sorted(set(list(sc["cal_idx"]) + list(sc["dep_idx"])))
        if args.max_views and len(views) > args.max_views:
            views = views[: args.max_views]
        views_np = np.asarray(views, np.int32)
        vt = torch.as_tensor(views, device=args.device)
        c2w_v = c2w_all[vt]
        K_v = K_all[vt]
        gt_v = gt[torch.as_tensor(views)].permute(0, 3, 1, 2).contiguous()   # (m,3,H,W)
        gt_gray = gt_v.mean(1).numpy().astype(np.float32)

        ply = args.ply_pattern.format(archive=args.archive, scene=scene)
        base = load_splats(ply, device=args.device)
        C.log(f"[{C.stamp()}] === {scene}: {base.n} primitives, {len(views)} held-out "
              f"views, {W}x{H} (factor {args.factor})")

        grays, resids, stats = [], [], {}
        for name in variants:
            t0 = time.time()
            sh_degree = None
            if name == "clean":
                sp = base
            elif name.startswith("prune"):
                ratio = int(name[5:]) / 100.0
                k = max(1, int(round(ratio * base.n)))
                keep = torch.argsort(-base.opacities)[:k].sort().values
                sp = base.subset(keep)
            elif name == "pup30":
                sp = load_splats(needed[scene], device=args.device)
            elif name.startswith("shdeg"):
                sh_degree = int(name[5:])
                if sh_degree >= base.sh_degree:
                    raise SystemExit(
                        f"{scene}/{name}: the checkpoint already has SH degree "
                        f"{base.sh_degree}, so {name} would render identically to "
                        f"clean (gsplat caps sh_degree at the asset's own degree). "
                        f"Use shdeg<{base.sh_degree}> or smaller.")
                sp = base
            elif name.startswith("quant"):
                # _quantize_splats mutates its argument, so the asset must be
                # cloned: without this, quant8/quant6/quant4 are *iterated*
                # quantisations of one shared tensor and every later variant
                # (including clean, if it comes after) sees the edited asset.
                sp = _quantize_splats(base.clone(), torch, bits=int(name[5:]))
            else:
                raise ValueError(f"unknown variant {name!r}")

            cols, alps = [], []
            for s in range(0, len(views), C.RENDER_CHUNK):
                sl = slice(s, s + C.RENDER_CHUNK)
                out = render(sp, c2w_v[sl], K_v[sl], W, H, sh_degree=sh_degree)
                cols.append(out["colors"].float().cpu())
                alps.append(out["alphas"].float().cpu())
                del out
            colors = torch.cat(cols, 0)                    # (m,H,W,3) CPU
            alphas = torch.cat(alps, 0)[..., 0]            # (m,H,W)
            del cols, alps

            gray = colors.mean(-1).numpy()
            resid = (colors - gt_v.permute(0, 2, 3, 1).cpu()).abs().mean(-1).numpy()
            rv_mean = resid.reshape(len(views), -1).mean(1)
            rv_med = np.median(resid.reshape(len(views), -1), axis=1)
            av = alphas.numpy().reshape(len(views), -1).mean(1)
            grays.append(gray)
            resids.append(resid)
            stats[name] = dict(
                n_primitives=int(sp.n),
                psnr=C.psnr_np(colors.numpy(), gt_v.permute(0, 2, 3, 1).numpy()),
                mean_alpha=float(av.mean()),
                resid_median=float(np.median(rv_med)),
                resid_mean=float(rv_mean.mean()),
                psnr_views=[C.psnr_np(colors[i].numpy(), gt_v[i].permute(1, 2, 0).numpy())
                            for i in range(len(views))],
                resid_mean_views=[float(x) for x in rv_mean],
                resid_median_views=[float(x) for x in rv_med],
                alpha_views=[float(x) for x in av],
            )
            if getattr(args, "fidelity", False):
                stats[name].update(_fidelity_stats(colors, gt_v, args))
            C.log(f"  {scene:9s} {name:8s} n={sp.n:>9,d} PSNR={stats[name]['psnr']:6.2f} "
                  f"resid mean={stats[name]['resid_mean']:.4f} "
                  f"median={stats[name]['resid_median']:.4f} "
                  f"alpha={stats[name]['mean_alpha']:.3f} ({time.time() - t0:.1f}s)")
            del colors, alphas, gray, resid
            if name != "clean":
                del sp
            if str(args.device).startswith("cuda"):
                torch.cuda.empty_cache()

        # decimated clean primitive centres for the world-space voxel regions
        n_keep = min(int(args.prim_sample), base.n)
        stride = max(1, base.n // max(1, n_keep))
        pm = base.means.detach().cpu().numpy()[::stride]
        po = base.opacities.detach().cpu().numpy()[::stride]
        meta = dict(dry_run=False, gt_convention=args.gt_convention, prim_sample_stride=int(stride),
                    prim_sample_n=int(len(pm)), scene_ntotal_primitives=int(base.n))
        row, _ = pack_and_save(out_dir, scene, variants,
                               np.stack(grays, 0), np.stack(resids, 0), gt_gray,
                               views_np, c2w_v.detach().cpu().numpy(),
                               K_v.detach().cpu().numpy(), stats, meta, pm, po, args)
        row["seconds"] = round(time.time() - t_scene, 1)
        rows.append(row)

    summary = dict(dry_run=False, archive=args.archive, factor=args.factor,
                   variants=variants, downsample=int(args.downsample),
                   alpha=float(args.alpha), n_splits=C.N_SPLITS, seed=int(args.seed),
                   budget_mb=float(args.budget_mb),
                   total_bytes=int(sum(r["bytes"] for r in rows)),
                   scenes=rows)
    C.json_dump(os.path.join(out_dir, "dump_summary.json"), summary)
    C.log(f"[{C.stamp()}] WROTE {os.path.join(out_dir, 'dump_summary.json')} "
          f"({C.sizeof_fmt(summary['total_bytes'])} total)")
    return summary


# ---------------------------------------------------------------------------
# dry-run (CPU, synthetic)
# ---------------------------------------------------------------------------


def _blur(a, k=5):
    """Separable box blur via cumulative sums (numpy only)."""
    if k <= 1:
        return a
    pad = k // 2
    for axis in (-2, -1):
        a = np.moveaxis(a, axis, -1)
        ap = np.pad(a, [(0, 0)] * (a.ndim - 1) + [(pad, pad)], mode="reflect")
        cs = np.cumsum(ap, axis=-1, dtype=np.float64)
        cs = np.concatenate([np.zeros(cs.shape[:-1] + (1,)), cs], axis=-1)
        a = ((cs[..., k:] - cs[..., :-k]) / k).astype(np.float32)
        a = np.moveaxis(a, -1, axis)
    return a


def _warp(img, dy, dx):
    """Bilinear resample of a 2-D map with a per-pixel displacement field."""
    H, W = img.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    sy = np.clip(yy + dy, 0, H - 1)
    sx = np.clip(xx + dx, 0, W - 1)
    y0 = np.floor(sy).astype(np.int64)
    x0 = np.floor(sx).astype(np.int64)
    y1 = np.minimum(y0 + 1, H - 1)
    x1 = np.minimum(x0 + 1, W - 1)
    fy, fx = sy - y0, sx - x0
    return (img[y0, x0] * (1 - fy) * (1 - fx) + img[y1, x0] * fy * (1 - fx)
            + img[y0, x1] * (1 - fy) * fx + img[y1, x1] * fy * fx).astype(np.float32)


def _synth_scene(rng, H, W, m, variants):
    """Deterministic synthetic (gt, {variant: rgb}) triplets with a known ordering.

    The point of the dry run is the *encoding, the schema and that the downstream
    scripts see a non-trivial signal*, not the physics.  Each variant gets a
    smooth spatially-varying warp whose amplitude grows with the edit severity
    (clean 0.2 px < shdeg2 < shdeg1 < quant8 < quant6 < pup30 < quant4 < prune50 <
    prune30 2.2 px) plus noise, so the localisation task, the block-matching task
    and the coverage numbers all have something monotone to measure.  Everything
    written by ``--dry-run`` is flagged ``dry_run: true`` and must never be quoted
    as a result.

    The tables below only *add* entries for the opt-in dose variants; every
    pre-existing key keeps its value and the generator consumes the rng in the
    same order, so ``--dry-run`` with the default ``VARIANTS`` stays byte-identical
    to the published fixture (checked in ``tests/test_extend_eval.py``).
    """
    base = np.zeros((H, W), np.float32)
    for k, amp in ((31, 0.55), (13, 0.28), (5, 0.12)):
        fl = _blur(rng.normal(size=(k, k)).astype(np.float32), 1)
        up = np.kron(fl, np.ones((H // k + 1, W // k + 1), np.float32))[:H, :W]
        base += amp * _blur(up, 3)
    fine = rng.normal(size=(H, W)).astype(np.float32)
    gt = np.clip(0.45 + 0.55 * base + 0.10 * _blur(fine, 1), 0.0, 1.0)
    gt = np.clip(0.5 + 1.6 * (gt - gt.mean()), 0.0, 1.0)          # add texture contrast

    noise = {"clean": 0.004, "pup30": 0.014, "prune50": 0.020,
             "prune30": 0.030, "shdeg1": 0.012, "quant8": 0.010,
             "shdeg2": 0.008, "quant6": 0.013, "quant4": 0.018}
    shift_px = {"clean": 0.2, "shdeg2": 0.3, "shdeg1": 0.4, "quant8": 0.5,
                "quant6": 0.7, "pup30": 0.9, "quant4": 1.0,
                "prune50": 1.4, "prune30": 2.2}
    # a stand-in for banding: 5-bit levels for quant8 (kept exactly as published so
    # the fixture stays byte-identical), coarser for quant4, finer for quant6
    band_levels = {"quant8": 31, "quant6": 63, "quant4": 15}
    gt3 = np.repeat(gt[None, ..., None], 3, axis=-1)               # (1,H,W,3)
    gt_all = np.repeat(gt3, m, axis=0)
    out = {}
    for name in variants:
        amp = float(shift_px.get(name, 1.0))
        dy = _blur(rng.normal(size=(m, H, W)).astype(np.float32), 9)
        dx = _blur(rng.normal(size=(m, H, W)).astype(np.float32), 9)
        dy = dy / max(float(np.std(dy)), 1e-6) * amp     # per-pixel displacement in px
        dx = dx / max(float(np.std(dx)), 1e-6) * amp
        warped = np.stack([np.stack([_warp(gt_all[i, ..., c], dy[i], dx[i])
                                     for c in range(3)], -1) for i in range(m)], 0)
        sig = noise.get(name, 0.01)
        n = rng.normal(scale=sig, size=(m, H, W, 3)).astype(np.float32)
        gain = 1.0 + rng.normal(scale=0.02, size=(m, 1, 1, 3)).astype(np.float32)
        r = warped * gain + n
        if name == "shdeg1":                      # view-dependent colour drift
            r = r * (1.0 + 0.05 * np.linspace(-1, 1, m)[:, None, None, None])
        if name.startswith("quant"):              # banding on top of the noise
            lv = band_levels.get(name, 2 ** int(name[5:]) - 1)
            r = np.round(np.clip(r, 0, 1) * lv) / float(lv)
        out[name] = np.clip(r, 0.0, 1.0).astype(np.float32)
    return gt_all.astype(np.float32), out


def dump_dry_run(args) -> dict:
    """Full write path on synthetic arrays; never imports torch."""
    rng = np.random.default_rng(args.seed)
    h, w = [int(x) for x in args.dry_run_hw.split(",")]
    m = int(args.dry_run_views)
    variants = _variants(args)
    _validate_variants(variants)
    out_dir = args.dry_run_out or os.path.join(args.out, "dryrun")
    os.makedirs(out_dir, exist_ok=True)
    # synthetic pinhole cameras on a circle, looking at the origin (camera +z forward)
    fx = fy = 0.8 * max(h, w)
    K = np.tile(np.array([[fx, 0, (w - 1) / 2.0], [0, fy, (h - 1) / 2.0], [0, 0, 1]],
                         np.float32), (m, 1, 1))
    c2w = np.tile(np.eye(4, dtype=np.float32), (m, 1, 1))
    for i in range(m):
        th = 2 * np.pi * i / max(1, m)
        pos = np.array([3.0 * np.sin(th), 0.2, 3.0 * np.cos(th)], np.float64)
        z_ax = -pos / np.linalg.norm(pos)                       # look at the origin
        up = np.array([0.0, 1.0, 0.0])
        x_ax = np.cross(up, z_ax)
        x_ax /= np.linalg.norm(x_ax)
        y_ax = np.cross(z_ax, x_ax)
        c2w[i, :3, :3] = np.stack([x_ax, y_ax, z_ax], axis=1).astype(np.float32)
        c2w[i, :3, 3] = pos.astype(np.float32)

    rows = []
    for scene in [s.strip() for s in args.dry_run_scenes.split(",") if s.strip()]:
        gt_all, renders = _synth_scene(rng, h, w, m, variants)
        gt_gray = gt_all.mean(-1)
        grays, resids, stats = [], [], {}
        for name in variants:
            rgb = renders[name]
            gray = rgb.mean(-1)
            resid = np.abs(rgb - gt_all).mean(-1)
            rv_mean = resid.reshape(m, -1).mean(1)
            rv_med = np.median(resid.reshape(m, -1), axis=1)
            grays.append(gray)
            resids.append(resid)
            stats[name] = dict(
                n_primitives=int(2_400_000 if name == "clean" else
                                 {"prune50": 1_200_000, "prune30": 720_000,
                                  "pup30": 720_000}.get(name, 2_400_000)),
                psnr=C.psnr_np(rgb, gt_all), mean_alpha=1.0,
                resid_median=float(np.median(rv_med)), resid_mean=float(rv_mean.mean()),
                psnr_views=[C.psnr_np(rgb[i], gt_all[i]) for i in range(m)],
                resid_mean_views=[float(x) for x in rv_mean],
                resid_median_views=[float(x) for x in rv_med],
                alpha_views=[1.0] * m)
            C.log(f"  dry {scene:12s} {name:8s} PSNR={stats[name]['psnr']:6.2f} "
                  f"resid mean={stats[name]['resid_mean']:.4f}")
        n_prims = int(args.dry_run_ply_prims)
        pm = rng.normal(scale=0.55, size=(n_prims, 3)).astype(np.float32)
        po = rng.uniform(0.05, 0.95, size=n_prims).astype(np.float32)
        meta = dict(dry_run=True, note="SYNTHETIC arrays - schema/size validation only",
                    prim_sample_stride=1, prim_sample_n=n_prims,
                    scene_ntotal_primitives=int(stats["clean"]["n_primitives"]))
        row, _ = pack_and_save(out_dir, scene, variants, np.stack(grays, 0),
                               np.stack(resids, 0), gt_gray,
                               np.arange(m, dtype=np.int32), c2w, K,
                               stats, meta, pm, po, args)
        rows.append(row)

    summary = dict(dry_run=True, note="SYNTHETIC arrays written by --dry-run; "
                                      "shapes/schema/sizes are real, pixel values are not",
                   variants=variants, downsample=int(args.downsample),
                   alpha=float(args.alpha), n_splits=C.N_SPLITS, seed=int(args.seed),
                   budget_mb=float(args.budget_mb),
                   total_bytes=int(sum(r["bytes"] for r in rows)), scenes=rows)
    path = os.path.join(out_dir, "dump_summary.json")
    C.json_dump(path, summary)
    C.log(f"[{C.stamp()}] DRY-RUN WROTE {path} "
          f"({C.sizeof_fmt(summary['total_bytes'])} total, "
          f"{len(rows)} synthetic scenes)")
    return summary


def main(argv=None):
    args = apply_profile(build_parser().parse_args(argv))
    if args.dry_run:
        dump_dry_run(args)
    else:
        dump_real(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
