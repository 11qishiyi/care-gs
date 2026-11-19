"""M21: cut a rate-scalable container at each layer boundary and decode what is left.

The point of the round is that a *prefix* of a ``.gs1`` file is a usable model.  This script walks
the ladder the format defines -- geometry plus the DC term (a degree-0 model), then one SH plane at
a time -- writes the truncated file, decodes it tolerantly, and exports the PLY the renderer reads,
so the PSNR of each step can be measured on held-out views rather than inferred from a tensor.

    python experiments/m21_ladder.py --file res/m21/models/bicycle_c10_o8_sh3_p.gs1 \
        --out res/m21/ladder --ply-dir res/m21/ply

The byte fraction of every step is reported, because "33 % of the file" and "the third SH plane" are
not the same cut and the paper has to state which one it measured.
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


def steps(path: str) -> list:
    """``[(label, frac, planes)]`` from "geometry only" to the whole file.

    A best-rate file gets one step: cut just before the SH rest block, which leaves every primitive
    with its position, opacity, scale, rotation and DC colour -- a degree-0 model at zero extra
    bytes, because the streams are already ordered for it.  A rate-scalable file gets the plane
    ladder on top of that.
    """
    f = C.layer_fracs(path)
    meta, _ = C.read_container_sizes(path)
    if not meta.get("sh_progressive"):
        rows = C.layer_table(path)
        total = sum(r["comp"] for r in rows)
        start = 0
        for r in rows:
            if r["name"] == "sh_rest":
                return [("dc", start / max(1, total), 0), ("full", 1.0, 3)]
            start += r["comp"]
        raise ValueError(f"{path}: no sh_rest stream")
    out = [("dc", f.get("sh_dc", 0.0), 0)]
    for k, name in enumerate(C.SH_PLANES):          # p2, p1, p0
        out.append((name.split("_")[-1], f[name], k + 1))
    out[-1] = (out[-1][0], 1.0, 3)                  # the last step is the file as shipped
    return out


def run(path: str, out_dir: str, ply_dir: str = None) -> list:
    os.makedirs(out_dir, exist_ok=True)
    if ply_dir:
        os.makedirs(ply_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(path))[0]
    rows = []
    for label, frac, planes in steps(path):
        cut = os.path.join(out_dir, f"{base}_{label}.gs1")
        C.truncate_file(path, cut, frac)
        t0 = time.time()
        meta, streams = C.read_container(cut, tolerant=True)
        dec = C.decode(meta, streams)
        dec_s = time.time() - t0
        t1 = time.time()
        ply = os.path.join(ply_dir, f"{base}_{label}.ply") if ply_dir else None
        if ply:
            C.to_ply(meta, streams, ply)
        ply_s = time.time() - t1
        n = int(dec["means"].shape[0])
        rows.append({"file": path, "step": label, "planes": planes, "frac": frac,
                     "bytes": os.path.getsize(cut),
                     "damaged_bytes": int(meta.get("damaged_bytes", 0)),
                     "n": n, "decode_s": round(dec_s, 3),
                     "decode_ply_s": round(ply_s, 3),
                     "bpp": round(os.path.getsize(cut) / max(1, n), 3),
                     "sh_rest_abs_mean": float(np.abs(dec["sh_rest"]).mean())
                     if dec["sh_rest"].size else 0.0,
                     "sh_rest_abs_max": float(np.abs(dec["sh_rest"]).max())
                     if dec["sh_rest"].size else 0.0,
                     "ply": ply})
        print(f"  {label:4s} planes={planes}  {rows[-1]['bytes']/1e6:8.2f} MB  "
              f"({frac*100:5.1f}% of payload, {rows[-1]['bpp']:.2f} B/prim)  "
              f"lost {rows[-1]['damaged_bytes']/1e6:6.2f} MB  decode {dec_s:5.2f} s", flush=True)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", required=True)
    ap.add_argument("--out", required=True, help="where the truncated .gs1 files go")
    ap.add_argument("--ply-dir", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    print(f"{os.path.basename(a.file)}:")
    rows = run(a.file, a.out, a.ply_dir)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(rows, f, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
