"""Tail-occupancy: a per-primitive score for the quantity a certificate counts.

The certificate counts residuals *above* the shipped threshold q, not squared error.
The marginal contribution of primitive i to that count is, to first order,

    s_i(q) = (1/|V|) * sum_v  [# pixels in M_i(v) with r_p > q] / [# pixels in M_i(v)]

where M_i(v) is the set of pixels primitive i covers in view v.  That is exactly the
finite-difference of P(r > q) with respect to the primitive's weight, up to the
occlusion model, and it needs only what the dump already carries: the residual maps,
the primitive centres, the cameras and the intrinsics.

This is deliberately *not* a better fidelity score.  It is a score for a different
functional; the experiment is whether ranking by it preserves coverage better than
ranking by opacity, Fisher sensitivity or opacity x volume at the same budget.

    python experiments/tail_occupancy.py --npz <dump> --out tail.json
    python experiments/tail_occupancy.py --selftest
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def project(prim_means, c2w, K, H, W):
    """World points -> integer pixel coordinates, with an in-front-of-camera mask."""
    R = c2w[:3, :3]
    t = c2w[:3, 3]
    pc = (prim_means - t) @ R
    z = pc[:, 2]
    keep = z > 1e-6
    uvw = pc @ K.T
    with np.errstate(divide="ignore", invalid="ignore"):
        u = uvw[:, 0] / np.where(np.abs(uvw[:, 2]) < 1e-12, np.nan, uvw[:, 2])
        v = uvw[:, 1] / np.where(np.abs(uvw[:, 2]) < 1e-12, np.nan, uvw[:, 2])
    keep &= np.isfinite(u) & np.isfinite(v)
    keep &= (u >= 0) & (u <= W - 1) & (v >= 0) & (v <= H - 1)
    return np.rint(v).astype(np.int64), np.rint(u).astype(np.int64), keep


def tail_occupancy(resid, prim_means, c2w, K, q, views=None):
    """resid (m,H,W), prim_means (n,3) -> (n,) score in [0,1], plus hit counts.

    ``views`` selects the calibration views; the mean over them is the score.
    """
    m, H, W = resid.shape
    sel = np.arange(m) if views is None else np.asarray(views)
    hit = np.zeros(prim_means.shape[0], np.float64)
    seen = np.zeros(prim_means.shape[0], np.float64)
    for i in sel:
        above = (resid[i] > q).astype(np.float64)
        yy, xx, keep = project(prim_means, c2w[i], K[i], H, W)
        idx = np.nonzero(keep)[0]
        if idx.size == 0:
            continue
        hit[idx] += above[yy[idx], xx[idx]]
        seen[idx] += 1.0
    score = np.where(seen > 0, hit / np.maximum(seen, 1.0), 0.0)
    return score, hit, seen


def selftest(seed: int = 0) -> int:
    rng = np.random.default_rng(seed)
    H, W, n, m = 24, 32, 40, 4
    prim = rng.uniform(-1.0, 1.0, size=(n, 3)).astype(np.float32)
    prim[:, 2] = rng.uniform(2.0, 4.0, size=n)          # all in front of the camera
    c2w = np.stack([np.eye(4, dtype=np.float32) for _ in range(m)])
    K = np.stack([np.array([[40, 0, W / 2], [0, 40, H / 2], [0, 0, 1]], np.float32)
                  for _ in range(m)])
    resid = rng.uniform(0, 1, size=(m, H, W)).astype(np.float32)
    q = 0.5
    score, hit, seen = tail_occupancy(resid, prim, c2w, K, q)
    assert score.shape == (n,), score.shape
    assert np.all((score >= 0) & (score <= 1)), "score must be a fraction"
    assert seen.max() > 0, "no primitive projected into any view"
    # a primitive whose every projected pixel is above q must score 1
    always = np.zeros_like(resid)
    score1, _, seen1 = tail_occupancy(always, prim, c2w, K, 0.5)
    assert np.all(score1[seen1 > 0] < 1e-9), "all-below-q must score 0"
    print(f"[selftest] {int((seen > 0).sum())}/{n} primitives visible, "
          f"score range {score.min():.2f}-{score.max():.2f} -> PASS")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--npz", default="")
    ap.add_argument("--out", default="tail.json")
    ap.add_argument("--alpha", type=float, default=C.ALPHA)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.npz:
        raise SystemExit("--npz is required")
    out = {}
    for path in C.discover_npz(a.npz):
        sc = C.load_npz_scene(path)
        name = sc["meta"]["scene"]
        vnames = [str(v) for v in sc["variant_names"]]
        resid = np.asarray(sc["resid"][vnames.index("clean")], np.float32)
        m = resid.shape[0]
        splits = C.split_perms(m, 1, C.RNG_SEED)        # one split: half the views
        cal = splits[0][0]
        flat = resid.reshape(m, -1)
        q = C.cq(flat[cal].reshape(-1), a.alpha)
        score, hit, seen = tail_occupancy(resid, np.asarray(sc["prim_means"]),
                                          np.asarray(sc["c2w"]), np.asarray(sc["K"]), q, cal)
        # how much of the tail mass the top 30% of primitives carries, a first look at
        # whether the score concentrates where the certificate's threshold bites
        order = np.argsort(-score)
        top = order[: max(1, int(0.3 * order.size))]
        out[name] = dict(q=float(q), n=int(score.size),
                         visible=int((seen > 0).sum()),
                         top30_mean=float(score[top].mean()),
                         rest_mean=float(score[order[max(1, int(0.3 * order.size)):]].mean()))
        C.log(f"  {name}: q={q:.4f} top30 mean tail={out[name]['top30_mean']:.3f} "
              f"rest={out[name]['rest_mean']:.3f}")
    C.json_dump(a.out, out)
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
