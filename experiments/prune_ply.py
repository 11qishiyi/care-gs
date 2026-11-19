"""Prune a 3DGS PLY down to a fraction of its primitives and write an INRIA PLY.

The score is the usual contribution proxy: a gaussian matters in proportion to how much of the
image it can darken or brighten, which scales with its opacity and its volume.  We use
``opacity * (sx * sy * sz) ** (1/3)`` -- the cube root keeps the score comparable to a length, so
a fat faint gaussian and a small bright one can trade places, which a raw volume product does not
allow.

Pruning alone always loses PSNR; the point of this script is to produce the *initialisation* for a
short finetune, which is what makes a 5x smaller model competitive.

    python experiments/prune_ply.py --in <ply> --out <ply> --keep 0.2
    python experiments/prune_ply.py --in <ply> --out <ply> --keep-frac 0.2 --score opacity
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research", "code"))
from calib.plyio import load_inria_ply, save_inria_ply  # noqa: E402


def score_of(d: dict, kind: str, importance=None) -> np.ndarray:
    scales = d["scales"].astype(np.float64)
    opac = d["opacities"].astype(np.float64).reshape(-1)
    if kind == "opacity":
        return opac
    if kind == "volume":
        return opac * np.cbrt(np.clip(scales.prod(axis=1), 1e-30, None))
    if kind == "area":
        return opac * scales.max(axis=1)
    if kind == "importance":
        #: M47: what the training loss was actually pulling on, measured by summing the squared
        #: gradients of means/scales/opacities over a short pass (``train_gs --importance_out``).
        #: It is not a proxy for visibility, it is the measurement the optimiser itself used.
        if importance is None:
            raise SystemExit("--score importance needs --importance <file.npy>")
        return np.asarray(importance, dtype=np.float64).reshape(-1)
    raise SystemExit(f"unknown score {kind}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--keep-frac", type=float, default=0.2)
    ap.add_argument("--score", default="volume", choices=["volume", "opacity", "area", "importance"])
    ap.add_argument("--importance", default="",
                    help="per-primitive saliency .npy from train_gs.py --importance_out (M47)")
    ap.add_argument("--min-opacity", type=float, default=0.0,
                    help="drop primitives below this opacity before scoring")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    d = load_inria_ply(args.src)
    n = len(d["means"])
    keep = np.ones(n, bool)
    if args.min_opacity > 0:
        keep &= d["opacities"].reshape(-1) >= args.min_opacity
    idx_all = np.nonzero(keep)[0]
    imp = np.load(args.importance) if args.importance else None
    if imp is not None and len(np.asarray(imp).reshape(-1)) != n:
        raise SystemExit(f"--importance has {np.asarray(imp).size} entries but the model has {n} primitives")
    s = score_of({k: (v[idx_all] if len(v) == n else v) for k, v in d.items()}, args.score,
                 None if imp is None else np.asarray(imp).reshape(-1)[idx_all])
    k = max(1, int(round(args.keep_frac * len(idx_all))))
    order = np.argsort(-s, kind="stable")[:k]
    rng = np.random.default_rng(args.seed)
    rng.shuffle(order)  # a shuffled file compresses the same but keeps any later passes unbiased
    idx = idx_all[order]
    out = {"means": d["means"][idx], "scales": d["scales"][idx], "quats": d["quats"][idx],
           "opacities": d["opacities"][idx] if d["opacities"].ndim == 2 else d["opacities"][idx],
           "sh0": d["sh0"][idx], "shN": d["shN"][idx]}
    os.makedirs(os.path.dirname(os.path.abspath(args.dst)) or ".", exist_ok=True)
    save_inria_ply(args.dst, out["means"], out["scales"], out["quats"],
                   np.asarray(out["opacities"]).reshape(-1), out["sh0"], out["shN"])
    print(f"kept {k}/{n} ({100.0 * k / n:.1f}%) score={args.score} "
          f"-> {args.dst} {os.path.getsize(args.dst) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
