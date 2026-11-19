"""Equivalence gate: the fast (sorted + searchsorted) coverage must equal the
naive boolean-array protocol of ``audit_bound.py`` bit for bit.

    PYTHONPATH=/workspace/code/research/code:/workspace/code python \
        experiments/a4_verify_fast.py --npz /workspace/res/a4/check/flowers.npz
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import rd_analyse as A  # noqa: E402


def naive_drops(resid, names, splits, alpha):
    V, m = resid.shape[0], resid.shape[1]
    flat = resid.reshape(V, m, -1).astype(np.float32)
    ci = list(names).index("clean")
    out = {n: [] for n in names if n != "clean"}
    covs = []
    for cal, dep in splits:
        cal, dep = np.asarray(cal), np.asarray(dep)
        q = C.cq(flat[ci][cal].reshape(-1), alpha)
        base = float((flat[ci][dep] <= q).mean())
        covs.append(base)
        for vi, n in enumerate(names):
            if n != "clean":
                out[n].append(float((flat[vi][dep] <= q).mean()) - base)
    return {n: np.asarray(v) for n, v in out.items()}, np.asarray(covs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", default="/workspace/res/a4/check/flowers.npz")
    ap.add_argument("--n-splits", type=int, default=60)
    ap.add_argument("--alpha", type=float, default=C.ALPHA)
    args = ap.parse_args()

    sc = C.load_npz_scene(args.npz)
    names = [str(v) for v in sc["variant_names"]]
    resid = np.asarray(sc["resid"])
    m = resid.shape[1]
    splits = C.split_perms(m, args.n_splits, C.RNG_SEED)
    fast, fast_cov, _q, _q2 = A.variant_drops(resid, names, splits, args.alpha)
    slow, slow_cov = naive_drops(resid, names, splits, args.alpha)

    print(f"{os.path.basename(args.npz)}: {len(names)} variants x {m} views, "
          f"{args.n_splits} splits")
    print(f"  clean coverage  fast={fast_cov.mean():.10f} slow={slow_cov.mean():.10f} "
          f"maxabs={float(np.abs(fast_cov - slow_cov).max()):.3e}")
    worst = 0.0
    for n in slow:
        d = float(np.abs(fast[n] - slow[n]).max())
        worst = max(worst, d)
        print(f"  {n:>8s} drop_mean fast={fast[n].mean():+.8f} "
              f"slow={slow[n].mean():+.8f} maxabs={d:.3e}")
    ok = worst < 1e-9
    print(f"  {'PASS' if ok else 'FAIL'}  max abs deviation {worst:.3e}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
