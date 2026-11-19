"""M47 -- how much do the gradient and volume selections actually differ?

    python -m tools.m47_overlap --ply <published.ply> --imp <npy> --keep 0.25

Prints the share of primitives kept by both, the Spearman correlation of the two scores, and the mass of each score
that survives the other's cut. Reads the model only to compute the volume score, so it is cheap.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "experiments"), os.path.join(ROOT, "research", "code")):
    if p not in sys.path:
        sys.path.insert(0, p)


def spearman(a, b):
    """Rank correlation without scipy: rank, centre, cosine."""
    n = len(a)
    ra = np.empty(n, dtype=np.float64)
    rb = np.empty(n, dtype=np.float64)
    ra[np.argsort(a, kind="stable")] = np.arange(n)
    rb[np.argsort(b, kind="stable")] = np.arange(n)
    ra -= ra.mean()
    rb -= rb.mean()
    denom = np.linalg.norm(ra) * np.linalg.norm(rb)
    return float(ra @ rb / denom) if denom > 0 else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ply", required=True, help="the model the saliency was measured on")
    ap.add_argument("--imp", required=True, help=".npy from train_gs.py --importance_out")
    ap.add_argument("--keep", type=float, default=0.25)
    ap.add_argument("--json")
    args = ap.parse_args()

    from calib.plyio import load_inria_ply

    d = load_inria_ply(args.ply)
    n = len(d["means"])
    vol = d["opacities"].astype(np.float64).reshape(-1) * np.cbrt(
        np.clip(d["scales"].astype(np.float64).prod(axis=1), 1e-30, None))
    imp = np.asarray(np.load(args.imp), dtype=np.float64).reshape(-1)
    if imp.size != n:
        raise SystemExit(f"saliency has {imp.size} entries, model has {n}")

    k = max(1, int(round(args.keep * n)))
    a = np.argsort(-imp, kind="stable")[:k]
    b = np.argsort(-vol, kind="stable")[:k]
    both = np.intersect1d(a, b)
    row = {
        "n": int(n), "keep": float(args.keep), "k": int(k),
        "kept_by_both": int(both.size),
        "overlap_frac_of_k": round(float(both.size) / k, 4),
        "spearman": round(spearman(imp, vol), 4),
        "imp_mass_kept_by_volume": round(float(imp[b].sum() / imp.sum()), 4),
        "vol_mass_kept_by_importance": round(float(vol[a].sum() / vol.sum()), 4),
        "imp_top_share_of_imp_mass": round(float(imp[a].sum() / imp.sum()), 4),
    }
    print(json.dumps(row))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(row, fh, indent=1)


if __name__ == "__main__":
    main()
