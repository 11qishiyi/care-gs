"""Coverage at three region granularities from the same npz artifacts (pure CPU).

The paper's main table reports *pixel* coverage.  A reviewer will ask whether the
effect is an artefact of the pixel granularity, so this script recomputes the
same 400-split protocol at three grains, for every scene x variant:

    pixel   the paper's number: every pixel of a deployment view is a unit
    block   B x B image blocks: a block's score is the MAX residual anywhere in it
            (so a single bad pixel inside a block invalidates the block)
    voxel   world-space voxels: a voxel's score is the max residual over the
            world points that fall into it

For blocks and voxels the calibration score of a region is the max over the
calibration views in which it is observed, the threshold is the same
split-conformal quantile, and deployment coverage is the fraction of deployment
regions under it -- exactly ``research/code/calib/voxel_cert.py``'s definition,
so the numbers are directly comparable with the paper's existing voxel results.

Voxel mode here is ``--mode approx`` and that is a documented approximation:

* the released PLY is not shipped back from the GPU node (GBs), so the dump
  carries a **decimated sample of the clean primitive centres** and the voxels
  are built from those points;
* the exact path in ``voxel_cert.py`` back-projects every *rendered pixel* using
  the expected-depth buffer, which needs the GPU render; here we project the
  primitive centres instead (no depth buffer on the CPU side).

Both use the identical world-space voxel hash (``voxel_cert.voxel_ids``), the
identical quantile rule and the identical max-pooling, so the *granularity
effect* is measured cleanly.  ``ambient`` numbers (regions never seen in
calibration) are reported both ways: counted as uncovered and excluded.

Usage
-----
    python experiments/region_coverage.py --npz experiments/artifacts/dump \
        --out experiments/artifacts/region_coverage.json
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pixel / block / voxel coverage under the 400-split protocol.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--npz", default=C.default_out("dump"))
    ap.add_argument("--out", default=C.default_out("region_coverage.json"))
    ap.add_argument("--variants", default="", help="default: all non-clean variants")
    ap.add_argument("--blocks", default="64",
                    help="comma list of block sizes in STORED pixels; 64 is the size the"
                         " paper's block results use on factor-4 maps"
                         " (64 stored px = 256 capture px)")
    ap.add_argument("--block-mode", default="floor", choices=["floor", "pad"],
                    help="floor = H//b blocks (certificate_audit.py convention); "
                         "pad = keep the remainder")
    ap.add_argument("--voxel", type=float, default=0.25,
                    help="voxel edge in world units (0 -> derive from the primitive extent)")
    ap.add_argument("--voxels-per-axis", type=int, default=32,
                    help="used only when --voxel 0")
    ap.add_argument("--granularities", default="pixel,block,voxel")
    ap.add_argument("--mode", default="approx", choices=["approx", "none"],
                    help="voxel mode: approx (decimated primitive centres, no depth) "
                         "or none (skip voxels)")
    ap.add_argument("--alpha", type=float, default=C.ALPHA)
    ap.add_argument("--n-splits", type=int, default=C.N_SPLITS)
    ap.add_argument("--seed", type=int, default=C.RNG_SEED)
    ap.add_argument("--max-scenes", type=int, default=0)
    ap.add_argument("--max-views", type=int, default=0)
    return ap


# ---------------------------------------------------------------------------
# region matrices
# ---------------------------------------------------------------------------


def block_reduce_max(img: np.ndarray, b: int, mode: str = "floor") -> np.ndarray:
    """Max-pool a 2-D map into ``b x b`` blocks.

    ``mode="floor"`` drops the right/bottom remainder and is the convention used by
    ``research/code/scripts/certificate_audit.py`` (``H//b`` blocks), so these
    numbers are comparable with the paper's existing block results.
    ``mode="pad"`` keeps the remainder by zero-padding (residuals are >= 0, so the
    padding cannot raise a block maximum).
    """
    h, w = img.shape
    if mode == "pad":
        hp = int(np.ceil(h / b)) * b
        wp = int(np.ceil(w / b)) * b
        if hp != h or wp != w:
            img = np.pad(img, ((0, hp - h), (0, wp - w)), mode="constant")
        h, w = img.shape
    hb, wb = h // b, w // b
    if hb == 0 or wb == 0:
        return np.asarray([[float(img.max())]], np.float32)
    return img[:hb * b, :wb * b].reshape(hb, b, wb, b).max(axis=(1, 3))


def block_matrix(resid: np.ndarray, b: int, mode: str = "floor") -> np.ndarray:
    """(m, n_blocks) per-view block-max scores."""
    m = resid.shape[0]
    return np.stack([block_reduce_max(resid[i], b, mode).reshape(-1) for i in range(m)], 0)


def project_primitives(prim_means: np.ndarray, c2w: np.ndarray, K: np.ndarray,
                       H: int, W: int, max_prim: int = 0):
    """Project primitive centres into one view -> (pixel_y, pixel_x, keep mask)."""
    R = c2w[:3, :3]
    t = c2w[:3, 3]
    pc = (prim_means - t) @ R                     # world -> camera  (R^T (x - t))
    z = pc[:, 2]
    keep = z > 1e-6
    uvw = pc @ K.T
    with np.errstate(divide="ignore", invalid="ignore"):
        u = uvw[:, 0] / uvw[:, 2]
        v = uvw[:, 1] / uvw[:, 2]
    keep &= np.isfinite(u) & np.isfinite(v)
    keep &= (u >= 0) & (u <= W - 1) & (v >= 0) & (v <= H - 1)
    return v, u, keep


def voxel_matrix(resid: np.ndarray, prim_means: np.ndarray, c2w: np.ndarray, K: np.ndarray,
                 voxel: float):
    """(m, n_voxels) per-view voxel scores from primitive centres (``--mode approx``).

    A voxel's score in a view = max residual over the stored pixels its sampled
    primitives project onto (voxel_cert's max-pooling, without the depth buffer).
    """
    m, H, W = resid.shape
    ids = C.voxel_ids(prim_means, voxel)
    uniq, inv = np.unique(ids, return_inverse=True)
    E = np.full((m, uniq.size), np.nan, np.float32)
    for i in range(m):
        v, u, keep = project_primitives(prim_means, c2w[i], K[i], H, W)
        if not keep.any():
            continue
        yy = np.rint(v[keep]).astype(np.int64).clip(0, H - 1)
        xx = np.rint(u[keep]).astype(np.int64).clip(0, W - 1)
        vals = resid[i][yy, xx]
        cols = inv[keep]
        # per-voxel max = np.maximum.at scatter
        cur = np.full(uniq.size, -np.inf, np.float32)
        np.maximum.at(cur, cols, vals.astype(np.float32))
        cur[~np.isfinite(cur)] = np.nan
        E[i] = cur
    return E, uniq


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def _variants_of(sc, args):
    vnames = sc["variant_names"]
    if args.variants:
        want = [v.strip() for v in args.variants.split(",") if v.strip()]
        missing = [v for v in want if v not in vnames]
        if missing:
            raise SystemExit(f"{sc['meta']['scene']}: missing variants {missing}")
        return want
    return [v for v in vnames if v != "clean"]


def run_scene(path, args):
    sc = C.load_npz_scene(path)
    meta = sc["meta"]
    name = meta["scene"]
    vnames = sc["variant_names"]
    edited = _variants_of(sc, args)
    resid = sc["resid"].astype(np.float32)                  # (V,m,H,W)
    m = resid.shape[1]
    if args.max_views:
        m = min(m, args.max_views)
    resid = resid[:, :m]
    mi = vnames.index("clean")
    clean_resid = resid[mi]
    splits = C.split_perms(m, args.n_splits, args.seed)
    gran = [g.strip() for g in args.granularities.split(",") if g.strip()]

    degr = float(meta.get("downsample", 1))
    factor = float(meta.get("factor", 4))
    blocks = [int(b) for b in str(args.blocks).split(",") if str(b).strip()]
    H, W = clean_resid.shape[-2:]

    rows = []

    def add(variant, granularity, summ, n_regions, extra=None):
        row = dict(scene=name, variant=variant, granularity=granularity,
                   n_regions=int(n_regions), n_views=int(m))
        for k, v in summ.items():
            if isinstance(v, dict):
                continue
            row[k] = C.as_float(v) if isinstance(
                v, (int, float, np.integer, np.floating)) else v
        if extra:
            row.update(extra)
        rows.append(row)

    # ---- pixel -----------------------------------------------------------
    if "pixel" in gran:
        clean_flat = clean_resid.reshape(m, -1)
        qs = [C.cq(clean_flat[cal].reshape(-1), args.alpha) for cal, _ in splits]
        cc, _, dd, qarr = C.pixel_split_coverage(clean_flat, clean_flat, splits,
                                                 args.alpha, qs=qs)
        add("clean", "pixel", C.summarise_drops(dd, cc, cc), clean_flat.shape[1],
            dict(q_mean=C.as_float(np.mean(qarr))))
        for v in edited:
            vi = vnames.index(v)
            flat = resid[vi].reshape(m, -1)
            cc, ss, dd, _ = C.pixel_split_coverage(clean_flat, flat, splits,
                                                   args.alpha, qs=qs)
            add(v, "pixel", C.summarise_drops(dd, cc, ss), clean_flat.shape[1])
        C.log(f"  {name}: pixel done ({clean_flat.shape[1]} units/view)")

    # ---- block -----------------------------------------------------------
    for b in blocks:
        if "block" not in gran:
            continue
        Emats = {}
        for v in ["clean"] + edited:
            vi = vnames.index(v)
            Emats[v] = block_matrix(resid[vi], b, args.block_mode)
        cc, _, dd = C.pooled_coverage_splits(Emats["clean"], Emats["clean"], splits,
                                             args.alpha, pool="max")
        add("clean", f"block{b}", C.summarise_drops(dd, cc, cc), Emats["clean"].shape[1],
            dict(block_stored_px=int(b), block_capture_px=int(b * factor * degr),
                 block_mode=args.block_mode))
        for v in edited:
            cc, ss, dd = C.pooled_coverage_splits(Emats["clean"], Emats[v], splits,
                                                  args.alpha, pool="max")
            add(v, f"block{b}", C.summarise_drops(dd, cc, ss), Emats["clean"].shape[1],
                dict(block_stored_px=int(b), block_capture_px=int(b * factor * degr),
                     block_mode=args.block_mode))
        C.log(f"  {name}: block{b} done ({Emats['clean'].shape[1]} regions)")

    # ---- voxel -----------------------------------------------------------
    if "voxel" in gran and args.mode != "none":
        pm = sc["prim_means"].astype(np.float64)
        voxel = float(args.voxel)
        if voxel <= 0:
            voxel = C.voxel_size_from_extent(pm, args.voxels_per_axis)
        Emats = {}
        for v in ["clean"] + edited:
            vi = vnames.index(v)
            E, uniq = voxel_matrix(resid[vi], pm, sc["c2w"][:m], sc["K"][:m], voxel)
            Emats[v] = E
        cov_info = dict(voxel_size=float(voxel), n_voxels=int(uniq.size),
                        prim_sample=int(pm.shape[0]),
                        prim_stride=int(meta.get("prim_sample_stride", 1)),
                        observed_frac=C.as_float(np.mean(np.isfinite(Emats["clean"]))))
        for unseen_uncovered in (True, False):
            tag = "counted_uncovered" if unseen_uncovered else "excluded"
            cc, ss, dd, info = C.pooled_coverage_splits(
                Emats["clean"], Emats["clean"], splits, args.alpha, pool="max",
                unseen_uncovered=unseen_uncovered, return_info=True)
            add("clean", f"voxel[{tag}]", C.summarise_drops(dd, cc, cc), uniq.size,
                dict(cov_info, **info))
            for v in edited:
                cc, ss, dd = C.pooled_coverage_splits(
                    Emats["clean"], Emats[v], splits, args.alpha, pool="max",
                    unseen_uncovered=unseen_uncovered)
                add(v, f"voxel[{tag}]", C.summarise_drops(dd, cc, ss), uniq.size, cov_info)
        C.log(f"  {name}: voxel done (voxel={voxel:.3f}, {uniq.size} voxels, "
              f"{100 * cov_info['observed_frac']:.0f}% observed)")
    return rows


def main(argv=None):
    args = build_parser().parse_args(argv)
    t0 = time.time()
    files = C.discover_npz(args.npz)
    if not files:
        raise SystemExit(f"no npz artifacts under {args.npz}")
    if args.max_scenes:
        files = files[: args.max_scenes]
    C.log(f"[{C.stamp()}] region_coverage: {len(files)} npz, "
          f"granularities={args.granularities} blocks={args.blocks} "
          f"voxel={args.voxel} mode={args.mode} splits={args.n_splits}")

    rows = []
    for path in files:
        C.log(f"  --- {os.path.basename(path)}")
        rows += run_scene(path, args)

    # ---- summarise per variant x granularity -----------------------------
    variants = sorted({r["variant"] for r in rows}, key=lambda v: (v != "clean", v))
    grans = []
    for r in rows:
        if r["granularity"] not in grans:
            grans.append(r["granularity"])
    summary = {}
    for v in variants:
        summary[v] = {}
        for g in grans:
            sel = [r for r in rows if r["variant"] == v and r["granularity"] == g]
            if not sel:
                continue
            degr = [r["degradation_pp"] for r in sel if r.get("degradation_pp") is not None]
            cl = [r["clean_mean"] for r in sel if r.get("clean_mean") is not None]
            summary[v][g] = dict(
                n_scenes=len(sel),
                clean_mean=float(np.mean(cl)) if cl else None,
                degradation_pp_mean=float(np.mean(degr)) if degr else None,
                degradation_pp_by_scene={r["scene"]: r.get("degradation_pp") for r in sel},
                drop_mean_by_scene={r["scene"]: r.get("drop_mean") for r in sel},
            )

    # pixel vs region comparison, per variant
    cmp = {}
    for v in variants:
        if v == "clean" or "pixel" not in summary[v]:
            continue
        pix = summary[v]["pixel"]
        cmp[v] = {}
        for g in grans:
            if g == "pixel" or g not in summary[v]:
                continue
            a, b = [], []
            for s in pix["degradation_pp_by_scene"]:
                pa = pix["degradation_pp_by_scene"].get(s)
                pb = summary[v][g]["degradation_pp_by_scene"].get(s)
                if pa is None or pb is None:
                    continue
                a.append(pa)
                b.append(pb)
            a, b = np.asarray(a, float), np.asarray(b, float)
            cmp[v][g] = dict(
                pixel_degradation_pp_mean=float(a.mean()) if a.size else None,
                region_degradation_pp_mean=float(b.mean()) if b.size else None,
                ratio=float(b.mean() / a.mean()) if a.size and abs(a.mean()) > 1e-9 else None,
                frac_scenes_region_worse=float(np.mean(b > a)) if a.size else None,
                n_scenes=int(a.size))

    meta = dict(npz=[os.path.basename(f) for f in files],
                alpha=float(args.alpha), n_splits=int(args.n_splits),
                seed=int(args.seed), blocks=args.blocks, voxel=args.voxel,
                block_mode=args.block_mode, granularities=grans, mode=args.mode,
                protocol="400 random cal/deployment view splits (np.random.default_rng(0), "
                         "n_C=max(2,m//2)); q = split-conformal quantile of the CLEAN "
                         "calibration scores; coverage on deployment units; "
                         "drop = coverage(edited) - coverage(clean) paired by split; "
                         "degradation_pp = -100*drop",
                region_pooling="max over the pixels/points inside a region, then max over "
                               "the calibration (deployment) views of a split -- "
                               "calib/voxel_cert.py's definition",
                voxel_approx="voxels built from a decimated sample of clean primitive "
                             "centres projected with the stored c2w/K; the exact "
                             "voxel_cert.py path back-projects the depth buffer on the GPU",
                generated=C.stamp())
    res = dict(meta=meta, rows=rows, summary_by_variant=summary,
               region_vs_pixel=cmp, seconds=round(time.time() - t0, 1))
    C.json_dump(args.out, res)
    C.log(f"[{C.stamp()}] WROTE {args.out} in {res['seconds']}s")
    for v, d in summary.items():
        if v == "clean":
            continue
        parts = [f"{g}={d[g]['degradation_pp_mean']:+.1f}pp" if d[g]["degradation_pp_mean"]
                 is not None else f"{g}=n/a" for g in d]
        C.log(f"  {v:8s} degradation: " + "  ".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
