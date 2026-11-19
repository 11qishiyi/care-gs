import sys

import numpy as np
import torch
import types

sys.path.insert(0, "D:/3dsg_1/experiments")

import m19_codec as C  # noqa: E402
import m24_alpha as A  # noqa: E402
import m29_split as S  # noqa: E402

rng = np.random.default_rng(1)
n = 40000


def T(x):
    return torch.from_numpy(np.ascontiguousarray(x))


q = rng.normal(size=(n, 4))
q /= np.linalg.norm(q, axis=1, keepdims=True)
sp = types.SimpleNamespace(
    means=T((rng.normal(size=(n, 3)) * 0.2).astype(np.float32)),
    scales=T(np.exp((rng.normal(size=(n, 3)) * 0.3 - 1.5).astype(np.float32))),
    quats=T(q.astype(np.float32)),
    opacities=T((1 / (1 + np.exp(-rng.normal(size=n)))).astype(np.float32)),
    sh0=T(rng.normal(size=(n, 3)).astype(np.float32)),
    shN=T((rng.normal(size=(n, 45)) * 0.05).astype(np.float32)),
    sh_degree=3,
)
r = A.build(sp, rank=8, bits_total=32, level=3, log=lambda *a, **k: None)
C.write_container("D:/3dsg_1/experiments/_t29a.gs1", r["streams"], r["meta"], level=3)
m0, s0 = C.read_container("D:/3dsg_1/experiments/_t29a.gs1")
a0 = C.decode(m0, s0)

plan = {"cluster_off": ("pos", 10, 3), "geo_scales": ("pos", 8, 3),
        "geo_quat_abc": ("scale", 8, 3), "geo_quat_which": ("pos", 2, 1),
        "geo_opacities": ("scale", 8, 1)}
res = S.build("D:/3dsg_1/experiments/_t29a.gs1", "D:/3dsg_1/experiments/_t29b.gs1", plan,
              level=3, log=lambda m: None)
m1, s1 = C.read_container("D:/3dsg_1/experiments/_t29b.gs1")
a1 = C.decode(m1, s1)
same = all(np.array_equal(a0[k], a1[k]) for k in a0)
print("identical:", same, "bytes", res["before"], "->", res["after"], f"{res['saved_pct']:+.2f} %")
