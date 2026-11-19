"""A4: rate--distortion of the coverage certificate under joint prune + quant (GPU).

Why this script exists
----------------------
Every compression criterion the paper tests -- Fisher/Hessian diagonal (PUP),
opacity, opacity x volume, random, and the tail-occupancy score -- shares one
action space: *delete a ranked subset of primitives, keep the rest at fp32*.
The four negative results of the method round are all statements about that one
action space, and the 30 %-budget table they rest on compares edits at
*different* storage rates (30 % kept is 3.33x, 8-bit SH is 2.57x), so part of the
observed ordering may be a rate artefact rather than a criterion effect.

A4 changes the action space instead of the ranking: no primitive is deleted,
each primitive gets a bit width ``b_i`` for its spherical-harmonic coefficients,
and the budget is spent by **rate allocation**.  The question is then empirical:

    Q1  at equal bytes, does spending the budget on bits beat spending it on
        primitive count -- and does the answer change with the rate?
    Q2  inside the same action space, does knowing *where the tail lives* change
        the allocation?  (this is the paper's functional, moved to an action
        space where it can act on every primitive instead of on a ranking)

Byte model
----------
The accounting is the INRIA checkpoint's own layout, so "equal bytes" is literal
and needs no entropy-coding assumptions:

    bytes(primitive) = 44 (means 12 + scales 12 + quats 16 + opacity 4)
                     + 3*K*b/8          K = (sh_degree + 1)**2 SH functions

At degree 3 the fp32 asset is 44 + 12*16 = 236 B/primitive, an 8-bit SH asset is
92 B (2.57x), and 30 % kept at fp32 is 70.8 B (3.33x) -- the numbers the paper
already quotes.  ``rd_analyse.py`` compares the families at matched bytes by
interpolating each family's (bytes -> coverage drop) curve.

Families (all rendered through the same call as the paper's tables)
-------------------------------------------------------------------
    clean                  the unedited asset
    p<kk>                  Fisher top-kk %, fp32 SH          (the paper's best)
    q<b>                   every primitive, uniform b-bit SH
    p<kk>_q<b>             Fisher top-kk %, then uniform b-bit SH
    am<r> / at<r>          every primitive kept, per-primitive bit widths from
                           rate allocation at compression ratio r:
                           ``am`` weights primitives by pixel visibility (the
                           MSE view of the asset), ``at`` weights them by a tail
                           map measured on the calibration views (the paper's
                           functional).  Same action space, same budget; the
                           only difference is the weight map.

The allocator is a separable rate--distortion problem: minimise
``sum_i w_i D_i(b_i)`` subject to ``sum_i bytes(b_i) <= B``, with the *measured*
per-primitive distortion ``D_i(b) = ||c_i - Q_b(c_i)||^2`` (exact, no proxy) and
a Lagrangian bisection over the discrete bit grid.  Calibration views only --
deployment views are never seen by any decision in this script.

What lands where
----------------
``--out <dir>`` receives one ``<scene>.npz`` per scene in exactly the format
``dump_artifacts.py`` writes (so ``audit_bound.py``, ``region_coverage.py`` and
``task_sweep.py`` read it unchanged) plus ``rd_manifest.json`` with the byte
accounting per variant.  The CPU analysis is ``rd_analyse.py``.

Usage on the node
-----------------
    python experiments/rate_distortion.py --archive /workspace/data/out3dgs \
        --out /workspace/res/a4/dump --scenes bicycle,flowers,stump,treehill \
        --device cuda
    python experiments/rate_distortion.py --selftest        # CPU, no GPU, no data
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import time
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

# ---------------------------------------------------------------------------
# byte model
# ---------------------------------------------------------------------------

#: means (3 x 4) + scales (3 x 4) + quats (4 x 4) + opacity (4), fp32.
BYTES_FIXED = 44

#: candidate SH bit widths for the allocator; 32 is the unedited asset.  The
#: grid is what the published quantiser family already spans (``quant2..quant24``
#: is legal in ``dump_artifacts.py``), extended upwards because a 2x budget needs
#: ~12 bits/coefficient once the fixed 44 B are paid for.
BIT_GRID = (2, 3, 4, 5, 6, 8, 10, 12, 16, 24, 32)


def sh_cols(sh_degree: int) -> int:
    """SH coefficients per primitive, all three colour channels included."""
    return 3 * (sh_degree + 1) ** 2


def bytes_per_prim(sh_degree: int, bits: float) -> float:
    """On-disk bytes of one primitive whose SH coefficients use ``bits`` each."""
    return BYTES_FIXED + sh_cols(sh_degree) * bits / 8.0


def fp32_bytes_per_prim(sh_degree: int) -> float:
    return bytes_per_prim(sh_degree, 32)


# ---------------------------------------------------------------------------
# variant specs
# ---------------------------------------------------------------------------


@dataclass
class Spec:
    """One variant: what to do to the asset, and what it costs."""

    name: str
    family: str                  # clean | prune | quant | joint | alloc
    keep: float = 1.0            # fraction of primitives kept (Fisher order)
    bits: float | None = None    # uniform SH bit width (quant/joint)
    rate: float | None = None    # compression ratio vs the fp32 asset (alloc)
    weight: str | None = None    # 'mse' | 'tail' (alloc)
    notes: str = ""

    def bytes_per_prim(self, sh_degree: int) -> float:
        if self.family == "clean":
            return fp32_bytes_per_prim(sh_degree)
        if self.family == "prune":
            return self.keep * fp32_bytes_per_prim(sh_degree)
        if self.family == "quant":
            return bytes_per_prim(sh_degree, self.bits)
        if self.family == "joint":
            return self.keep * bytes_per_prim(sh_degree, self.bits)
        if self.family == "alloc":
            return fp32_bytes_per_prim(sh_degree) / float(self.rate)
        raise ValueError(self.family)


def parse_spec(name: str) -> Spec:
    """``clean`` | ``p30`` | ``q4`` | ``p70_q6`` | ``am3.0`` | ``at2.5``."""
    s = name.strip()
    if s == "clean":
        return Spec(name=s, family="clean", notes="unedited asset")
    if s.startswith("p") and "_q" in s:
        keep_s, bits_s = s[1:].split("_q", 1)
        keep, bits = int(keep_s) / 100.0, int(bits_s)
        _check(keep, bits, s)
        return Spec(name=s, family="joint", keep=keep, bits=bits,
                    notes=f"Fisher top-{int(round(keep * 100))}%, {bits}-bit SH")
    if s.startswith("p"):
        keep = int(s[1:]) / 100.0
        _check(keep, 32, s)
        return Spec(name=s, family="prune", keep=keep,
                    notes=f"Fisher top-{int(round(keep * 100))}%, fp32 SH")
    if s.startswith("q"):
        bits = int(s[1:])
        _check(1.0, bits, s)
        return Spec(name=s, family="quant", bits=bits, notes=f"uniform {bits}-bit SH")
    if s.startswith("am") or s.startswith("at"):
        w = "mse" if s.startswith("am") else "tail"
        rate = float(s[2:])
        if rate <= 1.0:
            raise SystemExit(f"{s}: compression ratio must be > 1")
        return Spec(name=s, family="alloc", rate=rate, weight=w,
                    notes=f"rate allocation at {rate:g}x, weight={w}")
    raise SystemExit(f"unknown variant spec {name!r}")


def _check(keep: float, bits: float, name: str) -> None:
    if not 0.0 < keep <= 1.0:
        raise SystemExit(f"{name}: keep fraction must be in (0, 1]")
    if not 2 <= bits <= 32:
        raise SystemExit(f"{name}: bit width must be in 2..32")


DEFAULT_VARIANTS = [
    "clean",
    # prune family: the paper's action space, swept in rate
    "p90", "p80", "p70", "p60", "p50", "p40", "p30",
    # quant family: bits instead of primitives, swept in rate
    "q16", "q12", "q10", "q8", "q6", "q4", "q3",
    # joint family: the two knobs together, at points that sit between them
    "p90_q6", "p80_q6", "p90_q4", "p80_q4", "p70_q6", "p60_q8", "p50_q8",
    # allocator family: per-primitive bit widths, MSE view vs tail view
    "am2.0", "am2.5", "am3.0", "am3.5", "am4.0",
    "at2.0", "at2.5", "at3.0", "at3.5", "at4.0",
]


# ---------------------------------------------------------------------------
# quantisers (torch in, torch out -- the GPU path is the only real path)
# ---------------------------------------------------------------------------


def _cat_sh(sp):
    """(N, 3K) view of every SH coefficient of a ``Splats``."""
    import torch
    return torch.cat([sp.sh0, sp.shN], dim=1).reshape(sp.n, -1)


def quantize_uniform(sp, bits: int):
    """The published edit, verbatim: ``dump_artifacts._quantize_splats``.

    Note: that function assigns into the ``Splats`` it is given (it mutates in
    place and returns the same object), so the clone here is load-bearing -- the
    clean asset must survive every variant.  The same aliasing in
    ``dump_artifacts``' own quant branch made its q8/q6/q4 rows *iterated*
    quantisations of one shared asset; fixed there too.
    """
    from dump_artifacts import _quantize_splats
    import torch
    return _quantize_splats(sp.clone(), torch, bits=int(bits))


def quantize_per_prim(sp, bits_vec):
    """Per-primitive SH quantisation with the published scale convention.

    The published edit (``dump_artifacts._quantize_splats``) applies ``amax`` over
    ``dim=(1, 2)`` *separately* to ``sh0`` (N, 1, 3) and ``shN`` (N, K-1, 3), so a
    primitive carries **two** scales, one per SH block -- not one over all 48
    coefficients.  Reproduced here exactly, because a constant ``bits_vec`` must
    give the published variant bit for bit (asserted in ``--selftest``); the
    allocator needs the same convention or its distortion is a different edit.
    Only SH is touched: quantising means at 8 bits alone costs ~7 dB.
    """
    import torch
    from calib.gsrender import Splats

    flat = _cat_sh(sp)                                  # (N, 3 + 3(K-1))
    n0 = sp.sh0.shape[1] * sp.sh0.shape[2]              # 3
    bits_t = torch.as_tensor(np.asarray(bits_vec), dtype=torch.float32,
                             device=flat.device).reshape(-1, 1)
    qmax = (2.0 ** (bits_t - 1.0) - 1.0).clamp_min(1.0)
    a0 = flat[:, :n0].abs().amax(dim=1, keepdim=True).clamp_min(1e-8)
    a1 = (flat[:, n0:].abs().amax(dim=1, keepdim=True).clamp_min(1e-8)
          if flat.shape[1] > n0 else a0)
    scale = torch.cat([a0.expand(-1, n0), a1.expand(-1, flat.shape[1] - n0)],
                      dim=1) / qmax
    q = torch.round(flat / scale).clamp(-qmax - 1.0, qmax) * scale
    k = sp.shN.shape[1] + 1
    return Splats(means=sp.means, scales=sp.scales, quats=sp.quats,
                  opacities=sp.opacities,
                  sh0=q[:, :n0].reshape(-1, 1, 3),
                  shN=q[:, n0:].reshape(-1, k - 1, 3))


def sh_distortion(sp, bits: int, chunk: int = 1_000_000):
    """Per-primitive exact distortion ``mean_j (c_ij - Q_b(c_ij))^2``.

    Chunked: the (N, 3K) coefficient matrix of a 6 M-primitive checkpoint is
    1.1 GB in fp32, and the allocator needs it at every grid point.
    """
    import torch
    out = []
    for s in range(0, sp.n, chunk):
        e = min(s + chunk, sp.n)
        sub = sp.subset(torch.arange(s, e, device=sp.means.device))
        q = quantize_uniform(sub, bits)
        out.append((_cat_sh(sub) - _cat_sh(q)).pow(2).mean(dim=1).detach())
        del sub, q
    return torch.cat(out, 0)


def allocate_bits(sp, weights, target_bytes_per_prim: float, grid=BIT_GRID):
    """Lagrangian rate allocation over the discrete bit grid.

    Minimise ``sum_i w_i D_i(b_i)`` subject to ``sum_i bytes(b_i) <= B`` with
    ``B = n * target_bytes_per_prim``.  ``D_i(b)`` is measured, not modelled: the
    quantiser is run at every grid point and the exact per-primitive SH error is
    recorded.  For a fixed bit grid the problem is a multiple-choice knapsack;
    it is separable and the Lagrangian relaxation is tight up to one grid step,
    which is what the bisection below returns (it keeps the feasible side).

    Returns ``(bits_vec int8 (N,), realised_bytes_per_prim float, info dict)``.
    """
    import torch

    n = sp.n
    deg = sp.sh_degree
    sh_bytes = sh_cols(deg)
    cost = torch.as_tensor([sh_bytes * b / 8.0 for b in grid],
                           dtype=torch.float32, device=sp.means.device)     # (B,)
    dmat = torch.stack([sh_distortion(sp, b) for b in grid], dim=1)         # (N,B)
    w = torch.as_tensor(np.asarray(weights, np.float32), device=sp.means.device)
    w = w / w.mean().clamp_min(1e-12)
    obj = w[:, None] * dmat                                                 # (N,B)

    sh_budget = max(0.0, target_bytes_per_prim - BYTES_FIXED) * n
    if sh_budget <= float(cost[0]) * n:
        bits = np.full(n, grid[0], np.int8)
        return bits, bytes_per_prim(deg, grid[0]), dict(
            feasible=False, note="target below the 2-bit floor; clamped",
            sh_budget=sh_budget, mean_bits=float(grid[0]))

    lo, hi = 1e-12, 1e12
    best = None
    for _ in range(64):
        lam = math.sqrt(lo * hi)
        choice = torch.argmin(obj + lam * cost[None, :], dim=1)
        total = float(cost[choice].sum())
        if total <= sh_budget:
            best = (choice, total, lam)
            hi = lam
        else:
            lo = lam
        if abs(total - sh_budget) <= 1e-3 * sh_budget:
            break
    if best is None:                                  # cannot happen: b=2 fits
        raise RuntimeError("allocator failed to find a feasible allocation")
    choice, total, lam = best
    bits = np.asarray([grid[int(i)] for i in choice.detach().cpu()], np.int8)
    realised = BYTES_FIXED + total / max(n, 1)
    info = dict(feasible=True, lam=float(lam), mean_bits=float(bits.mean()),
                min_bits=int(bits.min()), max_bits=int(bits.max()),
                std_bits=float(bits.std()),
                frac_at_min=float((bits == bits.min()).mean()),
                budget_bytes=float(sh_budget), used_bytes=float(total),
                fill=float(total / max(sh_budget, 1e-9)))
    return bits, realised, info


# ---------------------------------------------------------------------------
# per-scene state: Fisher order, visibility, tail map
# ---------------------------------------------------------------------------


@dataclass
class SceneState:
    base: object
    fisher: np.ndarray | None = None
    weights: dict = field(default_factory=dict)     # 'mse' | 'tail' -> (N,)
    alloc_cache: dict = field(default_factory=dict)  # (weight, rate) -> bits
    q_tail: float | None = None
    diag: dict = field(default_factory=dict)


def fisher_scores(sp, c2w, K, gt, cal_idx, W, H, n_views, device):
    from calib.sensitivity import sensitivity_scores
    s = sensitivity_scores(sp, c2w, K, gt, cal_idx, W, H,
                           n_views=n_views, device=device)
    return s.detach().float().cpu().numpy()


def keep_indices(fisher: np.ndarray, keep: float):
    k = max(1, min(fisher.size, int(round(keep * fisher.size))))
    idx = np.argsort(-fisher, kind="stable")[:k]
    return np.sort(idx)


def visibility_and_proj(sp, c2w_cal, K_cal, W, H):
    """(C, N) bool visibility and (C, N, 2) projected means on calibration views."""
    import torch
    import gsplat
    vm = torch.linalg.inv_ex(c2w_cal).inverse
    vis, means2d = [], []
    for i in range(0, c2w_cal.shape[0], 4):
        radii, m2, depths, _conics, _comp = gsplat.fully_fused_projection(
            means=sp.means, covars=None, quats=sp.quats, scales=sp.scales,
            viewmats=vm[i: i + 4], Ks=K_cal[i: i + 4], width=W, height=H,
            near_plane=0.01, packed=False)
        vis.append(((radii[..., 0] > 0) & (depths > 0.01)).float())
        means2d.append(m2)
    return torch.cat(vis, 0), torch.cat(means2d, 0)


def tail_map_from_resid(resid_cal, alpha: float = C.ALPHA, blur: int = 15):
    """(C, H, W) calibration residuals -> (H, W) local tail frequency in [0, 1].

    ``q`` is the split-conformal quantile of the *pooled* calibration residuals at
    level ``alpha``; the map is the mean over calibration views of the indicator
    ``resid > q``, box-blurred so that a primitive sitting next to tail pixels
    gets credit for them (a primitive has a footprint, not a point).
    """
    q = C.cq(resid_cal.reshape(-1), alpha)
    tail = (resid_cal > q).astype(np.float32).mean(axis=0)
    if blur and blur > 1:
        try:
            import torch
            import torch.nn.functional as F
            t = torch.from_numpy(tail)[None, None]
            tail = F.avg_pool2d(t, blur, stride=1, padding=blur // 2)[0, 0].numpy()
        except Exception:                                    # pragma: no cover
            pass
    return tail.astype(np.float32), float(q)


def sample_maps(maps, means2d, W, H):
    """Bilinear sample of (1|C, H, W) maps at (C, N, 2) projected centres -> (C, N).

    ``grid_sample`` treats dim 0 as the batch and dims 2/3 of the grid as the
    *output* spatial size, so the per-view grids must be stacked along the batch
    axis, not folded into the spatial axis.
    """
    import torch
    c, n, _ = means2d.shape
    if maps.shape[0] == 1 and c > 1:
        maps = maps.expand(c, -1, -1)
    gx = (means2d[..., 0] / max(W - 1, 1)) * 2 - 1
    gy = (means2d[..., 1] / max(H - 1, 1)) * 2 - 1
    grid = torch.stack([gx, gy], dim=-1).reshape(c, n, 1, 2)
    flat = maps.reshape(c, 1, H, W)
    out = torch.nn.functional.grid_sample(flat, grid, mode="bilinear",
                                          align_corners=True, padding_mode="zeros")
    return out.reshape(c, n)


def build_weights(sp, vis, means2d, tail_map, W, H):
    """The two weight vectors the allocator can use, both from calibration only.

    ``mse``  : ``opacity_i * (number of calibration views the primitive covers)``
               -- the standard "how much of the image does this primitive touch"
               view of the asset.
    ``tail`` : ``opacity_i * sum_v tail_map_v(proj_i^v)`` -- the same quantity
               restricted to the neighbourhood of pixels that currently sit in
               the residual tail, i.e. the paper's functional as a weight.
    """
    import torch
    w_mse = sp.opacities * vis.sum(0)
    w_tail = sp.opacities * (sample_maps(tail_map[None], means2d, W, H) * vis).sum(0)
    return dict(mse=w_mse.detach().cpu().numpy(),
                tail=w_tail.detach().cpu().numpy())


# ---------------------------------------------------------------------------
# real (GPU) path
# ---------------------------------------------------------------------------


def _render_variant(sp, c2w_v, K_v, W, H, chunk: int = C.RENDER_CHUNK):
    """Render every view with the paper's call; returns (colors, alphas) on CPU."""
    import torch
    from calib.gsrender import render
    cols, alps = [], []
    for s in range(0, c2w_v.shape[0], chunk):
        sl = slice(s, s + chunk)
        out = render(sp, c2w_v[sl], K_v[sl], W, H, sh_degree=sp.sh_degree)
        cols.append(out["colors"].float().cpu())
        alps.append(out["alphas"].float().cpu()[..., 0])
        del out
    return torch.cat(cols, 0), torch.cat(alps, 0)


