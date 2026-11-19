"""M19: does the primitive ORDER cost quality?

The byte model ships primitives in Morton order (so the permutation costs no bits).  If the same
quantised model renders 4 dB worse in that order, the ordering is not free after all -- and every RD
number in this series, measured in training order, would be optimistic about the shipped file.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calib.gsrender as GR
import m4_bytes as M
from calib.plyio import save_inria_ply


def main() -> int:
    src, out = sys.argv[1], sys.argv[2]
    s = GR.load_splats(src, device="cpu")
    a = lambda k: np.asarray(getattr(s, k).detach().cpu().numpy(), dtype=np.float64)  # noqa: E731
    means = a("means")
    order = M.morton_order(means)
    save_inria_ply(out, means[order], a("scales")[order], a("quats")[order],
                   a("opacities")[order], a("sh0")[order], a("shN")[order])
    print("WROTE", out, "order head", order[:5], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
