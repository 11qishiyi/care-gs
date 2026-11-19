"""Decode timing and peak memory for the M24 containers (runs on the node)."""
import glob
import os
import resource
import sys
import time

sys.path.insert(0, "/workspace/code/experiments")
import m19_codec as C  # noqa: E402

for p in sorted(glob.glob("/workspace/res/m24/*_auto.gs1")):
    t = time.time()
    meta, st = C.read_container(p)
    dec = C.decode(meta, st)
    dt = time.time() - t
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
    print(f"{os.path.basename(p):52s} {os.path.getsize(p)/1e6:7.2f} MB  "
          f"decode {dt:5.2f} s  peakRSS {rss:5.2f} GB  n={int(meta['n']):,}")
    del dec, st
