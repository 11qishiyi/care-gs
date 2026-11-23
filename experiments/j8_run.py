"""J8 --- give pruning the same encoder, then ask whether the action-family asymmetry survives.

Referee A's objection to Fig. 2 and Table 5: the pruning arms are measured as *deleted primitives, unencoded*
(205-207 B/primitive, i.e. fp32 attributes plus zstd), while the quantisation arms go through the container
(13.6-56 B/primitive). The rate of a pruning arm is therefore `1.14 / keep` --- almost all of its "compression" is the
deletion itself. The claim that the pruning family has no admissible configuration may be a statement about the
missing encoder rather than about the action.

This driver encodes **both** families with the same container at the same operating points:

    quant-only        uniform 8-bit attributes on the full model          rate ~= bpp8 * n
    prune-k only      opacity top-k, unencoded (the paper's current arm)   rate ~= 1.14 / k
    prune-k + cont.   opacity top-k, then 8-bit attributes                 rate ~= bpp8 * k * n

and renders all of them on the same deployment views under the same shipped quantile q, so the three families land on
one (rate, coverage-loss) plane. The pre-registered reading is in experiments/J8_PLAN.md.

    python experiments/j8_run.py --archive /root/m360std --scenes bicycle,stump --keeps 1.0,0.9,0.7,0.5 \
        --bits 8 --out /root/res/j8
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research", "code"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/root/m360std")
    ap.add_argument("--scenes", default="bicycle,stump")
    ap.add_argument("--ply-pattern", default="{archive}/output/{scene}/point_cloud/iteration_40000/point_cloud.ply")
    ap.add_argument("--factor", type=int, default=1)
    ap.add_argument("--cal-frac", type=float, default=0.5)
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--keeps", default="1.0,0.9,0.7,0.5")
    ap.add_argument("--bits", type=int, default=8)
    ap.add_argument("--bpp8", type=float, default=0.0,
                    help="container bytes per primitive at this bit depth; 0 = measure it with the packer")
    ap.add_argument("--out", default="/root/res/j8")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args(argv)

    import torch
    from calib.archive_only import load_archive_only_scene
    from calib.colmap_io import load_images
    from calib.gsrender import load_splats

    # the container's own quantiser, so "the same encoder" means literally the same code
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from dump_artifacts import _quantize_splats  # noqa: PLC0415

    os.makedirs(args.out, exist_ok=True)
    keeps = [float(x) for x in args.keeps.split(",")]
    manifest = {"protocol": "J8_PLAN.md", "bits": args.bits, "alpha": args.alpha, "scenes": []}

    def render(sp, c2w, K, W, H):
        from calib.gsrender import render
        with torch.no_grad():
            out = render(sp, c2w.unsqueeze(0), K.unsqueeze(0), W, H)
        return out["colors"][0].float().cpu().numpy()

    for scene in [s for s in args.scenes.split(",") if s.strip()]:
        sc = load_archive_only_scene(args.archive, scene, factor=args.factor, cal_frac=args.cal_frac)
        W, H = int(sc["width"]), int(sc["height"])
        gt = load_images(sc["image_paths"], args.factor, (W, H)).astype(np.float32) / 255.0
        dep = [int(i) for i in sc["dep_idx"]]
        c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K = torch.from_numpy(sc["Ks"]).to(args.device)
        sp = load_splats(args.ply_pattern.format(archive=args.archive, scene=scene), device=args.device)
        n = int(sp.n)

        # the shipped quantile: calibrate on the clean model, then never move it (§3.2 of the paper)
        resid = []
        for v in dep:
            img = render(sp, c2w[v], K[v], W, H)
            resid.append(np.abs(img - gt[v]).mean(-1))
        q = float(np.quantile(np.concatenate([r.ravel() for r in resid]), 1 - args.alpha))
        clean_cov = float(np.mean([(r <= q).mean() for r in resid]))
        clean_psnr = float(np.mean([10 * np.log10(1.0 / max((r ** 2).mean(), 1e-12)) for r in resid]))
        print(f"{scene}: q={q:.5f} clean_cov={clean_cov:.4f} clean_psnr={clean_psnr:.2f} n={n}")

        rows = []
        for keep in keeps:
            idx = None
            if keep < 1.0:
                # opacity top-k, the paper's baseline pruning rule
                k = max(1, int(round(keep * n)))
                idx = torch.argsort(sp.opacities, descending=True)[:k]
            base = sp if idx is None else sp.subset(idx)
            n_pr = int(base.n)

            for arm in ("prune-only", "prune+container"):
                if arm == "prune-only" and keep < 1.0 and keep > 0:
                    # unencoded: the current paper arm, included so both are measured in the same run
                    covs, psnrs = [], []
                    for v in dep:
                        img = render(base, c2w[v], K[v], W, H)
                        r = np.abs(img - gt[v]).mean(-1)
                        covs.append(float((r <= q).mean()))
                        psnrs.append(float(10 * np.log10(1.0 / max((r ** 2).mean(), 1e-12))))
                else:
                    quant = _quantize_splats(base, torch, bits=args.bits)
                    covs, psnrs = [], []
                    for v in dep:
                        img = render(quant, c2w[v], K[v], W, H)
                        r = np.abs(img - gt[v]).mean(-1)
                        covs.append(float((r <= q).mean()))
                        psnrs.append(float(10 * np.log10(1.0 / max((r ** 2).mean(), 1e-12))))
                    del quant
                cov = float(np.mean(covs))
                # rate against the fp32 asset; an encoded arm is charged the container's own bytes per primitive,
                # so pruning pays the same per-primitive price that quantisation does
                fp32_bytes = 236.0 * n
                bpp = args.bpp8 if (arm == "prune+container" or keep == 1.0) else 205.7
                rate = fp32_bytes / max(n_pr * bpp, 1.0)
                rows.append(dict(keep=keep, arm=arm, n_primitives=n_pr, rate=round(rate, 2), bpp=bpp,
                                 coverage=round(cov, 4), loss_pp=round(100 * (clean_cov - cov), 2),
                                 psnr=round(float(np.mean(psnrs)), 3)))
                print(f"  keep={keep:.1f} {arm:16s} n={n_pr:8d} rate={rate:6.2f}x cov={cov:.4f} "
                      f"loss={100 * (clean_cov - cov):+6.2f}pp psnr={np.mean(psnrs):.2f}")
                del base
                torch.cuda.empty_cache()

        manifest["scenes"].append(dict(scene=scene, q=round(q, 5), clean_coverage=round(clean_cov, 4),
                                      clean_psnr=round(clean_psnr, 2), n_primitives=n, rows=rows))
        with open(os.path.join(args.out, "j8.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=1)
        del sp
        torch.cuda.empty_cache()

    print(f"wrote {os.path.join(args.out, 'j8.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
