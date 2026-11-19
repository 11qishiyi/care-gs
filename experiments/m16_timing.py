"""M16: what an encode costs -- wall time and peak RSS per (scene, spec), on the shipped path.

The papers report encode/decode time only sporadically (PCGS: 13.0 s encode / 20.5 s decode
on a V100-class card; MesonGS: 4 s - 1 min; ContextGS: ~20 s), and never for a post-hoc
coder, because their encoders retrain.  Ours is a pure CPU pass over an existing PLY, so the
number that matters is "how many minutes per asset, with no gradient step", measured on the
same box that produced the byte measurements.

What this measures
------------------
``encode_s``     load PLY -> streams -> zstd-12, i.e. ``m4_bytes.measure_scene`` for one spec.
``load_s``       the PLY read alone, so the codec cost can be separated from I/O.
``peak_rss_mb``  ``ru_maxrss`` after the encode, which is an upper bound (it is the process
                 high-water mark, not a delta).

What it does not measure
------------------------
Decode time.  There is no decoder in this repo yet -- ``m4_bytes`` builds a bitstream and
prices it, and only the small self-tests ever read one back.  Writing a decoder is a
prerequisite for the deployment claim, and this script reports ``decode_s: null`` rather than
a number that does not exist.

Usage::

    python experiments/m16_timing.py --archive /workspace/data/m360std \
        --scenes bicycle,room --specs c10_o8_sh3,vq12_c8_o8 --out m16_timing.json
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m4_bytes as M4  # noqa: E402


def peak_mb() -> float:
    """Process high-water RSS in MiB (Linux: KiB, macOS: bytes)."""
    v = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return v / 1024.0 if sys.platform != "darwin" else v / (1024.0 * 1024.0)


def one_scene(archive: str, scene: str, specs: list, level: int, pattern: str) -> dict:
    C = M4._C()
    C.add_code_root()
    from calib.gsrender import load_splats

    path = pattern.format(archive=archive, scene=scene)
    t0 = time.time()
    sp = load_splats(path, device="cpu")
    load_s = time.time() - t0
    rows = []
    for spec in specs:
        t1 = time.time()
        res = M4.measure_scene(sp, [spec], level, log=None, skip_flat=True)
        dt = time.time() - t1
        row = res["rows"][0]
        n = res["n"]
        stored = row["stored"]
        bpp = row["zstd_morton_bytes_per_prim"]
        rows.append({
            "spec": spec,
            "n": int(n),
            "stored": int(stored),
            "bytes_per_stored_prim": bpp,
            "size_mb": bpp * stored / 1e6,
            "encode_s": dt,
            "encode_s_per_mprim": dt / max(n / 1e6, 1e-9),
            "load_s": load_s,
            "peak_rss_mb": peak_mb(),
            "decode_s": None,
        })
        print(f"  {scene:10s} {spec:16s} {bpp:7.2f} B/prim  {dt:7.1f} s  "
              f"peak {rows[-1]['peak_rss_mb']:.0f} MiB", flush=True)
    return {"scene": scene, "ply": path, "n": int(res["n"]) if rows else 0, "rows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/workspace/data/m360std")
    ap.add_argument("--scenes", default="bicycle,room")
    ap.add_argument("--specs", default="c10_o8_sh3,vq12_c8_o8,p30_vq12_c8_o8")
    ap.add_argument("--level", type=int, default=12)
    ap.add_argument("--ply-pattern",
                    default="{archive}/output/{scene}/point_cloud/iteration_30000/point_cloud.ply")
    ap.add_argument("--out", default="/workspace/res/m16/m16_timing.json")
    args = ap.parse_args(argv)

    out = {"level": int(args.level), "backend": M4.ZSTD_BACKEND, "scenes": [],
           "note": "decode_s is null: no decoder exists yet (see the module docstring)"}
    for sc in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        out["scenes"].append(one_scene(args.archive, sc, [s.strip() for s in args.specs.split(",") if s.strip()],
                                      args.level, args.ply_pattern))
        # the high-water mark is sticky, so each scene is only comparable within itself
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(out, open(args.out, "w", encoding="utf-8"), indent=1)
    print(f"WROTE {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
