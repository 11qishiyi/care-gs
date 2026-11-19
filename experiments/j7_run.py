"""J7 driver --- prune by a coverage-aware score and measure what the certificate does.

For each scene and each keep rate, three rankings are compared on the *same* checkpoint and the same container:

    opacity        the published `prune50` rule (alpha, descending)
    fisher         the PUP diagonal, if a compatible field is present (else skipped)
    coverage-risk  `experiments/j7_score.py`: alpha * footprint * closeness-to-q

Each arm is rendered on the held-out views and scored by (a) coverage at the *clean* model's shipped quantile q and
(b) PSNR. The pre-registered criterion (`experiments/J7_PLAN.md`): at a matched keep rate the coverage-aware arm must
keep at least 30% more coverage than the opacity arm, on at least 4 of 6 (scene, keep) cells. A smaller gain is
reported as "the score is not the reason" and strengthens the paper's claim instead.

Needs CUDA (gsplat) and the Mip-NeRF 360 archives; it does not touch `dump_artifacts.py`, whose numbers are frozen.

    python experiments/j7_run.py --archive /root/m360std --scenes bicycle --q 0.0891 \
        --keeps 0.9,0.7,0.5 --out /root/res/j7
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research", "code"))

from j7_score import alpha_area, coverage_risk, select  # noqa: E402


def render_view(sp, c2w, K, W, H, device):
    import torch
    from calib.gsrender import render
    with torch.no_grad():
        out = render(sp, c2w.unsqueeze(0), K.unsqueeze(0), W, H)
    return out["colors"][0].float().cpu().numpy()


def score_coverage(colors, gts, q):
    resid = np.abs(colors - gts).mean(-1)
    return float((resid <= q).mean())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/root/m360std")
    ap.add_argument("--scenes", default="bicycle")
    ap.add_argument("--ply-pattern", default="{archive}/output/{scene}/point_cloud/iteration_40000/point_cloud.ply")
    ap.add_argument("--factor", type=int, default=1)
    ap.add_argument("--cal-frac", type=float, default=0.5)
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--keeps", default="0.9,0.7,0.5")
    ap.add_argument("--out", default="/root/res/j7")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args(argv)

    import torch
    from calib.archive_only import load_archive_only_scene
    from calib.colmap_io import load_images
    from calib.gsrender import load_splats

    os.makedirs(args.out, exist_ok=True)
    keeps = [float(x) for x in args.keeps.split(",")]
    manifest = {"protocol": "J7_PLAN.md", "alpha": args.alpha, "keeps": keeps, "scenes": []}

    for scene in [s for s in args.scenes.split(",") if s.strip()]:
        sc = load_archive_only_scene(args.archive, scene, factor=args.factor, cal_frac=args.cal_frac)
        W, H = int(sc["width"]), int(sc["height"])
        gt = load_images(sc["image_paths"], args.factor, (W, H)).astype(np.float32) / 255.0
        dep = [int(i) for i in sc["dep_idx"]]
        c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K = torch.from_numpy(sc["Ks"]).to(args.device)
        sp = load_splats(args.ply_pattern.format(archive=args.archive, scene=scene), device=args.device)

        # clean render -> residual map on the first held-out view, and the shipped quantile q
        resid_by_view = {}
        for v in dep:
            img = render_view(sp, c2w[v], K[v], W, H, args.device)
            resid_by_view[v] = np.abs(img - gt[v]).mean(-1)
        pooled = np.concatenate([r.ravel() for r in resid_by_view.values()])
        q = float(np.quantile(pooled, 1 - args.alpha))
        clean_cov = float(np.mean([(r <= q).mean() for r in resid_by_view.values()]))

        rows = []
        for keep in keeps:
            scores = {
                "opacity": sp.opacities.detach().float().cpu().numpy(),
                "coverage-risk": coverage_risk(
                    sp.means.detach().float().cpu().numpy(),
                    sp.scales.detach().float().cpu().numpy(),
                    sp.opacities.detach().float().cpu().numpy(),
                    sc["camtoworlds"][dep[0]], sc["Ks"][dep[0]], resid_by_view[dep[0]], q),
                "alpha-area": alpha_area(
                    sp.means.detach().float().cpu().numpy(),
                    sp.scales.detach().float().cpu().numpy(),
                    sp.opacities.detach().float().cpu().numpy(),
                    sc["camtoworlds"][dep[0]], sc["Ks"][dep[0]]),
            }
            for name, sc_vec in scores.items():
                idx = torch.as_tensor(select(np.asarray(sc_vec), keep), device=args.device)
                sub = sp.subset(idx)
                covs = []
                for v in dep:
                    img = render_view(sub, c2w[v], K[v], W, H, args.device)
                    covs.append(float((np.abs(img - gt[v]).mean(-1) <= q).mean()))
                rows.append(dict(keep=keep, score=name, n_primitives=int(sub.n),
                                 coverage=round(float(np.mean(covs)), 4),
                                 coverage_min=round(float(np.min(covs)), 4),
                                 loss_pp=round(100 * (clean_cov - float(np.mean(covs))), 2)))
                print(f"  {scene} keep={keep} {name:14s} cov={np.mean(covs):.4f} "
                      f"loss={100 * (clean_cov - np.mean(covs)):+.2f}pp")
                del sub
                torch.cuda.empty_cache()

        manifest["scenes"].append(dict(scene=scene, q=round(q, 5), clean_coverage=round(clean_cov, 4),
                                       n_primitives=int(sp.n), rows=rows))
        with open(os.path.join(args.out, "j7.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=1)
        del sp
        torch.cuda.empty_cache()

    print(f"wrote {os.path.join(args.out, 'j7.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
