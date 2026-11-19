"""M25: decode wall time and peak RSS for the shelf container, measured in a fresh process.

The measurement has to be in a fresh process: ``ru_maxrss`` is a high-water mark for the whole process,
so timing a decode after an encode would report the encoder's peak.  It also has to keep the decoded
tensors alive until after the reading, otherwise the number describes a decoder that threw its answer
away.
"""

from __future__ import annotations

import argparse
import gc
import glob
import os
import resource
import subprocess
import sys
import time

CHILD = r'''
import glob, os, resource, sys, time
sys.path.insert(0, "/workspace/code/experiments")
import m19_codec as C
p = sys.argv[1]
t0 = time.time()
meta, streams = C.read_container(p)
dec = C.decode(meta, streams)
dt = time.time() - t0
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
n = int(meta["n"])
total = sum(v.nbytes for v in dec.values())
print(f"{os.path.basename(p)}|{os.path.getsize(p)}|{dt:.3f}|{rss:.3f}|{total}|{n}")
'''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="/workspace/res/m25")
    ap.add_argument("--glob", default="*_auto.gs1")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.dir, a.glob)))
    if not files:
        print(f"no containers in {a.dir}")
        return 2
    for p in files:
        out = subprocess.run([sys.executable, "-c", CHILD, p], capture_output=True, text=True)
        if out.returncode != 0:
            print(out.stderr[-400:])
            continue
        name, size, dt, rss, total, n = out.stdout.strip().split("|")
        print(f"{name:44s} file {float(size)/1e6:7.2f} MB  decode {float(dt):6.2f} s  "
              f"peak RSS {float(rss):5.2f} GB  tensors {float(total)/1e6:6.2f} MB  n={int(n):,}",
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
