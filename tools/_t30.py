import sys

import numpy as np
import torch
import types

sys.path.insert(0, "D:/3dsg_1/experiments")

import m19_codec as C  # noqa: E402
import m24_alpha as A  # noqa: E402
import m30_adapt as Ad  # noqa: E402

rng = np.random.default_rng(3)
n = 60000


def T(x):
    return torch.from_numpy(np.ascontiguousarray(x))


#: dense in the middle, sparse at the edges -- so the cluster boxes really do differ in size
base = rng.normal(size=(n, 3)) * np.array([0.4, 0.4, 0.1])
base[n // 2:] *= 0.05
q = rng.normal(size=(n, 4))
q /= np.linalg.norm(q, axis=1, keepdims=True)
sp = types.SimpleNamespace(
    means=T(base.astype(np.float32)),
    scales=T(np.exp((rng.normal(size=(n, 3)) * 0.3 - 1.5).astype(np.float32))),
    quats=T(q.astype(np.float32)),
    opacities=T((1 / (1 + np.exp(-rng.normal(size=n)))).astype(np.float32)),
    sh0=T(rng.normal(size=(n, 3)).astype(np.float32)),
    shN=T((rng.normal(size=(n, 45)) * 0.05).astype(np.float32)),
    sh_degree=3,
)
r = A.build(sp, rank=8, bits_total=32, level=3, spec_name="gp6-6-6_c8_sh3",
            log=lambda *a, **k: None)
C.write_container("D:/3dsg_1/experiments/_t30a.gs1", r["streams"], r["meta"], level=3)
m0, s0 = C.read_container("D:/3dsg_1/experiments/_t30a.gs1")
p0 = C.decode(m0, s0)

row = Ad.adapt("D:/3dsg_1/experiments/_t30a.gs1", "D:/3dsg_1/experiments/_t30b.gs1",
               nominal=8, level=3, log=print)
m1, s1 = C.read_container("D:/3dsg_1/experiments/_t30b.gs1")
p1 = C.decode(m1, s1)
d = np.abs(p0["means"] - p1["means"])
print("max |dmean|", d.max(axis=0), "mean", d.mean())
print("shape ok", p1["means"].shape, "finite", np.isfinite(p1["means"]).all())
print("file", row["before"], "->", row["after"])
