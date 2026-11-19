"""Diagnose a decoded PLY against the model it came from, attribute by attribute.

Written for M19: the decoded renders came out 4-7 dB below what the encoder promised, and the only
way to find out which attribute broke is to compare tensors rather than images.  Positions are
matched by lexicographic sort (the encoder stores them in Morton order, so the arrays are
permutations of each other); colour is compared after the same sort.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def load(path: str) -> dict:
    import calib.gsrender as GR

    s = GR.load_splats(path, device="cpu")
    return {"means": np.asarray(s.means.detach().cpu().numpy(), dtype=np.float64),
            "scales": np.asarray(s.scales.detach().cpu().numpy(), dtype=np.float64),
            "quats": np.asarray(s.quats.detach().cpu().numpy(), dtype=np.float64),
            "opacities": np.asarray(s.opacities.detach().cpu().numpy(), dtype=np.float64).reshape(-1),
            "sh0": np.asarray(s.sh0.detach().cpu().numpy(), dtype=np.float64),
            "shN": np.asarray(s.shN.detach().cpu().numpy(), dtype=np.float64)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--dec", required=True)
    ap.add_argument("--n", type=int, default=200000, help="rows to compare (subsampled)")
    a = ap.parse_args()
    ref, dec = load(a.ref), load(a.dec)
    if ref["means"].shape != dec["means"].shape:
        print(f"SHAPE MISMATCH ref {ref['means'].shape} dec {dec['means'].shape}")
        return 1
    #: Match by lexicographic order of positions: both arrays hold the same set of points.
    oref = np.lexsort((ref["means"][:, 2], ref["means"][:, 1], ref["means"][:, 0]))
    odec = np.lexsort((dec["means"][:, 2], dec["means"][:, 1], dec["means"][:, 0]))
    sel = np.arange(0, oref.size, max(1, oref.size // a.n))
    for key in ("means", "scales", "opacities", "sh0"):
        r = ref[key][oref][sel]
        d = dec[key][odec][sel]
        err = np.abs(r - d)
        print(f"{key:10s} max {err.max():9.4g}  mean {err.mean():9.4g}  "
              f"ref|max| {np.abs(r).max():9.4g}")
    #: quaternions are sign-ambiguous: q and -q are the same rotation
    r = ref["quats"][oref][sel]
    d = dec["quats"][odec][sel]
    err = np.minimum(np.abs(r - d), np.abs(r + d)).max(axis=1)
    print(f"{'quats':10s} max {err.max():9.4g}  mean {err.mean():9.4g}  (sign-insensitive)")
    #: SH: per-coefficient error, which is what a renderer multiplies by the view basis
    r = ref["shN"].reshape(oref.size, -1)[oref][sel]
    d = dec["shN"].reshape(odec.size, -1)[odec][sel]
    err = np.abs(r - d)
    print(f"{'shN':10s} max {err.max():9.4g}  mean {err.mean():9.4g}  ref|max| {np.abs(r).max():9.4g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
