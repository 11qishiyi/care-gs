"""Round-trip check: save a Splats with `save_inria_ply`, read it back with `load_splats`,
and render the same view both ways.

If the PSNR of the re-loaded model against the in-memory one is not ~50 dB, the writer and the
loader disagree about a convention (scale log vs raw, opacity logit, f_rest channel order,
quaternion order) and every measured number built on a saved PLY is wrong.

    python experiments/check_ply_roundtrip.py --ply /workspace/data/strat/abs/point_cloud.ply \
        --archive /workspace/data/m360std --scene bicycle_abs --n-views 2
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research", "code"))
from calib.archive_only import load_archive_only_scene  # noqa: E402
from calib.gsrender import load_splats, psnr, render  # noqa: E402
from calib.plyio import load_inria_ply, save_inria_ply  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ply", required=True)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--scene", required=True)
    ap.add_argument("--n-views", type=int, default=2)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    orig = load_splats(args.ply, device=args.device)
    sc = load_archive_only_scene(args.archive, args.scene, factor=1)
    idx = list(np.asarray(sc["cal_idx"]))[: args.n_views]
    c2w = torch.as_tensor(np.asarray(sc["camtoworlds"])[idx])
    Ks = torch.as_tensor(np.asarray(sc["Ks"])[idx])
    H, W = int(sc["height"]), int(sc["width"])
    out_a = render(orig, c2w, Ks, W, H)["colors"].detach().cpu().clamp(0, 1)
    del orig

    tmp = os.path.join(tempfile.mkdtemp(), "rt.ply")
    d = load_inria_ply(args.ply)
    save_inria_ply(tmp, d["means"], d["scales"], d["quats"], d["opacities"],
                   d["sh0"], d["shN"])
    rt = load_splats(tmp, device=args.device)
    out_b = render(rt, c2w, Ks, W, H)["colors"].detach().cpu().clamp(0, 1)
    ps = [psnr(out_a[i], out_b[i]) for i in range(len(idx))]
    print(f"round trip (file -> arrays -> file -> splats): PSNR {np.mean(ps):6.2f} dB "
          f"per view {np.round(ps, 2).tolist()}")
    print(f"  first render mean {out_a.mean():.4f}, second {out_b.mean():.4f}")
    print(f"  size {os.path.getsize(args.ply)} B -> {os.path.getsize(tmp)} B")
    os.remove(tmp)


if __name__ == "__main__":
    main()
