"""M30 -- where does the position error land, and how does it compare to the local spacing?

For each container: decode the means, compare with the source model, and split the error by the size of
the cluster the primitive belongs to.  The question the round has to answer is whether a per-cluster
width chosen from the extent *helps* or whether the fixed-width grid was already allocating error the
way the renders want it.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import torch

sys.path.insert(0, "D:/3dsg_1/experiments")

import m20_model  # noqa: E402
import m4_bytes as M  # noqa: E402
import m19_codec as C  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ply")
    ap.add_argument("gs1", nargs="+")
    a = ap.parse_args()

    model = m20_model.load_model(a.ply)
    src = model.means.detach().cpu().numpy().astype(np.float32)
    order = M.morton_order(src)
    src_sorted = src[order]

    for path in a.gs1:
        meta, streams = C.read_container(path)
        out = C.decode(meta, streams)
        dec = out["means"].astype(np.float32)
        d = np.linalg.norm(dec - src_sorted, axis=1)
        hdr = np.frombuffer(streams["cluster_hdr"], dtype=np.float32).reshape(-1, 6)
        nblk = hdr.shape[0]
        block = int(M.CLUSTER_SIZE)
        blk = np.repeat(np.arange(nblk), block)[:src.shape[0]]
        ext = (hdr[:, 3:] * 255.0).max(axis=1) if "cluster_bits" not in streams else None
        if "cluster_bits" in streams:
            b = np.frombuffer(streams["cluster_bits"], dtype=np.uint8).astype(np.float64)
            qmax = (1 << b.astype(np.int64)) - 1
            ext = (hdr[:, 3:] * qmax[:, None]).max(axis=1)
        e = ext[blk]
        #: quartiles of cluster size
        edges = np.quantile(e, [0.0, 0.25, 0.5, 0.75, 1.0])
        print(f"== {path.split('/')[-1]}  mean|d| {d.mean()*1e3:.4f} mm  max {d.max()*1e3:.3f} mm")
        for i in range(4):
            sel = (e >= edges[i]) & (e <= edges[i + 1])
            if not sel.any():
                continue
            print(f"   extent {edges[i]*1e3:8.2f}-{edges[i+1]*1e3:8.2f} mm  n={sel.sum():9,d}  "
                  f"mean|d| {d[sel].mean()*1e3:8.4f} mm  ratio {d[sel].mean()/max(e[sel].mean(),1e-9):.5f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
