"""How much of a primitive's attribute entropy lives *inside* its voxel?  (M28 diagnosis)

If an anchor could describe its members, the within-voxel variance would be small compared with the
total variance.  This measures that fraction directly, for the attributes the anchor would have to
predict, at the voxel sizes M27/M28 used, plus the arithmetic of how many bits the anchor actually has.
"""

from __future__ import annotations

import sys

import numpy as np


def main() -> int:
    ply = sys.argv[1]
    import m27_anchor as A
    import m20_model
    import geom_pack as GP

    s = m20_model.load_model(ply)
    means = np.asarray(s.means, dtype=np.float32)
    n = means.shape[0]
    scale = np.log(np.maximum(np.asarray(s.scales, dtype=np.float32), 1e-12))
    op = np.clip(np.asarray(s.opacities, dtype=np.float32), 1e-6, 1 - 1e-6)
    logit = np.log(op / (1 - op))
    quats = np.asarray(s.quats, dtype=np.float64)
    q = quats / np.linalg.norm(quats, axis=1, keepdims=True)

    print(f"n={n:,}")
    print(f"{'ppa':>5}{'voxel':>9}{'anchors':>10}{'R2 scale':>10}{'R2 opacity':>12}"
          f"{'R2 quat':>9}{'bits/anchor':>13}")
    for ppa in (4, 8, 16, 64, 256):
        voxel = A.voxel_size_for(means, float(ppa))
        order, starts, counts, vox, org = A.group(means, voxel)
        na = vox.shape[0]
        ofa = np.repeat(np.arange(na), counts)

        def r2(v):
            v = np.asarray(v, dtype=np.float64)[order]
            m = np.add.reduceat(v, starts, axis=0) / (counts[:, None] if v.ndim > 1 else counts)
            res = v - (m[ofa] if v.ndim > 1 else m[ofa])
            tot = v - v.mean(axis=0)
            return 1.0 - float((res ** 2).sum() / max((tot ** 2).sum(), 1e-12))

        #: the anchor record M27/M28 stores: 3 scales + 4 (st3: 26 bit) + 1 opacity, quantised
        bits = 8 * 3 + 26 + 8
        print(f"{ppa:>5}{voxel:>9.3f}{na:>10,}{r2(scale):>10.3f}{r2(logit[:, None]):>12.3f}"
              f"{r2(q):>9.3f}{bits:>13}")
    print()
    print("R2 = fraction of an attribute's variance that its voxel's mean explains;")
    print("1 - R2 has to be paid per primitive no matter how large the network is.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
