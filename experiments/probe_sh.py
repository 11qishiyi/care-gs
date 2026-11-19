"""Does the SH coefficient layout explain the clean-render gap?

INRIA writes ``f_rest_0 .. 44`` channel-major: the 15 coefficients of red, then green, then blue.
gsplat wants ``(N, 15, 3)``, so one transpose is needed.  Getting it wrong does not crash -- it
permutes view-dependent colour between channels, which costs a few dB while leaving the diffuse
(DC) term, and therefore SSIM, almost intact.

    python experiments/probe_sh.py --archive <arch> --scene bonsai_smoke --n-views 1
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import torch
from PIL import Image
from plyfile import PlyData

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research", "code"))
from calib.archive_only import load_archive_only_scene  # noqa: E402
from calib.gsrender import Splats, render  # noqa: E402


def find_ply(archive: str, scene: str) -> str:
    base = os.path.join(archive, "output", scene, "point_cloud")
    best = None
    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d, "point_cloud.ply")
        if os.path.isfile(p):
            best = p
    return best


def psnr01(a, b):
    return 10.0 * np.log10(1.0 / max(float(np.mean((a - b) ** 2)), 1e-12))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--scene", required=True)
    ap.add_argument("--factor", type=int, default=1)
    ap.add_argument("--n-views", type=int, default=1)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    ply = PlyData.read(find_ply(args.archive, args.scene))
    v = ply["vertex"]
    n = v.count
    names = [p.name for p in v.properties]
    means = torch.as_tensor(np.stack([v["x"], v["y"], v["z"]], 1).astype(np.float32), device=args.device)
    scales = torch.as_tensor(np.exp(np.stack([v["scale_0"], v["scale_1"], v["scale_2"]], 1)
                                   .astype(np.float32)), device=args.device)
    quats = torch.as_tensor(np.stack([v["rot_0"], v["rot_1"], v["rot_2"], v["rot_3"]], 1)
                            .astype(np.float32), device=args.device)
    quats = quats / quats.norm(dim=-1, keepdim=True).clamp_min(1e-12)
    opac = torch.as_tensor(1.0 / (1.0 + np.exp(-np.asarray(v["opacity"], np.float32)))
                           .astype(np.float32), device=args.device)
    sh0 = torch.as_tensor(np.stack([v["f_dc_0"], v["f_dc_1"], v["f_dc_2"]], 1)
                          .astype(np.float32), device=args.device)[:, None, :]
    rest = [f"f_rest_{i}" for i in range(45) if f"f_rest_{i}" in names]
    raw = np.stack([np.asarray(v[k], np.float32) for k in rest], 1)
    print(f"{n} primitives, {len(rest)} f_rest properties, file {os.path.getsize(find_ply(args.archive, args.scene))/1e6:.0f} MB")

    sc = load_archive_only_scene(args.archive, args.scene, factor=args.factor)
    idx = list(np.asarray(sc["cal_idx"]))[: args.n_views]
    c2w = torch.as_tensor(np.asarray(sc["camtoworlds"])[idx])
    Ks = torch.as_tensor(np.asarray(sc["Ks"])[idx])
    H, W = int(sc["height"]), int(sc["width"])
    paths = np.asarray(sc["image_paths"])
    gts = np.stack([np.asarray(Image.open(paths[i]).convert("RGB").resize((W, H), Image.BILINEAR),
                               np.float32) / 255.0 for i in idx])

    layouts = {
        "channel-major -> (N,15,3)": raw.reshape(n, 3, 15).transpose(0, 2, 1),
        "coefficient-major (N,15,3)": raw.reshape(n, 15, 3),
    }
    for tag, shn in layouts.items():
        sp = Splats(means=means, scales=scales, quats=quats, opacities=opac,
                    sh0=sh0, shN=torch.as_tensor(np.ascontiguousarray(shn), device=args.device))
        out = render(sp, c2w, Ks, W, H)
        pred = out["colors"].detach().cpu().clamp(0, 1).numpy()
        ps = np.mean([psnr01(pred[i], gts[i]) for i in range(len(idx))])
        print(f"  {tag:32s} PSNR {ps:6.2f} dB")
        del sp, out, pred
    print(f"  DC-only (SH degree 0) would show the diffuse ceiling; gt mean {gts.mean():.3f}")


if __name__ == "__main__":
    main()
