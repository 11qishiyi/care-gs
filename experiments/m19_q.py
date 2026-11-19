"""M19: where does the decoded model lose its colour -- in the container, or in the PLY?

Reads a .gs1, decodes it, prints quantiles of the colour, then reads the PLY that was written from
the same decode and prints the same quantiles.  One process, three answers: stream, tensors, file.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m19_codec as C

QS = (0.0, 0.01, 0.5, 0.99, 1.0)


def q(a):
    return np.array2string(np.quantile(np.asarray(a, dtype=np.float64).reshape(-1), QS), precision=4)


gs1, ply, ref = sys.argv[1], sys.argv[2], sys.argv[3]
meta, streams = C.read_container(gs1)
out = C.decode(meta, streams)
print("streams:", {k: len(v) for k, v in sorted(streams.items())})
print("damaged:", meta.get("damaged_bytes"), "n:", meta["n"], "spec:", meta["spec"])
print("decoded  sh_dc", q(out["sh_dc"]))
print("decoded  sh_rest", q(out["sh_rest"]))
print("decoded  means", q(out["means"]))
print("decoded  scales", q(out["scales"]))
import calib.gsrender as GR

s = GR.load_splats(ply, device="cpu")
print("PLY      sh0", q(s.sh0.detach().cpu().numpy()))
print("PLY      shN", q(s.shN.detach().cpu().numpy()))
print("PLY      means", q(s.means.detach().cpu().numpy()))
r = GR.load_splats(ref, device="cpu")
print("REF      sh0", q(r.sh0.detach().cpu().numpy()))
print("REF      shN", q(r.shN.detach().cpu().numpy()))
