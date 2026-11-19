"""M19: is the PLY writer path itself lossless?  Save the reference model through ``to_ply``'s writer
and render it; if this is not ~24.5 dB then the codec is not the thing that is broken."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calib.gsrender as GR
from calib.plyio import save_inria_ply


def main() -> int:
    ref = "/workspace/data/m360std/output/bicycle/point_cloud/iteration_40000/point_cloud.ply"
    out = sys.argv[1]
    s = GR.load_splats(ref, device="cpu")
    means = np.asarray(s.means.detach().cpu().numpy(), dtype=np.float64)
    scales = np.asarray(s.scales.detach().cpu().numpy(), dtype=np.float64)
    quats = np.asarray(s.quats.detach().cpu().numpy(), dtype=np.float64)
    opac = np.asarray(s.opacities.detach().cpu().numpy(), dtype=np.float64).reshape(-1)
    sh0 = np.asarray(s.sh0.detach().cpu().numpy(), dtype=np.float64)
    shN = np.asarray(s.shN.detach().cpu().numpy(), dtype=np.float64)
    print("loaded", means.shape, "scales median", float(np.median(scales)),
          "opacity median", float(np.median(opac)), "shN", shN.shape, flush=True)
    save_inria_ply(out, means, scales, quats, opac, sh0, shN)
    #: Read back through the same loader the probe uses, and compare distributions.
    b = GR.load_splats(out, device="cpu")
    for key, a in (("means", means), ("scales", scales), ("quats", quats), ("opacities", opac)):
        v = np.asarray(getattr(b, key).detach().cpu().numpy(), dtype=np.float64).reshape(a.shape[0], -1)
        a2 = a.reshape(a.shape[0], -1)
        print(f"{key:10s} max|diff| {np.abs(a2 - v).max():.5g}  median ref {np.median(a2):.5g} "
              f"got {np.median(v):.5g}", flush=True)
    v = np.asarray(b.shN.detach().cpu().numpy(), dtype=np.float64)
    print(f"{'shN':10s} shape {v.shape} max|diff| {np.abs(shN - v).max():.5g}", flush=True)
    print("WROTE", out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
