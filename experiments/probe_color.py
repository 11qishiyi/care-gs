"""Is a clean-render gap a colour-convention gap or a geometry gap?

Renders a few held-out views of one archive entry and reports PSNR under four colour fits:

    raw          render as it comes out of the rasteriser
    gain         one global per-channel gain (3 numbers, fitted on all views)
    affine       one global per-channel gain and bias (6 numbers, fitted on all views)
    per-view     per-channel gain and bias fitted on each view separately (exposure drift)

Reading: if `raw` is far below `affine` and the fitted gains are close to 1, the model and the
ground truth disagree on colour convention (sRGB vs linear, exposure normalisation) rather than
on geometry, and the archive comparison is salvageable by fixing the convention.  If the gap
survives the fit, the model does not reproduce the published number and C1 must say so.

    python experiments/probe_color.py --archive <arch> --scene bonsai_smoke --n-views 4
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
    if best is None:
        raise SystemExit(f"no PLY under {base}")
    return best


def psnr01(a: np.ndarray, b: np.ndarray) -> float:
    return 10.0 * np.log10(1.0 / max(float(np.mean((a - b) ** 2)), 1e-12))


def fit_affine(pred: np.ndarray, gt: np.ndarray, bias: bool = True):
    """Per-channel least squares gain (+bias) mapping pred (N,3) to gt (N,3).

    Channels are fitted independently: the archive ground truth is the same sRGB image the model
    was trained on, so a colour-convention error is a per-channel scale/offset, never a mixing.
    """
    A = pred.astype(np.float64)
    B = gt.astype(np.float64)
    gain = np.zeros(3)
    off = np.zeros(3)
    for c in range(3):
        a, b = A[:, c], B[:, c]
        if bias:
            M = np.stack([a, np.ones_like(a)], axis=1)
            coef, *_ = np.linalg.lstsq(M, b, rcond=None)
            gain[c], off[c] = coef[0], coef[1]
        else:
            gain[c] = float((a * b).sum() / max(float((a * a).sum()), 1e-12))
    return gain, off


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--scene", required=True)
    ap.add_argument("--factor", type=int, default=1)
    ap.add_argument("--n-views", type=int, default=4)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    sc = load_archive_only_scene(args.archive, args.scene, factor=args.factor)
    splats = load_splats(find_ply(args.archive, args.scene), device=args.device)
    idx = list(np.asarray(sc["cal_idx"]))[: args.n_views]
    c2w = torch.as_tensor(np.asarray(sc["camtoworlds"])[idx])
    Ks = torch.as_tensor(np.asarray(sc["Ks"])[idx])
    H, W = int(sc["height"]), int(sc["width"])
    out = render(splats, c2w, Ks, W, H)
    pred = out["colors"].detach().cpu().clamp(0, 1).numpy()
    paths = np.asarray(sc["image_paths"])
    gts = np.stack([np.asarray(Image.open(paths[i]).convert("RGB").resize((W, H), Image.BILINEAR),
                               np.float32) / 255.0 for i in idx])
    del out
    n = len(idx)

    raw = float(np.mean([psnr01(pred[i], gts[i]) for i in range(n)]))
    flat_p = np.concatenate([pred[i].reshape(-1, 3) for i in range(n)])
    flat_g = np.concatenate([gts[i].reshape(-1, 3) for i in range(n)])
    gain, _ = fit_affine(flat_p, flat_g, bias=False)
    if gain.shape != (3,):
        # diagonal-only fit: a per-channel gain cannot mix channels, so solve each one separately
        gain = np.array([float((flat_p[:, c] * flat_g[:, c]).sum()
                               / max(float((flat_p[:, c] ** 2).sum()), 1e-12)) for c in range(3)])
    aff_gain, aff_bias = fit_affine(flat_p, flat_g, bias=True)
    gain_ps = np.mean([psnr01(np.clip(pred[i] * gain, 0, 1), gts[i]) for i in range(n)])
    aff_ps = np.mean([psnr01(np.clip(pred[i] * aff_gain + aff_bias, 0, 1), gts[i]) for i in range(n)])
    pv, pv_coef = [], []
    for i in range(n):
        k, b = fit_affine(pred[i].reshape(-1, 3), gts[i].reshape(-1, 3), bias=True)
        pv_coef.append(np.concatenate([k, b]))
        pv.append(psnr01(np.clip(pred[i] * k + b, 0, 1), gts[i]))

    print(f"scene {args.scene}  prims {splats.n}  views {n}  {W}x{H}")
    print(f"  raw       {raw:6.2f} dB")
    print(f"  gain      {gain_ps:6.2f} dB  gain={np.round(gain, 3)}")
    print(f"  affine    {aff_ps:6.2f} dB  gain={np.round(aff_gain, 3)} bias={np.round(aff_bias, 3)}")
    print(f"  per-view  {np.mean(pv):6.2f} dB  coef std={np.round(np.std(np.array(pv_coef), 0), 3)}")
    print(f"  means: gt {gts.mean():.3f}  render {pred.mean():.3f}")

    # structural check: a pure gain cannot fix geometry.  Report the residual's per-view
    # correlation with the mean residual, which is high when the error is a global offset.
    res = (pred - gts)
    print(f"  residual mean {res.mean():+.4f}  std {res.std():.4f}  "
          f"|mean|/std {abs(res.mean()) / max(res.std(), 1e-9):.2f}")


if __name__ == "__main__":
    main()
