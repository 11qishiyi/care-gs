"""Third task family: two-view relative pose (visual-odometry error), numpy only.

Why a third family
-------------------
The paper's localised weakness is that both reported tasks are hand-built *matchers*: a patch
template matcher and a global registration consensus. A consumer of a 3DGS asset in a
relocalisation or odometry pipeline does something else again: it matches features between two
views and solves for the relative pose. The quality of the asset then shows up as the accuracy
of that pose, not as a match count.

This module implements that task end to end with numpy:

  1. Harris corners on each view, described by their 9x9 mean-subtracted patch;
  2. correspondences between two consecutive views by NCC with a ratio test;
  3. normalised 8-point essential matrix, rank-2 projection, decomposition into (R, t);
  4. cheirality check to pick the right (R, t) among the four candidates;
  5. error against the pose estimated the same way from the ground-truth pair, so the metric
     is the *degradation* of the pose, not its absolute accuracy.

    python experiments/third_task.py --archive <archive> --scenes bicycle,flowers --out out.json
    python experiments/third_task.py --synthetic-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "research", "code"))

PATCH = 9
HALF = PATCH // 2


# ------------------------------------------------------------------ features / matching
def harris(gray: np.ndarray, n: int = 300, k: float = 0.04, min_dist: int = 7) -> np.ndarray:
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
    R = (Sxx * Syy - Sxy * Sxy) - k * (Sxx + Syy) ** 2
    R[:HALF + 2, :] = R[-(HALF + 2):, :] = 0
    R[:, :HALF + 2] = R[:, -(HALF + 2):] = 0
    idx = np.argsort(R.ravel())[::-1]
    used = np.zeros_like(R, bool)
    pts = []
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


def correspondences(g1: np.ndarray, g2: np.ndarray, corners: np.ndarray, radius: int,
                    ratio: float = 0.85, min_ncc: float = 0.5):
    H, W = g2.shape
    src, dst = [], []
    for (y, x) in corners:
        if y - HALF < 0 or x - HALF < 0 or y + HALF >= H or x + HALF >= W:
            continue
        patch = g1[y - HALF:y + HALF + 1, x - HALF:x + HALF + 1]
        y0, y1 = max(0, y - radius - HALF), min(H, y + radius + HALF + 1)
        x0, x1 = max(0, x - radius - HALF), min(W, x + radius + HALF + 1)
        win = g2[y0:y1, x0:x1]
        if win.shape[0] < PATCH or win.shape[1] < PATCH:
            continue
        m = ncc_map(win, patch)
        if m.size == 0:
            continue
        flat = m.ravel()
        best = int(flat.argmax())
        bestv = float(flat[best])
        if bestv < min_ncc:
            continue
        iy, ix = np.unravel_index(best, m.shape)
        mask = np.ones_like(m, bool)
        mask[max(0, iy - 1):iy + 2, max(0, ix - 1):ix + 2] = False
        second = float(m[mask].max()) if mask.any() else -1.0
        if second > 0 and bestv < ratio * second:
            continue
        src.append((x, y))              # (x, y) convention for the geometry below
        dst.append((ix + x0, iy + y0))
    return np.asarray(src, np.float32), np.asarray(dst, np.float32)


# ------------------------------------------------------------------ two-view geometry
def _normalise(pts: np.ndarray):
    c = pts.mean(axis=0)
    d = np.sqrt(((pts - c) ** 2).sum(axis=1)).mean()
    s = np.sqrt(2) / max(d, 1e-9)
    T = np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1]], np.float64)
    hom = np.column_stack([pts, np.ones(len(pts), np.float64)])
    return (T @ hom.T).T[:, :2], T


def essential_8pt(p1: np.ndarray, p2: np.ndarray):
    """Normalised 8-point algorithm. Returns (E, inlier_mask) with E in pixel coordinates."""
    if len(p1) < 8:
        return None, None
    n1, T1 = _normalise(p1)
    n2, T2 = _normalise(p2)
    A = np.column_stack([n2[:, 0] * n1[:, 0], n2[:, 0] * n1[:, 1], n2[:, 0],
                         n2[:, 1] * n1[:, 0], n2[:, 1] * n1[:, 1], n2[:, 1],
                         n1[:, 0], n1[:, 1], np.ones(len(n1))])
    _, _, Vt = np.linalg.svd(A)
    F = Vt[-1].reshape(3, 3)
    U, S, Vt2 = np.linalg.svd(F)
    S[-1] = 0.0
    F = U @ np.diag(S) @ Vt2
    E = T2.T @ F @ T1
    E /= max(np.abs(E).max(), 1e-12)
    return E, None


def sampson(E: np.ndarray, p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
    h1 = np.column_stack([p1, np.ones(len(p1))])
    h2 = np.column_stack([p2, np.ones(len(p2))])
    Ex1 = h1 @ E.T
    Etx2 = h2 @ E
    num = (h2 * Ex1).sum(axis=1) ** 2
    den = Ex1[:, 0] ** 2 + Ex1[:, 1] ** 2 + Etx2[:, 0] ** 2 + Etx2[:, 1] ** 2
    return num / np.maximum(den, 1e-12)


def pose_from_essential(E: np.ndarray, K: np.ndarray, p1: np.ndarray, p2: np.ndarray):
    """Decompose E into (R, t) and resolve the four-fold ambiguity by cheirality."""
    U, _, Vt = np.linalg.svd(E)
    if np.linalg.det(U) < 0:
        U = -U
    if np.linalg.det(Vt) < 0:
        Vt = -Vt
    W = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], np.float64)
    candidates = [(U @ W @ Vt, U[:, 2]), (U @ W @ Vt, -U[:, 2]),
                  (U @ W.T @ Vt, U[:, 2]), (U @ W.T @ Vt, -U[:, 2])]
    Kinv = np.linalg.inv(K)
    hom1 = np.column_stack([p1, np.ones(len(p1))])
    hom2 = np.column_stack([p2, np.ones(len(p2))])
    ray1 = (Kinv @ hom1.T).T
    ray2 = (Kinv @ hom2.T).T
    P1 = np.column_stack([np.eye(3), np.zeros(3)])
    best, best_inl = None, -1
    for R, t in candidates:
        P2 = np.column_stack([R, t])
        inl = 0
        for i in range(min(60, len(ray1))):
            A = np.vstack([ray1[i, 0] * P1[2] - P1[0], ray1[i, 1] * P1[2] - P1[1],
                           ray2[i, 0] * P2[2] - P2[0], ray2[i, 1] * P2[2] - P2[1]])
            _, _, V = np.linalg.svd(A)
            X = V[-1]
            if abs(X[3]) < 1e-12:
                continue
            X = X / X[3]
            z2 = (R @ X[:3])[2] + t[2]
            if X[2] > 0 and z2 > 0:
                inl += 1
        if inl > best_inl:
            best, best_inl = (R, t), inl
    return best


def rotation_angle(R: np.ndarray) -> float:
    c = (np.trace(R) - 1.0) / 2.0
    return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))


def direction_angle(t1: np.ndarray, t2: np.ndarray) -> float:
    a = t1 / max(np.linalg.norm(t1), 1e-12)
    b = t2 / max(np.linalg.norm(t2), 1e-12)
    c = float(np.clip(abs(a @ b), -1.0, 1.0))
    return float(np.degrees(np.arccos(c)))


def pair_pose(g1, g2, K, radius: int, corners: int):
    c = harris(g1, corners)
    p1, p2 = correspondences(g1, g2, c, radius)
    if len(p1) < 8:
        return None
    F, _ = essential_8pt(p1, p2)
    if F is None:
        return None
    # the 8-point solve is in pixel coordinates: convert the fundamental matrix to the
    # essential matrix of the same cameras before decomposing it
    E = K.T @ F @ K
    E /= max(np.abs(E).max(), 1e-12)
    res = pose_from_essential(E, K, p1, p2)
    if res is None:
        return None
    R, t = res
    return dict(R=R, t=t, n_matches=int(len(p1)),
                mean_sampson=float(np.mean(sampson(F, p1, p2))))


# ------------------------------------------------------------------ synthetic self-test
def synthetic_test():
    rng = np.random.default_rng(0)
    K = np.array([[400.0, 0, 160.0], [0, 400.0, 120.0], [0, 0, 1.0]])
    ang = np.radians(6.0)
    R_true = np.array([[np.cos(ang), 0, np.sin(ang)], [0, 1, 0], [-np.sin(ang), 0, np.cos(ang)]])
    t_true = np.array([0.6, 0.05, 0.1])
    X = np.column_stack([rng.uniform(-1.5, 1.5, 120), rng.uniform(-1, 1, 120),
                         rng.uniform(3.0, 7.0, 120)])
    P1 = np.column_stack([np.eye(3), np.zeros(3)])
    P2 = np.column_stack([R_true, t_true])
    x1 = (K @ (P1 @ np.column_stack([X, np.ones(len(X))]).T)).T
    x2 = (K @ (P2 @ np.column_stack([X, np.ones(len(X))]).T)).T
    p1 = x1[:, :2] / x1[:, 2:3]
    p2 = x2[:, :2] / x2[:, 2:3]
    F, _ = essential_8pt(p1, p2)
    E = K.T @ F @ K
    E /= max(np.abs(E).max(), 1e-12)
    R, t = pose_from_essential(E, K, p1, p2)
    print(f"  synthetic: rot err {abs(rotation_angle(R) - rotation_angle(R_true)):.4f} deg, "
          f"dir err {direction_angle(t, t_true):.4f} deg (sign-ambiguous)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--scenes", default="bicycle,flowers")
    ap.add_argument("--out", default="/workspace/res/third_task.json")
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--radius", type=int, default=12)
    ap.add_argument("--corners", type=int, default=300)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--synthetic-test", action="store_true")
    args = ap.parse_args()

    if args.synthetic_test:
        synthetic_test()
        return

    import torch
    from calib.gsrender import load_splats
    from second_task2 import build_scene, find_ply, render_chw

    rows = []
    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        sc, gt, W, H = build_scene(args.archive, scene, args.factor)
        c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K = np.asarray(sc["Ks"][0], np.float64)
        base = load_splats(find_ply(args.archive, scene), device=args.device)
        variants = {"clean": base}
        for name, ratio in (("prune50", 0.5), ("prune30", 0.3), ("prune10", 0.1)):
            k = max(1, int(round(ratio * base.n)))
            keep = torch.argsort(-base.opacities)[:k].sort().values
            variants[name] = base.subset(keep)
        gts = gt.mean(3)
        out = dict(scene=scene, n_views=int(len(gt)), radius=args.radius, variants={})
        # ground-truth pose per consecutive pair
        pairs = [(i, i + 1) for i in range(len(gts) - 1)]
        gt_pose = {}
        for (i, j) in pairs:
            p = pair_pose(gts[i], gts[j], K, args.radius, args.corners)
            if p is not None:
                gt_pose[(i, j)] = p
        for name, sp in variants.items():
            img = render_chw(sp, c2w, K_t := torch.from_numpy(sc["Ks"]).to(args.device),
                             W, H, args.device).mean(1).numpy()
            rot, dirn, ok = [], [], 0
            for (i, j) in pairs:
                if (i, j) not in gt_pose:
                    continue
                p = pair_pose(img[i], img[j], K, args.radius, args.corners)
                if p is None:
                    continue
                ok += 1
                rot.append(abs(rotation_angle(p["R"]) - rotation_angle(gt_pose[(i, j)]["R"])))
                dirn.append(direction_angle(p["t"], gt_pose[(i, j)]["t"]))
            out["variants"][name] = dict(
                n_pairs=ok, rot_err_median=float(np.median(rot)) if rot else float("nan"),
                rot_err_mean=float(np.mean(rot)) if rot else float("nan"),
                dir_err_median=float(np.median(dirn)) if dirn else float("nan"),
                success_5deg=float(np.mean([1.0 if r < 5 else 0.0 for r in rot])) if rot else float("nan"))
            print(f"[{scene}] {name:8s} pairs={ok}/{len(pairs)} "
                  f"rot_err={out['variants'][name]['rot_err_median']:.2f}deg "
                  f"dir_err={out['variants'][name]['dir_err_median']:.2f}deg "
                  f"success@5deg={out['variants'][name]['success_5deg']:.2f}", flush=True)
            del img
            torch.cuda.empty_cache()
        rows.append(out)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(rows, open(args.out, "w", encoding="utf-8"), indent=1, default=float)
    print("WROTE", args.out)


if __name__ == "__main__":
    main()
