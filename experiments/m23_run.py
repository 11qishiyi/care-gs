"""M23 driver: build the four variants of one model and price them apart.

Nothing here decides anything -- it writes containers, checks that the lossless variant really is
lossless (decoded tensors compared, not assumed), and exports a PLY per variant so the render stage can
report PSNR.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m19_codec as C  # noqa: E402
import m22_basis as B  # noqa: E402
import m23_pred as P  # noqa: E402

#: name -> (spec, geometry recoding mode, or None for the plain codec)
VARIANTS = {
    "A_base": ("c10_o8_sh3", None),
    "B_delta": ("c10_o8_sh3", "delta"),
    "C_st3": ("gp8-8-8_c10_sh3", None),
    "D_both": ("gp8-8-8_c10_sh3", "delta"),
    "E_block": ("c10_o8_sh3", "block"),
    "F_st3blk": ("gp8-8-8_c10_sh3", "block"),
}
#: what each variant isolates, for the report
PURPOSE = {
    "A_base": "the M22 point, reproduced",
    "B_delta": "A + modular deltas on scales/opacity (lossless)",
    "C_st3": "A + smallest-three quaternions (M15 measured this as free)",
    "D_both": "B + C",
    "E_block": "A + block-mean residuals on scales/opacity (lossless)",
    "F_st3blk": "C + E",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ply", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--bits", type=int, default=48)
    ap.add_argument("--level", type=int, default=12)
    ap.add_argument("--json")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    import m20_model
    mod = m20_model.load_model(a.ply)
    n = int(np.asarray(mod.shN).shape[0])
    rows, decoded = [], {}
    for name, (spec, delta) in VARIANTS.items():
        path = os.path.join(a.out, f"{name}.gs1")
        t0 = time.time()
        rec = B.encode_basis(mod, rank=a.rank, bits_total=a.bits, level=a.level, path=path,
                             spec_name=spec, geo_delta=delta)
        enc_s = time.time() - t0
        t1 = time.time()
        meta, streams = C.read_container(path)
        dec = C.decode(meta, streams)
        dec_s = time.time() - t1
        ply = os.path.join(a.out, f"{name}.ply")
        C.to_ply(meta, streams, ply)
        decoded[name] = {k: np.asarray(dec[k]) for k in ("means", "scales", "quats", "opacities")}
        size = os.path.getsize(path)
        row = {"variant": name, "spec": spec, "geo_delta": delta, "bytes": size, "n": n,
               "bytes_per_prim": size / n, "encode_s": round(enc_s, 1), "decode_s": round(dec_s, 2),
               "file": path, "ply": ply}
        if delta:
            row["delta_flags"] = meta.get("geo_delta")
        rows.append(row)
        print(f"  {name:7s} {size/1e6:7.2f} MB  {size/n:5.2f} B/prim  enc {enc_s:5.1f} s  "
              f"dec {dec_s:5.2f} s", flush=True)

    #: the lossless claim, checked: B must equal A and D must equal C, tensor by tensor
    checks = {}
    for lhs, rhs in (("B_delta", "A_base"), ("D_both", "C_st3"), ("E_block", "A_base"),
                     ("F_st3blk", "C_st3")):
        checks[f"{lhs}=={rhs}"] = {k: bool(np.array_equal(decoded[lhs][k], decoded[rhs][k]))
                                   for k in decoded[lhs]}
        print(f"  bit-exact {lhs} vs {rhs}: {checks[f'{lhs}=={rhs}']}", flush=True)
    for r in rows:
        r["bit_exact"] = checks.get(f"{r['variant']}==A_base") or checks.get(
            f"{r['variant']}==C_st3")
    if a.json:
        json.dump({"rows": rows, "checks": checks}, open(a.json, "w"), indent=1)
        print("WROTE", a.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
