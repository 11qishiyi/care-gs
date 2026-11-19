import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments"))
import m4_bytes as M
import qfp_rd as Q

rng = np.random.default_rng(0)
n = 2048
geo = {"means": rng.normal(0, 5, (n, 3)).astype(np.float64),
       "scales": rng.normal(-5, 0.5, (n, 3)).astype(np.float64),
       "quats": rng.normal(0, 1, (n, 4)).astype(np.float32),
       "opacities": rng.normal(2, 1, (n, 1)).astype(np.float32)}
sh = {"dc": rng.normal(0, 1, (n, 3)).astype(np.float64),
      "rest": rng.normal(0, 0.2, (n, 45)).astype(np.float64)}
for name in ["clean", "gp8-5-4_c6", "c10_o8_sh3", "sh16_g16", "c8_o8_sh2", "vq12_c8_o8"]:
    spec = Q.parse_spec(name)
    streams, per_prim = M._encode(spec, geo, sh, deg=3, keep_idx=None, perm=None)
    gh = len(streams.get("geo_hdr", b""))
    sh_h = len(streams.get("sh_hdr", b""))
    bpp = spec.bytes_per_prim(3, n_stored=n)
    print(f"{name:16s} geo_hdr {gh:3d}  sh_hdr {sh_h:2d}  bpp {bpp:9.5f}  bpp*n {bpp*n:10.2f}  "
          f"model(per_prim*n) {per_prim*n:10.2f}  streams {sum(map(len, streams.values()))}")