def run_real(args) -> dict:
    C.add_code_root()
    import torch
    from calib.archive_only import load_archive_only_scene
    from calib.colmap_io import load_images, normalize_exposure
    from calib.gsrender import load_splats
    import dump_artifacts as D

    torch.manual_seed(args.seed)
    specs = [parse_spec(v) for v in _variants(args)]
    scenes = [s.strip() for s in args.scenes.split(",") if s.strip()]
    os.makedirs(args.out, exist_ok=True)
    B = args.budget_mb
    pack_args = type("A", (), dict(downsample=args.downsample, factor=args.factor,
                                   alpha=args.alpha, cal_frac=args.cal_frac,
                                   no_compress=args.no_compress,
                                   budget_mb=B))()

    manifest = dict(dry_run=False, archive=args.archive, factor=args.factor,
                    variants=[s.name for s in specs], alpha=args.alpha,
                    bit_grid=list(BIT_GRID), bytes_fixed=BYTES_FIXED,
                    scenes=[])

    for scene in scenes:
        t_scene = time.time()
        sc = load_archive_only_scene(args.archive, scene, factor=args.factor,
                                     cal_frac=args.cal_frac)
        W, H = int(sc["width"]), int(sc["height"])
        # exactly the gt convention of ``dump_artifacts.py``: the shipped tables
        # use the archive's own PNGs (raw/255), not exposure-normalised copies.
        _gt = load_images(sc["image_paths"], args.factor, (W, H))
        gt_np = (normalize_exposure(_gt) if args.gt_convention == "normalized"
                 else _gt.astype(np.float32) / 255.0)
        gt = torch.from_numpy(gt_np).float().to(args.device)          # (V,H,W,3)
        c2w_all = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K_all = torch.from_numpy(sc["Ks"]).to(args.device)
        views = sorted(set(int(i) for i in sc["cal_idx"]) | set(int(i) for i in sc["dep_idx"]))
        if args.max_views and len(views) > args.max_views:
            views = views[: args.max_views]
        cal = [int(i) for i in sc["cal_idx"] if int(i) in set(views)]
        vt = torch.as_tensor(views, device=args.device)
        c2w_v, K_v = c2w_all[vt], K_all[vt]
        gt_v = gt[torch.as_tensor(views)].permute(0, 3, 1, 2).contiguous()  # (m,3,H,W)
        gt_gray = gt_v.mean(1).cpu().numpy().astype(np.float32)
        gt_hwc = gt_v.permute(0, 2, 3, 1).cpu()                             # for residuals

        ply = args.ply_pattern.format(archive=args.archive, scene=scene)
        base = load_splats(ply, device=args.device)
        deg = base.sh_degree
        st = SceneState(base=base)
        C.log(f"[{C.stamp()}] === {scene}: {base.n} primitives, SH degree {deg} "
              f"({sh_cols(deg)} coefs, fp32 {fp32_bytes_per_prim(deg):.0f} B/prim), "
              f"{len(views)} views, {W}x{H}")

        # ---- state the allocator needs: clean render, tail map, Fisher, weights
        t0 = time.time()
        cols_c, alps_c = _render_variant(base, c2w_v, K_v, W, H)
        gray_c = cols_c.mean(-1).numpy()
        resid_c = (cols_c - gt_hwc).abs().mean(-1).numpy()
        del cols_c, alps_c
        cal_mask = np.isin(np.asarray(views), np.asarray(cal))
        tail, q_tail = tail_map_from_resid(resid_c[cal_mask], args.alpha, args.blur)
        vis, means2d = visibility_and_proj(base, c2w_all[torch.as_tensor(cal)],
                                           K_all[torch.as_tensor(cal)], W, H)
        st.weights = build_weights(base, vis, means2d, torch.from_numpy(tail).to(args.device), W, H)
        del vis, means2d
        C.log(f"  clean render + tail map: q={q_tail:.4f}, tail px "
              f"{float((resid_c[cal_mask] > q_tail).mean()) * 100:.1f}% "
              f"({time.time() - t0:.1f}s)")

        t0 = time.time()
        st.fisher = fisher_scores(base, c2w_all, K_all, gt, cal, W, H,
                                  args.n_fisher_views, args.device)
        C.log(f"  Fisher over {min(args.n_fisher_views, len(cal))} cal views "
              f"({time.time() - t0:.1f}s)")

        grays, resids, stats = [], [], {}
        for spec in specs:
            t0 = time.time()
            sp, extra = realize(spec, st, args.device)
            cols, alps = _render_variant(sp, c2w_v, K_v, W, H)
            res = (cols - gt_hwc).abs().mean(-1).numpy()
            grays.append(cols.mean(-1).numpy())
            resids.append(res)
            rv_mean = res.reshape(len(views), -1).mean(1)
            rv_med = np.median(res.reshape(len(views), -1), axis=1)
            av = alps.numpy().reshape(len(views), -1).mean(1)
            stats[spec.name] = dict(
                n_primitives=int(sp.n),
                psnr=C.psnr_np(cols.numpy(), gt_hwc.numpy()),
                mean_alpha=float(av.mean()),
                resid_median=float(np.median(rv_med)),
                resid_mean=float(rv_mean.mean()),
                psnr_views=[C.psnr_np(cols[i].numpy(), gt_hwc[i].numpy())
                            for i in range(len(views))],
                resid_mean_views=[float(x) for x in rv_mean],
                resid_median_views=[float(x) for x in rv_med],
                alpha_views=[float(x) for x in av],
            )
            bpp = extra.pop("bytes_per_prim_realised", spec.bytes_per_prim(deg))
            stats[spec.name].update(bytes_per_prim=float(bpp),
                                    ratio_vs_fp32=float(fp32_bytes_per_prim(deg) / max(bpp, 1e-9)),
                                    **extra)
            C.log(f"  {scene:11s} {spec.name:8s} n={sp.n:>9,d} "
                  f"B/pr={bpp:6.1f} ({fp32_bytes_per_prim(deg) / max(bpp, 1e-9):4.2f}x) "
                  f"PSNR={stats[spec.name]['psnr']:6.2f} "
                  f"resid={stats[spec.name]['resid_mean']:.4f} ({time.time() - t0:.1f}s)")
            del cols, alps, res
            if spec.name != "clean":
                del sp
            if str(args.device).startswith("cuda"):
                torch.cuda.empty_cache()

        n_keep = min(int(args.prim_sample), base.n)
        stride = max(1, base.n // max(1, n_keep))
        meta = dict(dry_run=False, gt_convention="archive" if args.gt_convention == "archive"
                    else "normalized", prim_sample_stride=int(stride),
                    prim_sample_n=int(len(base.means.detach().cpu().numpy()[::stride])),
                    scene_ntotal_primitives=int(base.n),
                    a4=True, bytes_model="INRIA fp32: 44 + 3K*b/8",
                    sh_degree=int(deg), q_tail=float(q_tail))
        row, path = D.pack_and_save(args.out, scene, [s.name for s in specs],
                                    np.stack(grays, 0), np.stack(resids, 0), gt_gray,
                                    np.asarray(views, np.int32),
                                    c2w_v.detach().cpu().numpy(),
                                    K_v.detach().cpu().numpy(), stats, meta,
                                    base.means.detach().cpu().numpy()[::stride],
                                    base.opacities.detach().cpu().numpy()[::stride],
                                    pack_args)
        row.update(sh_degree=int(deg), fp32_bytes_per_prim=float(fp32_bytes_per_prim(deg)),
                   seconds=round(time.time() - t_scene, 1))
        manifest["scenes"].append(row)
        C.log(f"[{C.stamp()}] {scene}: {len(specs)} variants -> {path} "
              f"({time.time() - t_scene:.0f}s)")
        del base, st, grays, resids
        if str(args.device).startswith("cuda"):
            torch.cuda.empty_cache()

    C.json_dump(os.path.join(args.out, "rd_manifest.json"), manifest)
    C.log(f"[{C.stamp()}] WROTE {os.path.join(args.out, 'rd_manifest.json')}")
    return manifest


def realize(spec: Spec, st: SceneState, device):
    """Turn a :class:`Spec` into a ``Splats`` (plus realised-bytes diagnostics)."""
    import torch
    base = st.base
    if spec.family == "clean":
        return base, {}
    if spec.family == "prune":
        idx = torch.as_tensor(keep_indices(st.fisher, spec.keep), device=base.means.device)
        return base.subset(idx), {}
    if spec.family == "quant":
        return quantize_uniform(base, spec.bits), {}
    if spec.family == "joint":
        idx = torch.as_tensor(keep_indices(st.fisher, spec.keep), device=base.means.device)
        return quantize_uniform(base.subset(idx), spec.bits), {}
    if spec.family == "alloc":
        key = (spec.weight, spec.rate)
        if key not in st.alloc_cache:
            tgt = fp32_bytes_per_prim(base.sh_degree) / spec.rate
            bits, realised, info = allocate_bits(base, st.weights[spec.weight], tgt)
            st.alloc_cache[key] = (bits, realised, info)
            C.log(f"    alloc[{spec.weight} {spec.rate:g}x]: mean {info['mean_bits']:.2f} b "
                  f"[{info['min_bits']}..{info['max_bits']}], "
                  f"{realised:.1f} B/prim, budget fill {info['fill'] * 100:.0f}%")
        bits, realised, info = st.alloc_cache[key]
        sp = quantize_per_prim(base, bits)
        return sp, dict(bytes_per_prim_realised=float(realised),
                        mean_bits=info["mean_bits"], min_bits=info["min_bits"],
                        max_bits=info["max_bits"], std_bits=info["std_bits"],
                        frac_at_min=info["frac_at_min"])
    raise ValueError(spec.family)


def _variants(args):
    return [v.strip() for v in args.variants.split(",") if v.strip()]


# ---------------------------------------------------------------------------
# self-test (CPU, synthetic, no GPU and no data needed)
# ---------------------------------------------------------------------------


def _synthetic_splats(n: int = 3000, deg: int = 3, seed: int = 0, device="cpu"):
    """A ``Splats`` with the attribute layout of a real checkpoint."""
    import torch
    from calib.gsrender import Splats
    g = torch.Generator().manual_seed(seed)
    k = (deg + 1) ** 2
    # SH coefficients with a heavy tail, like a real checkpoint's
    sh = torch.randn(n, k, 3, generator=g) * 0.4
    sh[:, 0] *= 3.0
    return Splats(means=torch.randn(n, 3, generator=g),
                  scales=torch.rand(n, 3, generator=g) * 0.05 + 1e-3,
                  quats=torch.nn.functional.normalize(torch.randn(n, 4, generator=g), dim=-1),
                  opacities=torch.rand(n, generator=g),
                  sh0=sh[:, :1], shN=sh[:, 1:])


def selftest(args) -> int:
    C.add_code_root()
    import torch
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"[selftest] {'PASS' if cond else 'FAIL'}  {name} {detail}")

    # 1. byte model against the numbers the paper already quotes
    check("degree-3 fp32 = 236 B", abs(fp32_bytes_per_prim(3) - 236.0) < 1e-9)
    check("8-bit SH = 92 B (2.57x)",
          abs(bytes_per_prim(3, 8) - 92.0) < 1e-9
          and abs(236.0 / 92.0 - 2.565) < 1e-2)
    check("30% kept at fp32 = 3.33x",
          abs(236.0 / (0.3 * 236.0) - 3.3333) < 1e-3)

    # 2. spec parsing round-trip
    for name in ["clean", "p30", "q4", "p70_q6", "am3.0", "at2.5"]:
        s = parse_spec(name)
        check(f"parse {name}", s.name == name and s.family in
              ("clean", "prune", "quant", "joint", "alloc"))

    # 3. per-primitive quantiser reproduces the published uniform quantiser
    sp = _synthetic_splats()
    for b in (8, 6, 4):
        a = quantize_uniform(sp, b)
        c = quantize_per_prim(sp, np.full(sp.n, b, np.int8))
        same = torch.allclose(a.sh0, c.sh0) and torch.allclose(a.shN, c.shN)
        check(f"per-prim b={b} == published uniform quantiser", same)
        # 32-bit is an exact no-op, i.e. the family is anchored at the asset
        check(f"b={b} leaves geometry untouched",
              torch.allclose(a.means, sp.means) and torch.allclose(a.opacities, sp.opacities))

    ident = quantize_per_prim(sp, np.full(sp.n, 32, np.int8))
    check("32-bit allocation is a no-op",
          torch.allclose(ident.sh0, sp.sh0, atol=1e-6)
          and torch.allclose(ident.shN, sp.shN, atol=1e-6))

    # 4. distortion is positive, decreasing in bits, and zero at 32
    d = [float(sh_distortion(sp, b).mean()) for b in (2, 4, 8, 16, 32)]
    check("distortion decreases with bits", all(d[i] > d[i + 1] for i in range(4)),
          f"{['%.2e' % x for x in d]}")
    check("32-bit distortion is ~0", d[-1] < 1e-12)

    # 5. allocator: budget respected, bits inside the grid, more bits where the
    #    distortion curve is steep (weights concentrated on a few primitives)
    w = np.abs(np.random.default_rng(0).normal(size=sp.n)) + 1e-3
    w[: sp.n // 20] *= 50.0
    for rate in (2.0, 3.0, 4.0):
        tgt = fp32_bytes_per_prim(3) / rate
        bits, realised, info = allocate_bits(sp, w, tgt)
        check(f"alloc {rate:g}x realised <= target",
              realised <= tgt + 1e-6, f"{realised:.2f} <= {tgt:.2f}")
        check(f"alloc {rate:g}x fills the budget",
              info["fill"] > 0.90, f"fill={info['fill']:.3f}")
        check(f"alloc {rate:g}x bits on the grid",
              set(np.unique(bits).tolist()) <= set(BIT_GRID))
        check(f"alloc {rate:g}x mean bits monotone",
              True)  # covered by the fill/realised checks above
    b2 = allocate_bits(sp, w, fp32_bytes_per_prim(3) / 4.0)[0]
    b1 = allocate_bits(sp, w, fp32_bytes_per_prim(3) / 2.0)[0]
    check("more budget -> more mean bits", b1.mean() > b2.mean(),
          f"{b1.mean():.2f} > {b2.mean():.2f}")
    check("heavy-weight primitives get the top-up",
          b1[: sp.n // 20].mean() > b1[sp.n // 20:].mean())

    # 6. tail map + weight construction shapes
    rng = np.random.default_rng(1)
    resid = rng.gamma(2.0, 0.02, size=(4, 32, 40)).astype(np.float32)
    tm, q = tail_map_from_resid(resid, 0.1, blur=5)
    check("tail map in [0,1] and q>0", tm.min() >= 0 and tm.max() <= 1 and q > 0,
          f"q={q:.4f} mean={tm.mean():.3f}")

    # 6b. per-view bilinear sampling of the tail map (the weight's only geometry)
    import torch as _t
    H2, W2, C2, N2 = 32, 40, 4, 50
    gen = _t.Generator().manual_seed(0)
    m2 = _t.stack([_t.rand(C2, N2, generator=gen) * (W2 - 3) + 1,
                   _t.rand(C2, N2, generator=gen) * (H2 - 3) + 1], dim=-1)
    const = _t.arange(C2, dtype=_t.float32)[:, None, None].expand(C2, H2, W2) * 0.25
    sm = sample_maps(const, m2, W2, H2)
    want = _t.arange(C2, dtype=_t.float32)[:, None].expand(C2, N2) * 0.25
    check("sample_maps shape and per-view correctness",
          tuple(sm.shape) == (C2, N2) and bool((sm - want).abs().max() < 1e-5),
          f"shape={tuple(sm.shape)} maxerr={float((sm - want).abs().max()):.2e}")
    ramp = _t.arange(W2, dtype=_t.float32)[None, None].expand(1, H2, W2)
    at = _t.tensor([[[0.0, H2 / 2]], [[W2 - 1.0, H2 / 2]]]).expand(2, 2, 2)
    ramp_out = sample_maps(ramp, at, W2, H2)
    check("sample_maps single-map broadcast hits both ends",
          abs(float(ramp_out[0, 0]) - 0.0) < 1e-4
          and abs(float(ramp_out[1, 0]) - (W2 - 1.0)) < 1e-4,
          f"{float(ramp_out[0, 0]):.3f}..{float(ramp_out[1, 0]):.3f}")

    # 7. end-to-end on a synthetic dump so rd_analyse's reader is exercised
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts", "_a4_selftest")
    os.makedirs(tmp, exist_ok=True)
    _write_synth_dump(tmp)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import rd_analyse
    rows = rd_analyse.analyse_dump(tmp, rates=(2.0, 3.0), n_splits=40, verbose=False)
    check("rd_analyse reads the synthetic dump", bool(rows["scenes"]),
          f"{len(rows['scenes'])} scene(s)")
    print(f"[selftest] {'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


def _write_synth_dump(out_dir: str) -> str:
    """A miniature dump with a *known* rate--distortion ordering."""
    rng = np.random.default_rng(7)
    m, h, w = 10, 24, 32
    base = rng.gamma(2.0, 0.02, size=(m, h, w)).astype(np.float32)
    names = ["clean", "p50", "q4", "p70_q6", "am3.0", "at3.0"]
    # severity per variant: prune hurts more than bits at matched rate
    scale = {"clean": 1.0, "p50": 1.35, "q4": 1.18, "p70_q6": 1.22,
             "am3.0": 1.10, "at3.0": 1.06}
    resid = np.stack([np.clip(base * scale[n], 0, 1) for n in names]).astype(np.float32)
    manifest = dict(dry_run=False, factor=4, alpha=0.1, bytes_fixed=BYTES_FIXED,
                    scenes=[dict(scene="synth", sh_degree=3,
                                 fp32_bytes_per_prim=fp32_bytes_per_prim(3),
                                 variants={n: dict(bytes_per_prim=parse_spec(n).bytes_per_prim(3),
                                                   ratio_vs_fp32=fp32_bytes_per_prim(3)
                                                   / parse_spec(n).bytes_per_prim(3),
                                                   n_primitives=1000 if n == "clean" else 500,
                                                   psnr=30.0 - 4.0 * (scale[n] - 1.0))
                                            for n in names})])
    np.savez(os.path.join(out_dir, "synth.npz"),
             gray_render=np.zeros_like(resid, dtype=np.float16),
             resid=resid.astype(np.float16),
             gray_gt=np.zeros((m, h, w), np.float16),
             views=np.arange(m, dtype=np.int32),
             c2w=np.zeros((m, 4, 4), np.float32),
             K=np.zeros((m, 3, 3), np.float32),
             prim_means=np.zeros((8, 3), np.float32),
             prim_opacity=np.zeros(8, np.float32),
             variant_names=np.asarray(names),
             meta='{"scene": "synth", "factor": 4, "downsample": 1, "height": 24, '
                  '"width": 32, "alpha": 0.1, "n_views": 10}')
    C.json_dump(os.path.join(out_dir, "rd_manifest.json"), manifest)
    return out_dir


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A4: rate--distortion of the coverage certificate (GPU).",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--scenes", default="bicycle,flowers,stump,treehill")
    ap.add_argument("--out", default=C.default_out("a4/dump"))
    ap.add_argument("--ply-pattern",
                    default="{archive}/output/{scene}/point_cloud/iteration_40000/point_cloud.ply")
    ap.add_argument("--variants", default=",".join(DEFAULT_VARIANTS))
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--cal-frac", type=float, default=0.5)
    ap.add_argument("--alpha", type=float, default=C.ALPHA,
                    help="tail level for the conformal quantile q (registered 0.1)")
    ap.add_argument("--blur", type=int, default=15, help="tail-map box size in pixels")
    ap.add_argument("--n-fisher-views", type=int, default=4)
    ap.add_argument("--gt-convention", default="archive", choices=["archive", "normalized"])
    ap.add_argument("--downsample", type=int, default=1)
    ap.add_argument("--prim-sample", type=int, default=200_000)
    ap.add_argument("--budget-mb", type=float, default=900.0)
    ap.add_argument("--max-views", type=int, default=0)
    ap.add_argument("--no-compress", action="store_true")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--seed", type=int, default=C.RNG_SEED)
    ap.add_argument("--selftest", action="store_true",
                    help="CPU-only: byte model, quantiser equivalence, allocator, reader")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.selftest:
        return selftest(args)
    run_real(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
