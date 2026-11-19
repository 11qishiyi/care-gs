import os
import sys

import numpy as np

HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments")
sys.path.insert(0, HERE)
import m19_codec as C  # noqa: E402
import qfp_rd as Q     # noqa: E402

rng = np.random.default_rng(0)
n = 3000
geo = {"means": rng.normal(0, 5, (n, 3)), "scales": rng.normal(-5, .5, (n, 3)),
       "quats": rng.normal(0, 1, (n, 4)), "opacities": rng.normal(2, 1, (n, 1))}
sh = {"dc": rng.normal(0, 1, (n, 3)), "rest": rng.normal(0, .2, (n, 45))}
spec = Q.parse_spec("c10_o8_sh3")
ref = None
for layout in ("bits", "bytes", "bytes_coef"):
    streams, bpp = C.M._encode(spec, geo, sh, 3, None, None, sh_layout=layout)
    streams["geo_hdr"] = C.geo_header(geo, spec)
    meta = {"spec": "c10_o8_sh3", "n": n, "sh_degree": 3, "sh_layout": layout,
            "deg_out": 3, "model_bytes_per_prim": bpp}
    out = C.decode(meta, streams)
    dc = out["sh_dc"]
    rest = out["sh_rest"].reshape(n, -1) if out["sh_rest"].size else np.zeros((n, 0))
    codes = np.concatenate([dc, rest], axis=1)
    if ref is None:
        ref = codes
    print(f"{layout:11s} decoded codes match: {np.array_equal(codes, ref)}  "
          f"max|diff| {np.abs(codes - ref).max():.3e}  "
          f"payload sh_rest {len(streams['sh_rest'])} B")
