"""Do the three frame sizes decode to the same model, and what do they cost?

    python tools/m34_check.py --dir /workspace/res/m34/bonsai --glob '*_f*k_auto.gs1'

Prints, per container: file size, per-stream frame counts, sha1 of the decoded arrays, decode seconds and
peak RSS (in a child process, so the memory number is the decoder's and not this script's).
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHILD = r"""
import hashlib, json, resource, sys, time
import numpy as np
sys.path.insert(0, %r)
import m19_codec as C
p = sys.argv[1]
t0 = time.time()
meta, streams = C.read_container(p, tolerant=True)
out = C.decode(meta, streams)
dt = time.time() - t0
h = hashlib.sha1()
for k in sorted(out):
    a = np.ascontiguousarray(np.asarray(out[k], dtype=np.float32))
    h.update(k.encode())
    h.update(a.tobytes())
print(json.dumps({"sec": dt, "sha1": h.hexdigest(),
                  "rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
                  "n": int(meta["n"])}))
""" % HERE


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--glob", default="*_f*k_auto.gs1")
    a = ap.parse_args()

    rows = []
    for p in sorted(glob.glob(os.path.join(a.dir, a.glob))):
        import m19_codec as C

        sizes = C.read_container_sizes(p)[0]
        frames = {e["name"]: len(e["frames"]) for e in sizes["streams"]}
        r = subprocess.run([sys.executable, "-c", CHILD, p], capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-400:], file=sys.stderr)
            continue
        info = json.loads(r.stdout.strip().splitlines()[-1])
        rows.append({"file": os.path.basename(p), "bytes": os.path.getsize(p),
                     "frames": frames, "sec": info["sec"], "rss_mb": info["rss_mb"],
                     "sha1": info["sha1"], "n": info["n"]})
        print(f"{os.path.basename(p):48s} {rows[-1]['bytes']/1e6:7.2f} MB  dec {info['sec']:5.2f}s  "
              f"rss {info['rss_mb']/1024:5.2f} GB  sh_coef frames {frames.get('sh_coef')}  "
              f"sha {info['sha1'][:12]}")
    same = len({r["sha1"] for r in rows}) == 1
    print(f"\nall decodes identical: {same}")
    if rows:
        base = rows[0]
        for r in rows[1:]:
            print(f"  {r['file']}: bytes {100*(r['bytes']-base['bytes'])/base['bytes']:+.2f}%  "
                  f"decode {r['sec']/base['sec']:.2f}x  rss {r['rss_mb']/base['rss_mb']:.2f}x")
    print(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
