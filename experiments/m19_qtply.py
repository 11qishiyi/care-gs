"""M19 control: write the *reference quantiser's* model to a PLY and render it.

The decoded container renders ~4.5 dB below the number the RD curve reports for the same spec.  Two
things could cause that: the container loses something, or the PLY round trip does.  This writes the
model that produced the RD number straight to a PLY, so the two can be compared on one axis.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calib.gsrender as GR
import qfp_rd as Q
from calib.plyio import save_inria_ply


def main() -> int:
    ref, spec_name, out = sys.argv[1], sys.argv[2], sys.argv[3]
    spec = Q.parse_spec(spec_name)
    s = GR.load_splats(ref, device="cpu")
    q = Q.apply_quant(s, spec)
    means = np.asarray(q.means.detach().cpu().numpy(), dtype=np.float64)
    scales = np.asarray(q.scales.detach().cpu().numpy(), dtype=np.float64)
    quats = np.asarray(q.quats.detach().cpu().numpy(), dtype=np.float64)
    opac = np.asarray(q.opacities.detach().cpu().numpy(), dtype=np.float64).reshape(-1)
    sh0 = np.asarray(q.sh0.detach().cpu().numpy(), dtype=np.float64).reshape(len(means), 3)
    shN = np.asarray(q.shN.detach().cpu().numpy(), dtype=np.float64)
    print("quantised", means.shape, "shN", shN.shape,
          "sh0 q", np.round(np.quantile(sh0, [0, 0.5, 1]), 3), flush=True)
    save_inria_ply(out, means, scales, quats, opac, sh0, shN)
    print("WROTE", out, os.path.getsize(out), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
