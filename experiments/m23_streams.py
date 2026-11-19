"""M23 diagnostic: where did the delta transform go wrong, stream by stream.

Reads the two containers of the same model (one with deltas, one without) and prints the stored size of
every geometry stream.  Run it on the node, where the model exists.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m19_codec as C  # noqa: E402

A, B = sys.argv[1], sys.argv[2]
ma, sa = C.read_container(A)
mb, sb = C.read_container(B)


def sizes(meta):
    return {e["name"]: e["raw"] for e in meta["streams"]}


sa, sb = sizes(ma), sizes(mb)
keys = sorted(set(sa) | set(sb), key=lambda k: -(sa.get(k, 0) + sb.get(k, 0)))
n = int(ma["n"])
print(f"{'stream':20s} {'plain MB':>9s} {'delta MB':>9s} {'delta-plain':>12s}  {'B/prim':>7s}")
tot_a = tot_b = 0
for k in keys:
    a, b = sa.get(k, 0), sb.get(k, 0)
    if max(a, b) < 100_000:
        continue
    tot_a += a
    tot_b += b
    print(f"{k:20s} {a/1e6:9.2f} {b/1e6:9.2f} {(b-a)/1e6:+12.2f}  {(b-a)/n:+7.3f}")
print(f"{'TOTAL (listed)':20s} {tot_a/1e6:9.2f} {tot_b/1e6:9.2f} {(tot_b-tot_a)/1e6:+12.2f}  "
      f"{(tot_b-tot_a)/n:+7.3f}")
print(f"file sizes: {os.path.getsize(A)/1e6:.2f} MB -> {os.path.getsize(B)/1e6:.2f} MB")
