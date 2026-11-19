import sys, tempfile, pathlib
sys.path[:0] = ["D:/3dsg_1/experiments", "D:/3dsg_1"]
import numpy as np
import m19_codec as C
import m22_basis as B
from experiments.tests.test_m33_basis_neutral import _encoded

tmp = pathlib.Path(tempfile.mkdtemp())
p = _encoded(tmp, 32 << 10)
bad = str(tmp / "bad.gs1")
C.damage_file(p, bad, 0.05, seed=2, stream="sh_coef", burst=True)
meta1, s1 = C.read_container(bad, tolerant=True)
raw = s1["sh_coef"]
print("raw len", len(raw), "first 8", list(raw[:8]), "uniq", len(set(raw[:2000])))
ent = [s for s in meta1["streams"] if s["name"] == "sh_coef"][0]
print("raw_frames", ent.get("raw_frames"), "frames", ent["frames"], "crc", ent.get("crc"))
