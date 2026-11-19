"""M19: are the two Morton orders the same, and how compact are their blocks?

The container's 10-bit position codec lands 25x further from the source than ``qfp_rd.quantize_cluster``
on the same data and the same block size, so the block *contents* must differ.  This compares the two
orderings directly and reports the block extents each produces.
"""
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments"))
import m4_bytes as M
import qfp_rd as Q

n = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000
rng = np.random.default_rng(0)
m = rng.normal(0, 30.0, (n, 3))
o_np = M.morton_order(m)
o_t = np.asarray(Q.morton_order(torch.from_numpy(m.astype(np.float32))).numpy())
print("orders equal:", np.array_equal(o_np, o_t))
for name, order in (("numpy", o_np), ("torch", o_t)):
    x = m[order]
    blk = M.CLUSTER_SIZE
    nblk = (n + blk - 1) // blk
    pad = nblk * blk - n
    if pad:
        x = np.concatenate([x, np.repeat(x[-1:], pad, axis=0)], axis=0)
    x = x.reshape(nblk, blk, 3)
    ext = (x.max(axis=1) - x.min(axis=1))
    print(f"{name}: block extent median {np.median(ext):.4f} p99 {np.quantile(ext, 0.99):.4f} max {ext.max():.3f}")
    step = np.maximum(ext / 1023.0, 1e-12)
    print(f"{name}: implied mean |error| ~ {float(np.mean(step / 4)):.6f}")
