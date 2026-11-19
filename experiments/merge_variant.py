"""Merge edit: voxel-based Gaussian merging at a fixed ratio, CPU only.

The paper's edit taxonomy currently has pruning, SH truncation and SH quantisation. Merging is
the obvious fourth edit and the one the paper currently calls harmful "by construction" without
measuring it. This script produces a merged INRIA-format PLY so `node_run.py battery` can
render and score it like any other variant.

Merging rule (documented so a reader can reproduce it): partition primitives by their centre
into world-space voxels of a chosen edge length; inside a voxel replace the group by a single
Gaussian whose

    position  = opacity-weighted mean of the members,
    scale     = RMS of the member scales (a larger blob covers the same footprint),
    rotation  = that of the heaviest member,
    SH        = opacity-weighted mean (all 16 coefficients),
    opacity   = 1 - prod(1 - a_i)   (the compositing-equivalent of the group),

which keeps the voxel's coverage but coarsens its geometry: exactly the "geometric edit" the
paper says should invalidate a certificate.

    python experiments/merge_variant.py --ply in.ply --out merged.ply --target 0.4
    python experiments/merge_variant.py --synthetic-test
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "research", "code"))


# ------------------------------------------------------------------ core
def voxel_merge(means, scales, quats, opac, sh0, shN, edge: float):
    """Merge primitives inside `edge`-sized voxels. Arrays are (N, ...) numpy float32."""
    keys = np.floor(means / edge).astype(np.int64)
    _, inv = np.unique(keys, axis=0, return_inverse=True)
    order = np.argsort(inv, kind="stable")
    inv_sorted = inv[order]
    starts = np.searchsorted(inv_sorted, np.arange(inv.max() + 1))
    ends = np.concatenate([starts[1:], [len(inv_sorted)]])

    out_means, out_scales, out_quats, out_opac, out_sh0, out_shN = [], [], [], [], [], []
    for gi in range(len(starts)):
        idx = order[starts[gi]:ends[gi]]
        a = opac[idx].astype(np.float64)
        w = a / max(a.sum(), 1e-9)
        out_means.append((means[idx] * w[:, None]).sum(0))
        out_scales.append(np.sqrt((scales[idx].astype(np.float64) ** 2 * w[:, None]).sum(0)))
        heaviest = idx[int(np.argmax(a))]
        out_quats.append(quats[heaviest])
        out_opac.append(1.0 - float(np.prod(1.0 - np.clip(a, 0.0, 0.999999))))
        out_sh0.append((sh0[idx].astype(np.float64) * w[:, None, None]).sum(0))
        if shN is not None and shN.shape[1] > 0:
            out_shN.append((shN[idx].astype(np.float64) * w[:, None, None]).sum(0))
    return dict(
        means=np.asarray(out_means, np.float32),
        scales=np.asarray(out_scales, np.float32),
        quats=np.asarray(out_quats, np.float32),
        opacities=np.asarray(out_opac, np.float32),
        sh0=np.asarray(out_sh0, np.float32),
        shN=np.asarray(out_shN, np.float32) if out_shN else None,
    )


def choose_edge(means, target: float) -> float:
    """Binary-search a voxel edge that leaves approximately `target` of the primitives."""
    lo = float(np.percentile(np.linalg.norm(means - means.mean(0), axis=1), 1)) / 50
    hi = float(np.ptp(means, axis=0).max()) / 2
    best = hi
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        keys = np.floor(means / mid).astype(np.int64)
        n = len(np.unique(keys, axis=0))
        if n / len(means) > target:
            lo = mid
        else:
            hi = mid
            best = mid
    return best


# ------------------------------------------------------------------ self-test
def synthetic_test():
    rng = np.random.default_rng(0)
    N = 2000
    means = rng.uniform(-1, 1, (N, 3)).astype(np.float32)
    scales = rng.uniform(0.005, 0.02, (N, 3)).astype(np.float32)
    quats = rng.normal(size=(N, 4)).astype(np.float32)
    quats /= np.linalg.norm(quats, axis=1, keepdims=True)
    opac = rng.uniform(0.05, 0.9, N).astype(np.float32)
    sh0 = rng.normal(size=(N, 1, 3)).astype(np.float32)
    shN = rng.normal(size=(N, 15, 3)).astype(np.float32)

    edge = choose_edge(means, 0.4)
    out = voxel_merge(means, scales, quats, opac, sh0, shN, edge)
    print(f"  synthetic: {N} -> {len(out['means'])} primitives "
          f"({len(out['means'])/N:.2f} of the original) at edge {edge:.4f}")
    # every merged opacity must be at least the largest member opacity
    keys = np.floor(means / edge).astype(np.int64)
    _, inv = np.unique(keys, axis=0, return_inverse=True)
    worst = 0.0
    for gi in range(inv.max() + 1):
        idx = np.where(inv == gi)[0]
        expected = 1.0 - np.prod(1.0 - np.clip(opac[idx], 0, 0.999999))
        worst = max(worst, abs(expected - out["opacities"][gi]))
    print(f"  synthetic: max opacity-reconstruction error {worst:.2e}")
    print(f"  synthetic: shapes means{out['means'].shape} shN{None if out['shN'] is None else out['shN'].shape}")


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ply", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--target", type=float, default=0.4, help="fraction of primitives to keep")
    ap.add_argument("--edge", type=float, default=None, help="voxel edge; overrides --target")
    ap.add_argument("--report", default="/workspace/res/merge_summary.json")
    ap.add_argument("--synthetic-test", action="store_true")
    args = ap.parse_args()

    if args.synthetic_test:
        synthetic_test()
        return

    from calib.plyio import load_inria_ply, save_inria_ply

    d = load_inria_ply(args.ply)
    means = np.asarray(d["means"], np.float32)
    scales = np.asarray(d["scales"], np.float32)
    quats = np.asarray(d["quats"], np.float32)
    opac = np.asarray(d["opacities"], np.float32)
    sh0 = np.asarray(d["sh0"], np.float32)
    shN = np.asarray(d["shN"], np.float32) if d.get("shN") is not None else None

    edge = args.edge if args.edge is not None else choose_edge(means, args.target)
    out = voxel_merge(means, scales, quats, opac, sh0, shN, edge)
    keep = len(out["means"]) / max(len(means), 1)
    print(f"{args.ply}: {len(means)} -> {len(out['means'])} primitives "
          f"({keep:.3f} of the original) at edge {edge:.5f}", flush=True)
    save_inria_ply(args.out, out["means"], out["scales"], out["quats"], out["opacities"],
                   out["sh0"], out["shN"])
    import json
    os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
    json.dump(dict(source=os.path.basename(args.ply), n_before=int(len(means)),
                   n_after=int(len(out["means"])), kept=float(keep), edge=float(edge),
                   target=float(args.target)), open(args.report, "w"), indent=1)
    print("WROTE", args.out)


if __name__ == "__main__":
    main()
