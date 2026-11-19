"""M20 measurement: the same model, three SH layouts, the shipped container each time.

Everything except the SH byte layout is identical -- same quantiser, same codes, same Morton
order, same zstd level -- so the differences are the layout's.  Fidelity is checked by decoding
and comparing the codes bit for bit against the ``bits`` layout: a lossless re-layout that changes
a single code is a bug, not a trade-off.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m19_codec as C  # noqa: E402
import m4_bytes as M   # noqa: E402
import qfp_rd as Q     # noqa: E402


def _codes(meta: dict, streams: dict) -> np.ndarray:
    out = C.decode(meta, streams)
    dc = out["sh_dc"]
    rest = out["sh_rest"].reshape(dc.shape[0], -1) if out["sh_rest"].size \
        else np.zeros((dc.shape[0], 0))
    return np.concatenate([dc, rest], axis=1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="/workspace/data/m20")
    ap.add_argument("--scenes", default="bicycle")
    ap.add_argument("--specs", default="c10_o8_sh3,c8_o8_sh3")
    ap.add_argument("--layouts", default="bits,bytes,bytes_coef")
    ap.add_argument("--level", type=int, default=12)
    ap.add_argument("--out", default="/workspace/res/m20")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    from m20_model import load_model

    rows = []
    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        t0 = time.time()
        sp = load_model(os.path.join(args.models, f"{scene}.ply"))
        n = int(sp.means.shape[0])
        print(f"[{scene}] {n:,} primitives in {time.time() - t0:.1f} s", flush=True)
        ref_codes = {}
        for spec in [s.strip() for s in args.specs.split(",") if s.strip()]:
            for layout in [s.strip() for s in args.layouts.split(",") if s.strip()]:
                path = os.path.join(args.out, f"{scene}_{spec}_{layout}.gs1")
                t0 = time.time()
                rec = C.encode_model(sp, spec, level=args.level, path=path, sh_layout=layout)
                enc = time.time() - t0
                size = os.path.getsize(path)
                t0 = time.time()
                meta, streams = C.read_container(path)
                codes = _codes(meta, streams)
                dec = time.time() - t0
                same = True
                if spec not in ref_codes:
                    ref_codes[spec] = codes
                else:
                    same = bool(np.array_equal(codes, ref_codes[spec]))
                row = {"scene": scene, "spec": spec, "layout": layout, "n": n,
                       "file": int(size), "bytes_per_prim": size / n, "ratio": 236.0 / (size / n),
                       "encode_s": round(enc, 1), "decode_s": round(dec, 2),
                       "codes_identical_to_bits": same,
                       "peak_rss_mb": round(resource.getrusage(
                           resource.RUSAGE_SELF).ru_maxrss / 1024.0, 0)}
                rows.append(row)
                print(f"  {spec:14s} {layout:11s} {size / 1e6:8.2f} MB "
                      f"{size / n:6.2f} B/prim {236.0 / (size / n):6.2f}x  "
                      f"enc {enc:5.1f} s dec {dec:5.2f} s  codes=={same}", flush=True)
                if not same:
                    print("  !! the layout changed the decoded codes", flush=True)
        del ref_codes
    with open(os.path.join(args.out, "measure.json"), "w") as f:
        json.dump({"level": args.level, "rows": rows}, f, indent=1)
    print("\nwrote", os.path.join(args.out, "measure.json"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
