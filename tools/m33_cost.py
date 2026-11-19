"""Decode cost of a *damaged* file: does the tolerant path cost more than the intact one?

    python tools/m33_cost.py --dir /workspace/res/m33/bicycle/dmg

Same contract as ``m25_time.py`` (one subprocess per file, ``ru_maxrss`` from that process, so the
number is the decode's peak and not the parent's), but it reads with ``tolerant=True`` and prints
the file's lost bytes next to the time and the peak.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHILD = r"""
import json, resource, sys, time
sys.path[:0] = ["%s/experiments", "%s"]
import m19_codec as C
p = sys.argv[1]
t0 = time.time()
meta, streams = C.read_container(p, tolerant=True)
model = C.decode(meta, streams)
dt = time.time() - t0
print(json.dumps({"file": p, "decode_s": dt, "peak_gb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6,
                  "lost_mb": meta.get("damaged_bytes", 0) / 1e6, "n": int(meta["n"])}))
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--glob", default="*.gs1")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    rows = []
    for p in sorted(glob.glob(os.path.join(a.dir, a.glob))):
        src = CHILD % (HERE, HERE)
        r = subprocess.run([sys.executable, "-c", src, p], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"{os.path.basename(p):34s} FAILED {r.stderr.strip().splitlines()[-1][:90]}")
            continue
        d = json.loads(r.stdout.strip().splitlines()[-1])
        rows.append(d)
        print(f"{os.path.basename(p):34s} decode {d['decode_s']:5.2f} s  peak {d['peak_gb']:5.2f} GB  "
              f"lost {d['lost_mb']:6.2f} MB", flush=True)
    if a.json:
        json.dump(rows, open(a.json, "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
