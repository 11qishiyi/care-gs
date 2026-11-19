"""J7 --- a *coverage-aware* pruning score, and why it might not save pruning.

The paper's pruning arms rank primitives by opacity (`prune50`) or by a Fisher/PUP diagonal (`pup30`). Both are
coverage-blind: they say how much a primitive contributes to the image, not whether deleting it moves the rendered
error across the shipped quantile `q`. A reviewer's obvious question is therefore "would a score designed for
coverage do better?", and this file is the instrument for answering it.

The score (per primitive j, for one view):

    s_j = alpha_j * A_j * (1 - |e(p_j) - q| / q)_+
    A_j = pi * (f * s_max / z_j)^2          # screen-space footprint, from the pinhole geometry
    e(p_j) = min over a 3x3 window of the clean residual map at the projected centre p_j

Intuition: a primitive is dangerous to delete when it covers many pixels, is opaque, and those pixels sit *near the
threshold* --- there the error can cross `q` and the coverage statement breaks. A primitive whose pixels are far
from `q` (either comfortably inside or hopelessly outside) costs little to remove.

Everything is numpy + torch-free except the optional projection helper, so `--selftest` runs on a CPU with synthetic
splats and checks the properties the score must have.

    python experiments/j7_score.py --selftest
"""
from __future__ import annotations

import argparse
import sys

import numpy as np


# ----------------------------------------------------------------------------- score
def project_centres(means: np.ndarray, c2w: np.ndarray, K: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Project primitive centres. Returns (u, v, depth) in pixels; depth <= 0 marks behind-camera."""
    R, t = c2w[:3, :3], c2w[:3, 3]
    cam = (means - t) @ R                      # world -> camera (R^T (x - t))
    z = cam[:, 2]
    safe = np.where(np.abs(z) < 1e-6, 1e-6, z)
    uvw = cam @ K.T
    u = uvw[:, 0] / safe
    v = uvw[:, 1] / safe
    return u, v, z


def footprint_area(scales: np.ndarray, z: np.ndarray, focal: float) -> np.ndarray:
    """pi * (f * s_max / z)^2 -- the area a primitive can touch on screen."""
    s_max = scales.max(axis=1) if scales.ndim == 2 else scales
    return np.pi * (focal * s_max / np.maximum(np.abs(z), 1e-6)) ** 2


def coverage_risk(means: np.ndarray, scales: np.ndarray, opacities: np.ndarray,
                  c2w: np.ndarray, K: np.ndarray, resid: np.ndarray, q: float) -> np.ndarray:
    """s_j = alpha_j * A_j * (1 - |e(p_j) - q| / q)_+ ; zero for off-screen or behind-camera primitives."""
    H, W = resid.shape
    u, v, z = project_centres(np.asarray(means, np.float64), np.asarray(c2w, np.float64), np.asarray(K, np.float64))
    focal = float(0.5 * (K[0, 0] + K[1, 1]))
    A = footprint_area(np.asarray(scales, np.float64), z, focal)
    ui = np.rint(u).astype(np.int64)
    vi = np.rint(v).astype(np.int64)
    inside = (z > 0) & (ui >= 0) & (ui < W) & (vi >= 0) & (vi < H)
    e = np.full(ui.shape, np.inf)
    # 3x3 window minimum keeps the score robust to a one-pixel projection error
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            yy = np.clip(vi + dy, 0, H - 1)
            xx = np.clip(ui + dx, 0, W - 1)
            e = np.minimum(e, resid[yy, xx])
    closeness = np.clip(1.0 - np.abs(e - q) / max(q, 1e-12), 0.0, None)
    s = np.asarray(opacities, np.float64) * A * closeness
    return np.where(inside & np.isfinite(s), s, 0.0)


def select(scores: np.ndarray, keep: float) -> np.ndarray:
    """Indices of the `keep` fraction with the largest score, returned sorted (stable output for a given input)."""
    n = scores.size
    k = max(1, int(round(keep * n)))
    return np.sort(np.argsort(-scores, kind="stable")[:k])


# ----------------------------------------------------------------------------- selftest
def selftest() -> int:
    rng = np.random.default_rng(7)
    n, H, W = 4000, 240, 320
    means = rng.normal(0, 1.5, (n, 3))
    means[:, 2] += 4.0                                     # in front of the camera
    scales = np.exp(rng.normal(-2.0, 0.4, (n, 3)))
    opac = rng.uniform(0.2, 1.0, n)
    c2w = np.eye(4)
    K = np.array([[300.0, 0, W / 2], [0, 300.0, H / 2], [0, 0, 1]])
    resid = rng.exponential(0.02, (H, W))
    q = float(np.quantile(resid, 0.9))

    s = coverage_risk(means, scales, opac, c2w, K, resid, q)
    ok = True

    def check(cond: bool, msg: str) -> None:
        nonlocal ok
        print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")
        ok = ok and cond

    check(np.all(np.isfinite(s)), "scores finite")
    check(np.all(s >= 0), "scores non-negative")
    check(int((s > 0).sum()) > 100, f"a non-trivial number of primitives score > 0 ({(s > 0).sum()} of {n})")

    s2 = coverage_risk(means, scales, opac * 2.0, c2w, K, resid, q)
    check(np.allclose(s2, 2 * s, rtol=1e-9, atol=1e-12), "linear in opacity")

    s3 = coverage_risk(means, scales * 2.0, opac, c2w, K, resid, q)
    check(np.allclose(s3, 4 * s, rtol=1e-6, atol=1e-12), "quadratic in scale (area)")

    # a primitive far from the threshold must score below one that sits on it
    near = coverage_risk(np.array([[0, 0, 4.0]]), np.array([[0.02, 0.02, 0.02]]), np.array([0.9]), c2w, K,
                         np.full((H, W), q), q)
    far = coverage_risk(np.array([[0, 0, 4.0]]), np.array([[0.02, 0.02, 0.02]]), np.array([0.9]), c2w, K,
                        np.full((H, W), 0.0), q)
    check(near[0] > 0 and far[0] == 0, f"threshold-aware: e=q scores {near[0]:.4g}, e=0 scores {far[0]:.4g}")

    # the ranking must differ from opacity (otherwise the whole exercise is moot)
    op_rank = np.argsort(-opac)
    cov_rank = np.argsort(-s)
    overlap = len(set(op_rank[: n // 2]) & set(cov_rank[: n // 2])) / (n // 2)
    check(overlap < 0.95, f"top-50% overlap with opacity ranking = {overlap:.2f} (< 0.95)")

    a, b = select(s, 0.5), select(s, 0.5)
    check(np.array_equal(a, b) and a.size == n // 2, "selection deterministic and of the right size")

    print("\nSELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


def alpha_area(means: np.ndarray, scales: np.ndarray, opacities: np.ndarray,
               c2w: np.ndarray, K: np.ndarray) -> np.ndarray:
    """The ablation of `coverage_risk`: opacity times footprint, with the proximity-to-q term removed.

    If this beats plain opacity, the earlier loss was the proximity term rather than the coverage idea; if it does
    not, opacity is simply hard to beat. Zero for off-screen or behind-camera primitives, same as `coverage_risk`.
    """
    u, v, z = project_centres(np.asarray(means, np.float64), np.asarray(c2w, np.float64), np.asarray(K, np.float64))
    focal = float(0.5 * (K[0, 0] + K[1, 1]))
    A = footprint_area(np.asarray(scales, np.float64), z, focal)
    s = np.asarray(opacities, np.float64) * A
    inside = z > 0
    return np.where(inside & np.isfinite(s), s, 0.0)
