import sys, tempfile, pathlib
sys.path[:0] = ["D:/3dsg_1/experiments", "D:/3dsg_1"]
import numpy as np
import m19_codec as C
import m22_basis as B
from experiments.tests.test_m33_basis_neutral import _encoded

tmp = pathlib.Path(tempfile.mkdtemp())
p = _encoded(tmp, 32 << 10)
meta0, s0 = C.read_container(p)
print("frames per stream:", [(s["name"], len(s["frames"])) for s in meta0["streams"] if s["name"].startswith("sh_")])
print("coef bits:", list(np.frombuffer(s0["sh_coef_bits"], dtype=np.uint8)))
ref = C.decode(meta0, s0)
bad = str(tmp / "bad.gs1")
C.damage_file(p, bad, 0.05, seed=2, stream="sh_coef", burst=True)
meta1, s1 = C.read_container(bad, tolerant=True)
ent = [s for s in meta1["streams"] if s["name"] == "sh_coef"][0]
print("lost ranges", ent["lost_ranges"], "raw", ent["raw"], "frames", ent["frames"])
bits = list(np.frombuffer(s1["sh_coef_bits"], dtype=np.uint8))
codes = B.unpack_codes(s1["sh_coef"], bits, 3000, "bits")
filled = B.neutralise_coef(codes, bits, meta1, 3000, "bits")
for k, (a, b) in enumerate(zip(codes, filled)):
    d = int((a != b).sum())
    print(f"comp {k} bits {bits[k]} changed codes {d}  sample {a[:6]} -> {b[:6]}")
