import sys

import numpy as np

sys.path.insert(0, "experiments")
import m4_bytes as M  # noqa: E402
import m19_codec as C  # noqa: E402
import qfp_rd as Q     # noqa: E402

rng = np.random.default_rng(0)
n = 2048
geo = {"means": rng.normal(0, 5, (n, 3)), "scales": rng.normal(-5, .5, (n, 3)),
       "quats": rng.normal(0, 1, (n, 4)), "opacities": rng.normal(2, 1, (n, 1))}
sh = {"dc": rng.normal(0, 1, (n, 3)), "rest": rng.normal(0, .2, (n, 45))}
for name in ("c10_o8_sh3", "m16_o8_sh4", "c8_o8_sh2", "sh16_g16"):
    spec = Q.parse_spec(name)
    st, pp = M._encode(spec, geo, sh, 3, None, None, sh_layout="bytes")
    st["geo_hdr"] = M.geo_header_bytes(geo, spec)
    meta = {"spec": name, "n": n, "sh_degree": 3, "sh_layout": "bytes", "deg_out": 3,
            "model_bytes_per_prim": pp}
    out = C.decode(meta, st)
    ordr = M.morton_order(geo["means"])
    dm = min(float(np.abs(out["means"] - geo["means"][ordr]).max()),
             float(np.abs(out["means"] - geo["means"]).max()))
    print(f"{name:14s} means max|err| {dm:.5f}  hdr {len(st['geo_hdr'])} B")
