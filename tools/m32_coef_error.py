"""M32 -- the offline criterion: does a plan's *coefficient* error rank it the way the render does?

J4 of the M32 spec asks whether the rank/bit budget can be chosen without rendering anything.  This
script is the only place that question is answered, and it answers it the same way for every scene: fit
the shared basis at each plan's rank, quantise with the same allocator the encoder uses, and report the
relative RMS error of the reconstructed 45 coefficients.

    python tools/m32_coef_error.py --ply <ply> --plans 16:48,24:48,32:48,8:48,16:64 --json out.json

Runs on CPU (torch svd_lowrank with a fixed seed, so the numbers are reproducible).  A scene's fit costs
about one encode's SVD, i.e. 30-60 s on six million primitives.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(HERE, "experiments"), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import m20_model  # noqa: E402
import m22_basis as B  # noqa: E402
import m4_bytes as M  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ply", required=True)
    ap.add_argument("--plans", default="16:48,24:48,32:48,8:48,16:64")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    plans = []
    for item in a.plans.split(","):
        rank, bits = item.split(":")
        plans.append((int(rank), int(bits)))

    mod = m20_model.load_model(a.ply)
    #: the same flattening the encoder uses, so the coefficient error is the error of the shipped block
    _geo, sh = M._attribute_arrays(mod)
    rest = B.rest_matrix(sh)
    fits = {}
    rows = []
    for rank, bits in plans:
        if rank not in fits:
            fits[rank] = B.fit(rest, rank)
            print(f"[fit] rank {rank}: subspace energy kept {float(fits[rank]['energy']):.4f}",
                  flush=True)
        f = fits[rank]
        q = B.quantise_alloc(f["coef"], f["comp"], bits)
        rec = np.asarray(q["rec"], dtype=np.float64)
        true = np.asarray(f["coef"], dtype=np.float64)
        rel = float(np.sqrt(((rec - true) ** 2).sum()) / max(np.sqrt((true ** 2).sum()), 1e-20))
        #: the metric that matters: error against the *original* 45 columns, so throwing the subspace
        #: away is charged.  ``rel`` above only sees the quantiser inside the retained subspace, which is
        #: why it ranks ``r8`` first and the render ranks it fourth.
        basis = np.asarray(f["basis"], dtype=np.float64)          # (rank, 45)
        mean = np.asarray(f["mean"], dtype=np.float64)            # (1, 45)
        xc = np.asarray(rest, dtype=np.float64) - mean
        num = den = 0.0
        step = 1_000_000
        for i in range(0, xc.shape[0], step):
            block = xc[i:i + step]
            approx = rec[i:i + step] @ basis
            num += float(((approx - block) ** 2).sum())
            den += float((block ** 2).sum())
        rel_full = float(np.sqrt(num) / max(np.sqrt(den), 1e-20))
        row = {"plan": f"r{rank}_b{bits}", "rank": rank, "bits": bits,
               "colour_bytes": 1.0 + bits / 8.0,   # ``bits`` is the total budget per primitive
               "bits_used": int(q["bits_total"]), "rel_rmse": rel, "rel_rmse_full": rel_full,
               "mean_abs": float(np.abs(rec - true).mean())}
        rows.append(row)
        print(f"  {row['plan']:10s} colour {row['colour_bytes']:5.2f} B/prim  "
              f"bits {row['bits_used']:3d}  rel_rmse {rel*100:6.2f} %  "
              f"full {rel_full*100:6.2f} %", flush=True)

    if a.json:
        json.dump(rows, open(a.json, "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
