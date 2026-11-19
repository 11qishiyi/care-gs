"""Local probe: does the SH ladder round-trip on a synthetic model?  (M19 debug helper.)"""
import sys, os
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m19_codec as C


class S:
    pass


rng = np.random.default_rng(0)
n = 500
s = S()
s.sh_degree = 3
s.means = torch.tensor(rng.normal(0, 1.0, (n, 3)), dtype=torch.float32)
s.scales = torch.tensor(np.exp(rng.normal(-2.0, 0.4, (n, 3))), dtype=torch.float32)
q = rng.normal(size=(n, 4)); q /= np.linalg.norm(q, axis=1, keepdims=True)
s.quats = torch.tensor(q, dtype=torch.float32)
s.opacities = torch.tensor(rng.uniform(0.02, 0.98, (n,)), dtype=torch.float32)
s.sh0 = torch.tensor(rng.normal(0, 0.5, (n, 3)), dtype=torch.float32)
s.shN = torch.tensor(rng.normal(0, 0.1, (n, 15, 3)), dtype=torch.float32)

for spec in ("c10_o8_sh3", "vq12_c8_o8"):
    res = C.verify_roundtrip(s, spec)
    print(spec, {k: (round(v["max"], 5), round(v["mean"], 6)) for k, v in res.items()})
