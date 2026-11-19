"""M19: does the container's position codec match the RD curve's own `quantize_cluster`?

If the two agree, the 4 dB must come from somewhere else; if they do not, the byte model is shipping
a coarser position grid than the curve scored, and every c-spec RD point is optimistic.
"""
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calib.gsrender as GR
import m4_bytes as M
import qfp_rd as Q


def main() -> int:
    ref, gs1 = sys.argv[1], sys.argv[2]
    s = GR.load_splats(ref, device="cpu")
    means = np.asarray(s.means.detach().cpu().numpy(), dtype=np.float64)
    qc = np.asarray(Q.quantize_cluster(torch.from_numpy(means.copy()), 10).numpy(), dtype=np.float64)
    order = M.morton_order(means)
    d = np.abs(qc[order] - means[order])
    print(f"quantize_cluster(10) err vs ref: max {d.max():.6g} mean {d.mean():.6g}", flush=True)
    import m19_codec as C

    meta, streams = C.read_container(gs1)
    dec = C.decode(meta, streams)["means"]
    dd = np.abs(dec - means[order])
    print(f"container decode   err vs ref: max {dd.max():.6g} mean {dd.mean():.6g}", flush=True)
    dm = np.abs(dec - qc[order])
    print(f"container vs quantize_cluster: max {dm.max():.6g} mean {dm.mean():.6g}", flush=True)
    #: block-by-block, to see whether the two agree on most blocks and disagree on some
    blk = M.CLUSTER_SIZE
    per_block = np.array([np.abs(dec[i:i + blk] - qc[order][i:i + blk]).max()
                          for i in range(0, min(len(dec), blk * 200), blk)])
    print("first 200 blocks: max|diff| quantiles",
          np.round(np.quantile(per_block, [0, 0.5, 0.9, 1.0]), 6), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
