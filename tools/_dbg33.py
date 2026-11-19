import sys, os
sys.path[:0] = ["D:/3dsg_1/experiments", "D:/3dsg_1"]
import numpy as np, torch
import m19_codec as C
from experiments.tests.test_m33_damage import _toy, _encode

import tempfile, pathlib
tmp = pathlib.Path(tempfile.mkdtemp())
p = _encode(tmp, 1 << 16)
meta0, _ = C.read_container_sizes(p)
print("streams:", [(s["name"], len(s["frames"]), s["raw"]) for s in meta0["streams"]][:6])
bad = str(tmp / "bad.gs1")
info = C.damage_file(p, bad, 0.02, seed=1, stream="sh_rest", burst=True)
print("flip info", {k: info[k] for k in ("stream", "flipped", "span")})
meta1, s1 = C.read_container(bad, tolerant=True)
print("damaged_bytes", meta1["damaged_bytes"])
print("bad frames", [(s["name"], s.get("bad_frames")) for s in meta1["streams"] if s.get("bad_frames")])
