"""Second downstream task: global geometric registration consensus (numpy only).

Why a second task family
------------------------
The main paper task is *local* re-localisation: a 32x32 ground-truth patch searched inside a
small window of the rendered image.  A reviewer's natural objection is that the decoupling we
report could be a property of one matcher.

This task is the front-end of a different family: a relocalisation / visual-odometry pipeline
first establishes 2-D correspondences and then fits a global geometric model, and what
matters downstream is the *consensus* of that fit, not any single patch.  We therefore

  1. detect Harris corners on the ground-truth image,
  2. describe each corner by its 9x9 mean-subtracted patch,
  3. match it in the rendered image inside a +-8 px window by NCC with a ratio test,
  4. fit a global similarity (scale 1, rotation 0, one translation) by RANSAC,
  5. report the inlier ratio at 2 px and the median residual of inliers.

A render that is a faithful copy of the capture keeps almost every match geometrically
consistent (inlier ratio near 1); an edited render breaks the consensus.

    python experiments/second_task2.py --archive /workspace/data/out3dgs \
        --scenes bicycle,flowers --out /workspace/res/second_task.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "research", "code"))


# ------------------------------------------------------------------ primitives
def harris(gray: np.ndarray, n: int = 200, k: float = 0.04, min_dist: int = 6) -> np.ndarray:
    """Top-n Harris corners as (y, x) ints, greedily separated by min_dist."""
    g = gray.astype(np.float32)
    gy, gx = np.gradient(g)
    Ixx, Iyy, Ixy = gx * gx, gy * gy, gx * gy
    s = 3
    ker = np.ones((2 * s + 1, 2 * s + 1), np.float32)

    def blur(a):
        out = np.zeros_like(a)
        H, W = a.shape
        p = np.pad(a, s, mode="edge")
        for dy in range(2 * s + 1):
            for dx in range(2 * s + 1):
                out += p[dy:dy + H, dx:dx + W] * ker[dy, dx]
        return out / ker.sum()

    Sxx, Syy, Sxy = blur(Ixx), blur(Iyy), blur(Ixy)
    det = Sxx * Syy - Sxy * Sxy
    tr = Sxx + Syy
    R = det - k * tr * tr
    R[:4, :] = R[-4:, :] = 0
    R[:, :4] = R[:, -4:] = 0
    idx = np.argsort(R.ravel())[::-1]
    pts = []
    used = np.zeros_like(R, bool)
    for f in idx:
        y, x = divmod(int(f), R.shape[1])
        if used[max(0, y - min_dist):y + min_dist + 1, max(0, x - min_dist):x + min_dist + 1].any():
            continue
        used[y, x] = True
        pts.append((y, x))
        if len(pts) >= n:
            break
    return np.asarray(pts, np.int32)


def ncc_map(img: np.ndarray, patch: np.ndarray) -> np.ndarray:
    H, W = img.shape
    P = patch.shape[0]
    if H < P or W < P:
        return np.zeros((0, 0), np.float32)
    win = np.lib.stride_tricks.sliding_window_view(img, (P, P))
    win = win.reshape(H - P + 1, W - P + 1, -1).astype(np.float32)
    win -= win.mean(axis=2, keepdims=True)
    den = np.sqrt((win ** 2).sum(axis=2))
    p = patch.reshape(-1).astype(np.float32)
    p = p - p.mean()
    pn = np.sqrt((p ** 2).sum())
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (win @ p) / (den * pn)
    out[~np.isfinite(out)] = 0.0
    return out


def match(gt: np.ndarray, img: np.ndarray, corners: np.ndarray, radius: int,
          ratio: float, min_ncc: float):
    """Return (src, dst) correspondences with a Lowe-style ratio test."""
    H, W = img.shape
    src, dst, scores = [], [], []
    for (y, x) in corners:
        P = 9
        h = P // 2
        if y - h < 0 or x - h < 0 or y + h >= H or x + h >= W:
            continue
        patch = gt[y - h:y + h + 1, x - h:x + h + 1]
        y0, y1 = max(0, y - radius - h), min(H, y + radius + h + 1)
        x0, x1 = max(0, x - radius - h), min(W, x + radius + h + 1)
        win = img[y0:y1, x0:x1]
        if win.shape[0] < P or win.shape[1] < P:
            continue
        m = ncc_map(win, patch)
        if m.size == 0:
            continue
        flat = m.ravel()
        best = int(flat.argmax())
        bestv = float(flat[best])
        if bestv < min_ncc:
            continue
        # ratio test against the best peak outside a 3x3 neighbourhood
        iy, ix = np.unravel_index(best, m.shape)
        mask = np.ones_like(m, bool)
        mask[max(0, iy - 1):iy + 2, max(0, ix - 1):ix + 2] = False
        second = float(m[mask].max()) if mask.any() else -1.0
        if second > 0 and bestv < ratio * second:
            continue
        src.append((y, x))
        dst.append((iy + y0, ix + x0))
        scores.append(bestv)
    return np.asarray(src, np.float32), np.asarray(dst, np.float32), np.asarray(scores, np.float32)


def fit_translation_ransac(src: np.ndarray, dst: np.ndarray, thr: float = 2.0,
                           iters: int = 300, seed: int = 0):
    """Single-translation model (the identity motion) fitted by RANSAC.

    Returns (inlier_ratio, median_inlier_residual_px, best_translation).
    """
    n = len(src)
    if n < 4:
        return 0.0, float("nan"), (0.0, 0.0)
    rng = np.random.default_rng(seed)
    d = dst - src
    best_inl, best_t = None, (0.0, 0.0)
    for _ in range(iters):
        i = int(rng.integers(n))
        t = d[i]
        res = np.abs(d - t).max(axis=1)
        inl = res <= thr
        if best_inl is None or inl.sum() > best_inl.sum():
            best_inl, best_t = inl, (float(t[0]), float(t[1]))
    res = np.abs(d - np.asarray(best_t)).max(axis=1)
    inl = res <= thr
    med = float(np.median(np.abs(d[inl] - np.asarray(best_t)).max(axis=1))) if inl.any() else float("nan")
    return float(inl.mean()), med, best_t


# ------------------------------------------------------------------ scene / render
def build_scene(archive, scene, factor):
    from calib.archive_only import load_archive_only_scene
    from calib.colmap_io import load_images
    sc = load_archive_only_scene(archive, scene, factor=factor, cal_frac=0.5)
    W, H = sc["width"], sc["height"]
    gt = load_images(sc["image_paths"], factor, (W, H)).astype(np.float32) / 255.0
    return sc, gt, W, H


def find_ply(archive, scene):
    base = os.path.join(archive, "output", scene)
    for c in (os.path.join(base, "point_cloud", "iteration_40000", "point_cloud.ply"),
              os.path.join(base, "point_cloud", "iteration_30000", "point_cloud.ply")):
        if os.path.isfile(c):
            return c
    raise SystemExit(f"no ply for {scene}")


def render_chw(splats, c2w, K, W, H, device, chunk=4):
    import torch
    from calib.gsrender import render
    cols = []
    n = c2w.shape[0]
    with torch.no_grad():
        for s in range(0, n, chunk):
            it = torch.arange(s, min(n, s + chunk), device=device)
            cols.append(render(splats, c2w[it], K[it], W, H)["colors"].permute(0, 3, 1, 2).float().cpu())
    return torch.cat(cols, 0)


def boot(vals, n_boot=2000, seed=0):
    v = np.asarray([x for x in vals if x == x], np.float64)
    if v.size == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    m = rng.choice(v, size=(n_boot, v.size), replace=True).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--scenes", default="bicycle,flowers")
    ap.add_argument("--out", default="/workspace/res/second_task.json")
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--radius", type=int, default=8)
    ap.add_argument("--ratio", type=float, default=0.85)
    ap.add_argument("--min-ncc", type=float, default=0.5)
    ap.add_argument("--thr", type=float, default=2.0)
    ap.add_argument("--corners", type=int, default=200)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--synthetic-test", action="store_true")
    args = ap.parse_args()

    if args.synthetic_test:
        rng = np.random.default_rng(0)
        base = rng.random((160, 200)).astype(np.float32)
        base = (base * 255).astype(np.uint8).astype(np.float32) / 255.0
        for name, img in (("identical", base),
                          ("shift1", np.roll(base, 1, axis=1)),
                          ("noise", np.clip(base + rng.normal(0, 0.06, base.shape), 0, 1))):
            c = harris(base, 120)
            src, dst, sc = match(base, img, c, args.radius, args.ratio, args.min_ncc)
            ir, med, t = fit_translation_ransac(src, dst, args.thr)
            print(f"  synthetic {name:10s} matches={len(src):4d} inlier_ratio={ir:.3f} "
                  f"median_resid={med:.2f} t={t}")
        return

    import torch
    from calib.gsrender import load_splats
    rows = []
    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        sc, gt, W, H = build_scene(args.archive, scene, args.factor)
        c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K = torch.from_numpy(sc["Ks"]).to(args.device)
        base = load_splats(find_ply(args.archive, scene), device=args.device)
        variants = {"clean": base}
        for name, ratio in (("prune50", 0.5), ("prune30", 0.3), ("prune10", 0.1)):
            k = max(1, int(round(ratio * base.n)))
            keep = torch.argsort(-base.opacities)[:k].sort().values
            variants[name] = base.subset(keep)
        gts = gt.mean(3)
        out = dict(scene=scene, n_views=int(len(gt)), W=W, H=H, radius=args.radius,
                   ratio=args.ratio, min_ncc=args.min_ncc, thr=args.thr, variants={})
        for name, sp in variants.items():
            img = render_chw(sp, c2w, K, W, H, args.device).mean(1).numpy()
            ir, med, nm, raw, nccs, ir1 = [], [], [], [], [], []
            for v in range(len(gts)):
                c = harris(gts[v], args.corners)
                src, dst, sco = match(gts[v], img[v], c, args.radius, args.ratio, args.min_ncc)
                i_, m_, _t = fit_translation_ransac(src, dst, args.thr)
                i1_, _, _ = fit_translation_ransac(src, dst, 1.0)
                ir.append(i_)
                med.append(m_)
                nm.append(len(src))
                nccs.append(float(sco.mean()) if len(sco) else float('nan'))
                ir1.append(i1_)
                raw.append(dict(inlier_ratio=i_, inlier_ratio_1px=i1_, median_resid=m_,
                                n_matches=len(src),
                                mean_ncc=float(sco.mean()) if len(sco) else float('nan')))
            lo, hi = boot(ir)
            lo1, hi1 = boot(ir1)
            out["variants"][name] = dict(inlier_ratio_mean=float(np.nanmean(ir)),
                                         lo=lo, hi=hi,
                                         inlier_ratio_1px=float(np.nanmean(ir1)), lo1=lo1, hi1=hi1,
                                         median_resid=float(np.nanmedian(med)),
                                         n_matches_mean=float(np.nanmean(nm)),
                                         mean_ncc=float(np.nanmean(nccs)), per_view=raw)
            d = out["variants"][name]
            print(f"[{scene}] {name:8s} inlier@2px={d['inlier_ratio_mean']:.3f} [{lo:.3f},{hi:.3f}]  "
                  f"inlier@1px={d['inlier_ratio_1px']:.3f}  resid={d['median_resid']:.2f}px  "
                  f"matches={d['n_matches_mean']:.0f}  ncc={d['mean_ncc']:.3f}", flush=True)
            del img
            torch.cuda.empty_cache()
        rows.append(out)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(rows, open(args.out, "w", encoding="utf-8"), indent=1)
    print("WROTE", args.out)


if __name__ == "__main__":
    main()
