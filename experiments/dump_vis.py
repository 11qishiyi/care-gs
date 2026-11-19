"""Dump render / ground truth / difference for a few test views so the failure is visible.

    python experiments/dump_vis.py --archive <arch> --scene bicycle_abs --out /workspace/res/vis
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research", "code"))
from calib.archive_only import load_archive_only_scene  # noqa: E402
from calib.gsrender import load_splats, render  # noqa: E402


def find_ply(archive: str, scene: str) -> str:
    base = os.path.join(archive, "output", scene, "point_cloud")
    best = None
    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d, "point_cloud.ply")
        if os.path.isfile(p):
            best = p
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--scene", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-views", type=int, default=2)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    sc = load_archive_only_scene(args.archive, args.scene, factor=1)
    splats = load_splats(find_ply(args.archive, args.scene), device=args.device)
    idx = list(np.asarray(sc["cal_idx"]))[: args.n_views]
    c2w = torch.as_tensor(np.asarray(sc["camtoworlds"])[idx])
    Ks = torch.as_tensor(np.asarray(sc["Ks"])[idx])
    H, W = int(sc["height"]), int(sc["width"])
    out = render(splats, c2w, Ks, W, H)
    pred = out["colors"].detach().cpu().clamp(0, 1).numpy()
    alpha = out["alphas"].detach().cpu().numpy()
    paths = np.asarray(sc["image_paths"])
    for j, i in enumerate(idx):
        gt = np.asarray(Image.open(paths[i]).convert("RGB").resize((W, H), Image.BILINEAR),
                        np.float32) / 255.0
        Image.fromarray((pred[j] * 255).astype(np.uint8)).save(
            os.path.join(args.out, f"{j}_render.png"))
        Image.fromarray((gt * 255).astype(np.uint8)).save(os.path.join(args.out, f"{j}_gt.png"))
        d = np.abs(pred[j] - gt).mean(-1)
        Image.fromarray((np.clip(d * 3, 0, 1) * 255).astype(np.uint8)).save(
            os.path.join(args.out, f"{j}_diff.png"))
        print(f"view {j} {os.path.basename(paths[i])}: render mean {pred[j].mean():.3f} "
              f"gt mean {gt.mean():.3f} alpha mean {alpha[j].mean():.3f} "
              f"abs diff {d.mean():.4f}")
    print("WROTE", args.out)


if __name__ == "__main__":
    main()
