"""Why does a one-frame burst change every primitive?  Compare two decodes attribute by attribute."""
import sys

import numpy as np

sys.path[:0] = ["/workspace/code/experiments", "/workspace/code"]
import m19_codec as C

a, b = sys.argv[1], sys.argv[2]
ma, sa = C.read_container(a, tolerant=True)
mb, sb = C.read_container(b, tolerant=True)
da, db = C.decode(ma, sa), C.decode(mb, sb)
for k in ("means", "scales", "opacities", "quats", "sh_dc", "sh_rest"):
    if k not in da:
        continue
    x = np.asarray(da[k], dtype=np.float32)
    y = np.asarray(db[k], dtype=np.float32)
    if x.shape != y.shape:
        print(k, "shape", x.shape, y.shape)
        continue
    d = np.abs(x - y).reshape(len(x), -1).max(axis=1)
    q = np.quantile(d, [0.0, 0.5, 0.9, 0.99, 1.0])
    print(f"{k:9s} changed {(d > 0).mean()*100:6.2f}%  >1e-6 {(d > 1e-6).mean()*100:6.2f}%  "
          f"q {np.round(q, 6)}  max {d.max():.6g}")
