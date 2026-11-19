"""Learned-matcher robustness check (stage 10).

The paper's task families are hand-built.  This script asks whether a *learned*,
detector-free matcher changes the picture: it renders the clean asset and two pruned
variants at half resolution (factor 2), matches ground truth to render with LoFTR
(kornia, MegaDepth weights), and repeats the hand-built patch task on the same
renders so the two are compared on identical images.

Per scene and variant it reports
  * LoFTR: mean precision at 2 px (the images are pixel-aligned, so a perfect render
    gives identity correspondences), median displacement, match count, mean confidence;
  * NCC: the paper's reduced patch task (32 px patch, +-24 search, 60 patches/view)
    on the same half-resolution renders.

    python experiments/stage10_learned.py --archive /workspace/data/out3dgs \
        --scenes bicycle,flowers,stump,treehill --out /workspace/res/stage10
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "research", "code"))
sys.path.insert(0, os.path.join(REPO, "experiments"))

RATIOS = (("clean", 1.0), ("prune30", 0.3), ("prune10", 0.1))


def top_k(scores, ratio):
    import torch
    k = max(1, int(round(ratio * scores.numel())))
    return torch.argsort(-scores)[:k].sort().values


def render_np(splats, c2w, K, W, H, chunk=2):
    import torch
    from calib.gsrender import render
    cols = []
    m = c2w.shape[0]
    with torch.no_grad():
        for s in range(0, m, chunk):
            it = torch.arange(s, min(m, s + chunk), device=c2w.device)
            cols.append(render(splats, c2w[it], K[it], W, H)["colors"].permute(0, 3, 1, 2).float().cpu())
    return torch.cat(cols, 0).numpy()


def pad_to_8(x):
    import torch
    _, _, H, W = x.shape
    ph, pw = (-H) % 8, (-W) % 8
    if ph or pw:
        x = torch.nn.functional.pad(x, (0, pw, 0, ph), mode="replicate")
    return x


def loftr_stats(matcher, gt_gray, ren_gray, device="cuda", max_side=640, tol=1.0):
    """Match at the resolution LoFTR is trained for: both images are resized so the long side is
    `max_side`; a match counts as correct if it lands within `tol` pixels *at that resolution*
    (for a 1236-px render, 1 resized px is 1.93 render px, i.e. the paper's 2-px tolerance)."""
    import torch
    a = torch.as_tensor(gt_gray, dtype=torch.float32)[None, None].to(device)
    b = torch.as_tensor(ren_gray, dtype=torch.float32)[None, None].to(device)
    h, w = a.shape[-2:]
    f = min(1.0, max_side / max(h, w))
    if f < 1.0:
        size = (max(8, int(round(h * f))), max(8, int(round(w * f))))
        a = torch.nn.functional.interpolate(a, size=size, mode="bilinear", align_corners=False)
        b = torch.nn.functional.interpolate(b, size=size, mode="bilinear", align_corners=False)
    a = pad_to_8(a)
    b = pad_to_8(b)
    with torch.no_grad():
        out = matcher({"image0": a, "image1": b})
    kp0 = out["keypoints0"].detach().cpu().numpy()
    kp1 = out["keypoints1"].detach().cpu().numpy()
    conf = out["confidence"].detach().cpu().numpy() if "confidence" in out else np.ones(len(kp0))
    if len(kp0) == 0:
        return dict(n=0, precision=float("nan"), med_disp=float("nan"), mean_conf=float("nan"))
    d = np.abs(kp0 - kp1).max(axis=1)
    keep = conf >= 0.5
    if keep.sum() >= 5:
        d, conf = d[keep], conf[keep]
    return dict(n=int(len(d)), precision=float((d <= tol).mean()),
                med_disp=float(np.median(d)), mean_conf=float(np.mean(conf)),
                match_scale=f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--scenes", default="bicycle,flowers,stump,treehill")
    ap.add_argument("--out", default="/workspace/res/stage10")
    ap.add_argument("--factor", type=int, default=2)
    ap.add_argument("--n-patches", type=int, default=60)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--skip-ncc", action="store_true")
    args = ap.parse_args()

    import torch
    from second_task2 import build_scene, find_ply, ncc_map
    from node_run import sample_corners
    from calib.gsrender import load_splats
    from kornia.feature import LoFTR

    os.makedirs(args.out, exist_ok=True)
    matcher = LoFTR(pretrained="outdoor").to(args.device).eval()

    def ncc_task(gt_gray, ren_gray, corners, size=32, search=24):
        H, W = ren_gray.shape
        ok = tot = 0
        for (y, x) in corners:
            patch = gt_gray[y:y + size, x:x + size]
            if patch.shape[0] != size or patch.shape[1] != size:
                continue
            y0, y1 = max(0, y - search), min(H, y + search + size)
            x0, x1 = max(0, x - search), min(W, x + search + size)
            win = ren_gray[y0:y1, x0:x1]
            if win.shape[0] < size or win.shape[1] < size:
                continue
            m = ncc_map(win, patch)
            if m.size == 0:
                continue
            iy, ix = np.unravel_index(np.argmax(m), m.shape)
            hit = abs((iy + y0) - y) <= 2 and abs((ix + x0) - x) <= 2 and m[iy, ix] >= 0.60
            ok += int(hit)
            tot += 1
        return (ok / tot) if tot else float("nan"), tot

    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        t0 = time.time()
        sc, gt, W, H = build_scene(args.archive, scene, args.factor)
        c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K = torch.from_numpy(sc["Ks"]).to(args.device)
        base = load_splats(find_ply(args.archive, scene), device=args.device)
        print(f"\n=== {scene}: {base.n} primitives, {len(gt)} views, {W}x{H} ===", flush=True)
        gt_gray = gt.mean(3)
        rng = np.random.default_rng(1234)
        corners = [sample_corners(gt_gray[v], 32, args.n_patches, rng) for v in range(len(gt_gray))]

        out = dict(scene=scene, n_views=int(len(gt)), W=W, H=H, factor=args.factor, variants={})
        for name, ratio in RATIOS:
            splats = base if ratio >= 1.0 else base.subset(top_k(base.opacities, ratio))
            imgs = render_np(splats, c2w, K, W, H)
            ren_gray = imgs.mean(1)
            rows_l, rows_n = [], []
            for v in range(len(gt_gray)):
                rows_l.append(loftr_stats(matcher, gt_gray[v], ren_gray[v], args.device))
                if not args.skip_ncc:
                    rows_n.append(ncc_task(gt_gray[v], ren_gray[v], corners[v]))
            var = dict(
                psnr=float(10 * np.log10(1.0 / max(float(np.mean((imgs - np.transpose(gt, (0, 3, 1, 2))) ** 2)), 1e-12))),
                n_primitives=int(splats.n),
                loftr=dict(
                    precision=[r["precision"] for r in rows_l],
                    n=[r["n"] for r in rows_l],
                    med_disp=[r["med_disp"] for r in rows_l],
                    mean_conf=[r["mean_conf"] for r in rows_l],
                    precision_mean=float(np.nanmean([r["precision"] for r in rows_l])),
                    n_mean=float(np.nanmean([r["n"] for r in rows_l])),
                ),
            )
            if not args.skip_ncc:
                var["ncc"] = dict(hit=[r[0] for r in rows_n], total=[r[1] for r in rows_n],
                                  hit_mean=float(np.nanmean([r[0] for r in rows_n])))
            out["variants"][name] = var
            del imgs
            torch.cuda.empty_cache()
            print(f"  {name:8s} PSNR {var['psnr']:5.2f}  LoFTR prec@2px {var['loftr']['precision_mean']:.3f} "
                  f"(n={var['loftr']['n_mean']:.0f})"
                  + (f"  NCC hit {var['ncc']['hit_mean']:.3f}" if 'ncc' in var else ""), flush=True)

        points = {}
        for key in ("loftr",):
            clean = out["variants"]["clean"][key]
            for name in ("prune30", "prune10"):
                v = out["variants"][name][key]
                points[f"{key}_{name}"] = dict(
                    drop=100 * (v["precision_mean"] - clean["precision_mean"]))
        if not args.skip_ncc:
            clean = out["variants"]["clean"]["ncc"]["hit_mean"]
            for name in ("prune30", "prune10"):
                v = out["variants"][name]["ncc"]["hit_mean"]
                points[f"ncc_{name}"] = dict(drop=100 * (v - clean))
        out["points"] = points
        out["seconds"] = round(time.time() - t0, 1)
        p = os.path.join(args.out, f"{scene}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
        print(f"  WROTE {p} ({out['seconds']}s)  points={json.dumps(points)}", flush=True)


if __name__ == "__main__":
    main()
