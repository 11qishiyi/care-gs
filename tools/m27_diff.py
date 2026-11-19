"""Where do the decibels go?  Compare a decoded anchor container with the model it came from.

    PYTHONPATH=... python3 tools/m27_diff.py <ply> <gs1> [--ppa 8]

Prints, in the container's own primitive order: position error, scale error, quaternion error,
opacity error, DC error and rest error, plus the anchor statistics that decide them.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ply")
    ap.add_argument("gs1")
    ap.add_argument("--ppa", type=float, default=0.0, help="re-encode at this ppa instead of reading")
    a = ap.parse_args()

    import m19_codec as C
    import m20_model
    import m27_anchor as A

    splats = m20_model.load_model(a.ply)
    n = int(splats.means.shape[0])
    meta, streams = C.read_container(a.gs1)
    #: dispatch through the codec so the same audit serves M27 (constant anchors) and M28 (predicted)
    out = C.decode(meta, streams)
    voxel = float(meta["voxel"])
    order = A.group(np.asarray(splats.means, dtype=np.float32), voxel)[0]

    means = np.asarray(splats.means, dtype=np.float32)[order]
    rest = np.asarray(splats.shN, dtype=np.float32).reshape(n, -1)[order]
    rest_d = out["sh_rest"].reshape(n, -1)
    dc = np.asarray(splats.sh0, dtype=np.float32).reshape(n, 3)[order]
    dc_d = out["sh_dc"]
    op = np.asarray(splats.opacities, dtype=np.float32)[order]
    sc = np.asarray(splats.scales, dtype=np.float32)[order]

    def rel(x, y):
        d = np.abs(x - y)
        scale = max(float(np.abs(x).mean()), 1e-9)
        return float(d.mean()), float(d.max()), float(d.mean() / scale)

    print(f"n={n:,} anchors={int(meta['n_anchor']):,} ppa={meta['ppa_measured']:.2f} voxel={voxel:.4f} predicted={bool(meta.get('predicted'))}")
    for name, x, y in (("means", means, out["means"]), ("scales", sc, out["scales"]),
                       ("opacity", op, out["opacities"]), ("dc", dc, dc_d), ("rest", rest, rest_d)):
        m, mx, r = rel(x, y)
        print(f"  {name:<8} mean|d|={m:.5f} max|d|={mx:.5f} rel={r * 100:6.2f}%")
    q = np.asarray(splats.quats, dtype=np.float32)[order]
    qd = out["quats"]
    dot = np.abs((q * qd).sum(axis=1))
    print(f"  quats    min|dot|={float(dot.min()):.5f} mean={float(dot.mean()):.5f}")
    #: the rest error is the sharing cost; compare with what a *per-primitive* coder achieves
    print(f"  rest per-anchor spread: std across members "
          f"{float(np.std(rest - rest_d, axis=1).mean()):.5f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
