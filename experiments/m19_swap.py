"""M19: one attribute at a time -- which decoded field costs the 4 dB?

Renders four hybrids, each with exactly one attribute restored from the reference model (aligned to
the decoded Morton order): positions, scales, quaternions, opacities.  The one that recovers the
control's 24.3 dB is the field the container gets wrong.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calib.gsrender as GR
import m4_bytes as M
from calib.plyio import save_inria_ply

FIELDS = ("means", "scales", "quats", "opacities")


def get(s, k):
    return np.asarray(getattr(s, k).detach().cpu().numpy(), dtype=np.float64)


def main() -> int:
    ref_path, dec_path, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    r = GR.load_splats(ref_path, device="cpu")
    d = GR.load_splats(dec_path, device="cpu")
    order = M.morton_order(get(r, "means"))
    base = {k: (get(d, k) if k != "opacities" else get(d, k).reshape(-1)) for k in FIELDS}
    ref = {k: (get(r, k)[order] if k != "opacities" else get(r, k)[order].reshape(-1))
           for k in FIELDS}
    os.makedirs(outdir, exist_ok=True)
    for f in FIELDS:
        mix = dict(base)
        mix[f] = ref[f]
        out = os.path.join(outdir, f"swap_{f}.ply")
        save_inria_ply(out, mix["means"], mix["scales"], mix["quats"], mix["opacities"],
                       get(d, "sh0"), get(d, "shN"))
        err = np.abs(base[f].reshape(len(base[f]), -1) - ref[f].reshape(len(ref[f]), -1))
        print(f"{out}  decoded-vs-ref max {err.max():.5g} mean {err.mean():.5g}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
