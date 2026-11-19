"""2x2 activation probe: are the PLY attributes raw (log/logit) or already activated?

An INRIA 3DGS PLY stores scales in log space and opacities as logits.  Reading them with the
wrong activation is not a crash, it is a quiet 3-5 dB loss: exp() applied twice blurs geometry,
sigmoid() applied twice washes colour out.  Because that is exactly the size of the gap we see
against the published rows, this probe renders the same views under all four combinations and
prints PSNR, so the convention is decided by measurement rather than by reading two loaders.

    python experiments/probe_activation.py --archive <arch> --scene bonsai_smoke --n-views 4
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
    if best is None:
        raise SystemExit(f"no PLY under {base}")
    return best


def read_ply(path: str):
    ply = PlyData.read(path)
    v = ply["vertex"]
    names = [p.name for p in v.properties]
    n = v.count
    means = np.stack([v["x"], v["y"], v["z"]], 1).astype(np.float32)
    scales = np.stack([v["scale_0"], v["scale_1"], v["scale_2"]], 1).astype(np.float32)
    quats = np.stack([v["rot_0"], v["rot_1"], v["rot_2"], v["rot_3"]], 1).astype(np.float32)
    opac = np.asarray(v["opacity"], dtype=np.float32)
    sh0 = np.stack([v["f_dc_0"], v["f_dc_1"], v["f_dc_2"]], 1).astype(np.float32)
    rest = [f"f_rest_{i}" for i in range(45) if f"f_rest_{i}" in names]
    if rest:
        raw = np.stack([np.asarray(v[k], dtype=np.float32) for k in rest], 1)  # (n, 45)
        # INRIA writes channel-major: 15 coefficients for R, then G, then B.
        shN = raw.reshape(n, 3, 15).transpose(0, 2, 1).copy()
    else:
        shN = np.zeros((n, 15, 3), np.float32)
    print(f"{n} primitives, {len(rest)} f_rest properties, shN {shN.shape}")
    return means, scales, quats, opac, sh0, shN


def _psnr(a: np.ndarray, b: np.ndarray) -> float:
    return 10.0 * np.log10(1.0 / max(float(np.mean((a - b) ** 2)), 1e-12))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--scene", required=True)
    ap.add_argument("--factor", type=int, default=1)
    ap.add_argument("--n-views", type=int, default=4)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    sc = load_archive_only_scene(args.archive, args.scene, factor=args.factor)
    idx = list(np.asarray(sc["cal_idx"]))[: args.n_views]
    c2w = torch.as_tensor(np.asarray(sc["camtoworlds"])[idx])
    Ks = torch.as_tensor(np.asarray(sc["Ks"])[idx])
    H, W = int(sc["height"]), int(sc["width"])
    gts = [np.asarray(Image.open(np.asarray(sc["image_paths"])[i]).convert("RGB").resize((W, H),
                       Image.BILINEAR), np.float32) / 255.0 for i in idx]

    means, scales, quats, opac, sh0, shN = read_ply(find_ply(args.archive, args.scene))
    dev = args.device
    means_t = torch.as_tensor(means, device=dev)
    quats_t = torch.as_tensor(quats, device=dev)
    quats_t = quats_t / quats_t.norm(dim=-1, keepdim=True).clamp_min(1e-12)
    sh0_t = torch.as_tensor(sh0, device=dev)[:, None, :]
    shN_t = torch.as_tensor(shN, device=dev)

    print(f"scene {args.scene}  {W}x{H}  views {len(idx)}")
    for act in ("exp", "raw"):
        for oact in ("sigmoid", "raw"):
            s = torch.exp(torch.as_tensor(scales, device=dev)) if act == "exp" \
                else torch.as_tensor(scales, device=dev)
            o = torch.sigmoid(torch.as_tensor(opac, device=dev)) if oact == "sigmoid" \
                else torch.as_tensor(opac, device=dev)
            sp = Splats(means=means_t, scales=s, quats=quats_t, opacities=o,
                        sh0=sh0_t, shN=shN_t)
            out = render(sp, c2w, Ks, W, H)
            pred = out["colors"].detach().cpu().clamp(0, 1).numpy()
            ps = np.mean([_psnr(pred[i], gts[i]) for i in range(len(idx))])
            print(f"  scales={act:3s} opacities={oact:7s}  PSNR {ps:6.2f} dB  "
                  f"(s.mean {float(s.mean()):.4f}, o.mean {float(o.mean()):.3f})")
            del sp, out, pred
    print(f"  gt mean {np.mean(gts):.3f}")


if __name__ == "__main__":
    main()
