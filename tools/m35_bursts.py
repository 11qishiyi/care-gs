"""How big is a burst really? Repeat the same fraction at several offsets and count what is lost.

M34 measured the *frame size* as the robustness knob by burning one 4 MB frame.  M35's 1.0 % burst on
the same container lost 114 MB across **every** stream, which is a different failure mode: the burst
landed on a frame length word, the tolerant reader then walked the file at the wrong offsets, and the
rest of the container was unrecoverable.  Whether that happens is a property of *where* the burst
lands, so it has to be measured over several offsets rather than at the one seed the round happened
to use.

    python tools/m35_bursts.py --glob '/workspace/res/m35/bicycle_f*/*_auto.gs1' --seeds 0,1,2,3,4
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import m19_codec as C  # noqa: E402


def one(path: str, frac: float, seed: int, tmpdir: str) -> dict:
    dst = os.path.join(tmpdir, f"burst_{int(frac*10000):04d}_{seed}.gs1")
    C.damage_file(path, dst, frac, seed=seed, burst=True)
    meta, stream_map = C.read_container(dst, tolerant=True)
    lost = int(meta.get("damaged_bytes", 0))
    hit = [s["name"] for s in meta["streams"] if s.get("bad_frames")]
    try:
        C.decode(meta, stream_map)
        ok, note = True, ""
    except Exception as exc:  # noqa: BLE001 - a container that cannot decode is a result
        ok, note = False, f"{type(exc).__name__}: {exc}"[:120]
    os.unlink(dst)
    return dict(frac=frac, seed=seed, lost_bytes=lost, streams=hit, decoded=ok, note=note)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True)
    ap.add_argument("--seeds", default="0,1,2,3,4")
    ap.add_argument("--fracs", default="0.001,0.01")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(",") if s.strip()]
    fracs = [float(s) for s in a.fracs.split(",") if s.strip()]
    rows = []
    for path in sorted(glob.glob(a.glob)):
        size = os.path.getsize(path)
        tmpdir = os.path.dirname(path)
        for frac in fracs:
            for seed in seeds:
                r = one(path, frac, seed, tmpdir)
                r.update(path=os.path.basename(path), file_bytes=size)
                rows.append(r)
                print(f"{os.path.basename(path)[:34]:34s} frac={frac:<6} seed={seed} "
                      f"lost={r['lost_bytes']/1e6:7.2f} MB streams={len(r['streams']):2d} "
                      f"decoded={r['decoded']}", flush=True)
    if a.out:
        json.dump(rows, open(a.out, "w"), indent=1)
        print("wrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
