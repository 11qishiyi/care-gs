"""M19 local probe: does a multi-frame container round-trip the streams byte for byte?

The toy selftest uses 900 primitives, so every stream fits in one frame; the real model spans several
frames and the decoded SH came out wrong, which points at the framing.  Same code path, a model big
enough to be split.
"""
import os
import sys
import tempfile

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m19_codec as C


class S:
    pass


n = int(sys.argv[1]) if len(sys.argv) > 1 else 1_200_000
rng = np.random.default_rng(0)
s = S()
s.sh_degree = 3
s.means = torch.tensor(rng.normal(0, 30.0, (n, 3)), dtype=torch.float32)
s.scales = torch.tensor(np.exp(rng.normal(-5.0, 1.0, (n, 3))), dtype=torch.float32)
q = rng.normal(size=(n, 4)); q /= np.linalg.norm(q, axis=1, keepdims=True)
s.quats = torch.tensor(q, dtype=torch.float32)
s.opacities = torch.tensor(rng.uniform(0.02, 0.98, (n,)), dtype=torch.float32)
s.sh0 = torch.tensor(rng.normal(0, 1.0, (n, 3)), dtype=torch.float32)
s.shN = torch.tensor(rng.normal(0, 0.15, (n, 15, 3)), dtype=torch.float32)

td = tempfile.mkdtemp()
for spec in ("c10_o8_sh3", "vq12_c8_o8"):
    p = os.path.join(td, f"{spec}.gs1")
    rec = C.encode_model(s, spec, level=12, path=p)
    meta, got = C.read_container(p)
    print(spec, "file", os.path.getsize(p), "damaged", meta["damaged_bytes"])
    for name, raw in rec["streams"].items():
        same = got[name] == raw
        nf = [e["frames"] for e in meta["streams"] if e["name"] == name][0]
        print(f"  {name:16s} raw {len(raw):9d} frames {len(nf):2d} identical {same}")
    res = C.verify_roundtrip(s, spec)
    print("  verify", {k: round(v["max"], 4) for k, v in res.items()})
    out = C.decode(meta, got)
    print("  decoded sh_dc quantiles", np.array2string(np.quantile(out["sh_dc"], [0, 0.5, 1.0]), precision=3),
          "ref", np.array2string(np.quantile(np.asarray(s.sh0), [0, 0.5, 1.0]), precision=3))
