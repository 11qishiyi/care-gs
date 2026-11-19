"""Photometric diagnostic: is the reported 16-20 dB a property of the asset or of the GT pipeline?

The paper's residuals are ``|render - gt|`` where ``gt`` went through
``normalize_exposure`` (per-image scaling of the *ground truth only*, so that its mean
intensity becomes 0.40).  Released checkpoints were trained on the raw images of the
capture, so normalising only the GT can turn a mild exposure difference into a large
residual, and every downstream statement (q, coverage, and how much an edit moves them)
inherits that scale.

This script renders the same views once and reports the residual scale and the
certificate behaviour under five GT conventions:

    raw        gt as shipped (0-1), render untouched                     (honest baseline)
    norm_gt    normalize_exposure(gt) only          <- what the paper does today
    norm_both  per-image mean matching applied to gt AND render
    gain       per-image scalar gain fitted on the render
    affine     per-image affine (a, b) fitted on the render

For each convention: PSNR, median residual, the conformal quantile q, fresh coverage,
and the coverage drop after a 30% opacity prune (the paper's headline effect).

    python experiments/node_diag.py --archive /workspace/data/official \
        --scenes flowers,bicycle,treehill,stump --out /workspace/res/diag.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "code"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calib.archive_only import load_archive_only_scene  # noqa: E402
from calib.colmap_io import load_images, normalize_exposure  # noqa: E402

ALPHA = 0.10


def cq(scores, alpha):
    n = scores.size
    k = min(max(int(np.ceil((n + 1) * (1 - alpha))), 1), n)
    return float(np.sort(scores)[k - 1])


def conformal_block(r_clean, r_pruned, n_splits=400, seed=0, alpha=ALPHA):
    """400 random cal/deploy splits, exactly as many_splits.py: coverage + paired drop."""
    rng = np.random.default_rng(seed)
    n = r_clean.shape[0]
    n_c = max(2, n // 2)
    clean_c, stale_c = [], []
    for _ in range(n_splits):
        perm = rng.permutation(n)
        ci, vi = perm[:n_c], perm[n_c:]
        q = cq(r_clean[ci].reshape(-1), alpha)
        clean_c.append(float((r_clean[vi].reshape(-1) <= q).mean()))
        stale_c.append(float((r_pruned[vi].reshape(-1) <= q).mean()))
    clean_c, stale_c = np.array(clean_c), np.array(stale_c)
    d = stale_c - clean_c
    return dict(clean_mean=float(clean_c.mean()), clean_lo=float(np.percentile(clean_c, 2.5)),
                clean_hi=float(np.percentile(clean_c, 97.5)), stale_mean=float(stale_c.mean()),
                drop_mean=float(d.mean()), drop_lo=float(np.percentile(d, 2.5)),
                drop_hi=float(np.percentile(d, 97.5)))


def psnr(a, b):
    mse = float(np.mean((a - b) ** 2))
    return float("inf") if mse <= 1e-12 else float(10.0 * np.log10(1.0 / mse))


def per_image_gain(render, gt):
    """Best scalar gain a for each image (no offset): a = <r,g>/<r,r>."""
    r = render.reshape(render.shape[0], -1)
    g = gt.reshape(gt.shape[0], -1)
    a = (r * g).sum(1) / np.clip((r * r).sum(1), 1e-8, None)
    return render * a[:, None, None]


def per_image_affine(render, gt):
    r = render.reshape(render.shape[0], -1)
    g = gt.reshape(gt.shape[0], -1)
    a = np.zeros(r.shape[0], dtype=np.float64)
    b = np.zeros(r.shape[0], dtype=np.float64)
    for i in range(r.shape[0]):
        ri, gi = r[i], g[i]
        A = np.stack([ri, np.ones_like(ri)], 1)
        sol, *_ = np.linalg.lstsq(A, gi, rcond=None)
        a[i], b[i] = sol
    out = a[:, None, None] * render + b[:, None, None]
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def mean_match(src, target):
    """Scale each image of `src` so its mean equals the corresponding `target` mean."""
    s = src.reshape(src.shape[0], -1).mean(1).clip(1e-6, None)
    t = target.reshape(target.shape[0], -1).mean(1)
    return (src * (t / s)[:, None, None]).astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/workspace/data/official")
    ap.add_argument("--scenes", default="flowers,bicycle,treehill,stump")
    ap.add_argument("--out", default="/workspace/res/diag.json")
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--alpha", type=float, default=ALPHA)
    ap.add_argument("--n-splits", type=int, default=400)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import torch
    from calib.gsrender import load_splats, render

    rows = []
    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        sc = load_archive_only_scene(args.archive, scene, factor=args.factor, cal_frac=0.5)
        W, H = sc["width"], sc["height"]
        gt_raw = load_images(sc["image_paths"], args.factor, (W, H)).astype(np.float32) / 255.0
        c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K = torch.from_numpy(sc["Ks"]).to(args.device)
        ply = os.path.join(args.archive, "output", scene, "point_cloud",
                           "iteration_40000", "point_cloud.ply")
        if not os.path.isfile(ply):
            cands = [os.path.join(dp, f) for dp, _dn, fn in os.walk(os.path.join(args.archive, "output", scene))
                     for f in fn if f.endswith(".ply")]
            ply = sorted(cands)[-1]
        full = load_splats(ply, device=args.device)
        idx = list(range(len(sc["image_paths"])))

        @torch.no_grad()
        def render_all(splats):
            out = []
            for s in range(0, len(idx), 4):
                it = torch.as_tensor(idx[s:s + 4], device=args.device)
                col = render(splats, c2w[it], K[it], W, H)["colors"].permute(0, 3, 1, 2)
                out.append(col.mean(1).cpu().numpy())
            return np.concatenate(out, 0).astype(np.float32)

        ren = render_all(full)
        k = max(1, int(round(0.3 * full.n)))
        keep = torch.argsort(-full.opacities)[:k].sort().values
        ren30 = render_all(full.subset(keep))

        variants = {
            "raw": (gt_raw, ren, ren30),
            "norm_gt": (normalize_exposure(gt_raw * 255.0), ren, ren30),
            "norm_both": (normalize_exposure(gt_raw * 255.0),
                          mean_match(ren, normalize_exposure(gt_raw * 255.0)),
                          mean_match(ren30, normalize_exposure(gt_raw * 255.0))),
            "gain": (gt_raw, per_image_gain(ren, gt_raw), per_image_gain(ren30, gt_raw)),
            "affine": (gt_raw, per_image_affine(ren, gt_raw), per_image_affine(ren30, gt_raw)),
        }
        row = dict(scene=scene, n_primitives=int(full.n), n_views=len(idx), W=W, H=H,
                   render_mean=float(ren.mean()), gt_mean=float(gt_raw.mean()),
                   protocols={})
        for name, (g, r, r30) in variants.items():
            rc = np.abs(r - g)
            rp = np.abs(r30 - g)
            cb = conformal_block(rc, rp, n_splits=args.n_splits, alpha=args.alpha)
            row["protocols"][name] = dict(
                psnr=psnr(r, g), psnr30=psnr(r30, g),
                resid_median=float(np.median(rc)), resid_mean=float(rc.mean()),
                q=float(cq(rc[: max(2, len(idx) // 2)].reshape(-1), args.alpha)),
                **cb)
        # how much of the residual is a pure per-image brightness offset?
        row["gt_view_means"] = [round(float(x), 3) for x in gt_raw.reshape(gt_raw.shape[0], -1).mean(1)]
        row["render_view_means"] = [round(float(x), 3) for x in ren.reshape(ren.shape[0], -1).mean(1)]
        rows.append(row)
        print(f"\n=== {scene}: {full.n} primitives, {len(idx)} views, {W}x{H} ===")
        for name in variants:
            p = row["protocols"][name]
            print(f"  {name:10s} PSNR {p['psnr']:5.2f} dB  med_resid {p['resid_median']:.4f}  "
                  f"q {p['q']:.4f}  cov {p['clean_mean']:.3f}  drop30 {100*p['drop_mean']:+.1f}pp "
                  f"[{100*p['drop_lo']:+.1f},{100*p['drop_hi']:+.1f}]")
        print(f"  gt view means {row['gt_view_means'][:6]} ...")
        print(f"  render means  {row['render_view_means'][:6]} ...", flush=True)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(rows, open(args.out, "w", encoding="utf-8"), indent=1)
    print("\nWROTE", args.out)


if __name__ == "__main__":
    main()
