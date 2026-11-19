#!/usr/bin/env python3
"""M51 -- decode one container and report wall clock + peak RSS of the child process.

    python3 tools/m51_decode.py <file.gs1>
"""
import os
import resource
import subprocess
import sys
import time

gs1 = sys.argv[1]
out = "/tmp/m51_decode.ply"
env = dict(os.environ)
env.setdefault("PYTHONPATH", "/workspace/code/research/code:/workspace/code:/workspace/code/experiments")

start = time.time()
proc = subprocess.run([sys.executable, "experiments/m19_codec.py", "--to-ply", gs1, "--out", out],
                      cwd="/workspace/code", env=env, capture_output=True, text=True)
wall = time.time() - start
peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss  # kB on Linux
size = os.path.getsize(out) if os.path.exists(out) else 0
if os.path.exists(out):
    os.remove(out)
print(f"returncode {proc.returncode} wall_s {wall:.2f} peak_rss_kb {peak} decoded_bytes {size}")
if proc.returncode != 0:
    print(proc.stderr[-800:])
