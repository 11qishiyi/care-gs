"""M19: which half of the decoded model is wrong -- geometry or colour?

Both PLYs hold the same primitives; the decoded one is in Morton order of the reference positions, so
``order = morton_order(ref.means)`` is exactly the permutation between them.  Two hybrids are written:

* ``geo_dec_col_ref``: decoded geometry, reference colour (pairs through ``order``)
* ``geo_ref_col_dec``: reference geometry, decoded colour

Whichever hybrid renders near the reference's 24.5 dB is the half that survived.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calib.gsrender as GR
import m4_bytes as M
from calib.plyio import save_inria_ply


def arr(s, key):
    a = getattr(s, key).detach().cpu().numpy()
    return np.asarray(a, dtype=np.float64)


def main() -> int:
    ref_path, dec_path, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    r = GR.load_splats(ref_path, device="cpu")
    d = GR.load_splats(dec_path, device="cpu")
    rm = arr(r, "means")
    order = M.morton_order(rm)
    print("order", order.shape, "dec", arr(d, "means").shape, flush=True)
    #: sanity: the decoded positions must equal the reference's, permuted
    err = np.abs(arr(d, "means") - rm[order]).max()
    print(f"means |dec - ref[order]| max {err:.4g}", flush=True)
    rshN = arr(r, "shN")[order]
    dshN = arr(d, "shN")
    print("shN |dec - ref[order]| max", float(np.abs(dshN - rshN).max()), flush=True)
    os.makedirs(outdir, exist_ok=True)
    #: decoded geometry + reference colour
    save_inria_ply(os.path.join(outdir, "geo_dec_col_ref.ply"), arr(d, "means"), arr(d, "scales"),
                   arr(d, "quats"), arr(d, "opacities"), arr(r, "sh0")[order], rshN)
    #: reference geometry + decoded colour
    save_inria_ply(os.path.join(outdir, "geo_ref_col_dec.ply"), arr(r, "means"), arr(r, "scales"),
                   arr(r, "quats"), arr(r, "opacities"), arr(d, "sh0"), dshN)
    print("WROTE hybrids", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
