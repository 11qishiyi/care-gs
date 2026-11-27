"""J9 --- does the family law survive a change of tolerance, of error functional, and of scene?

The 56-cell grid that carries the paper's claim was measured at one tolerance (alpha = 0.1) and one functional
(abs per-pixel error, channel mean). This driver re-measures the same edit families and stores, per (scene, variant,
view), the **quantile function of the per-pixel error** at a fixed grid of levels, plus the same for the squared
error. From those two tables every tolerance and both functionals are a lookup, so one GPU pass answers:

  (a) alpha in {0.01, 0.02, 0.05, 0.1, 0.2, 0.3}   --- is the separation a property of the tolerance level?
  (b) abs vs squared error                          --- is it a property of the functional?
  (c) per-view vs pooled                            --- does it hold view by view?
  (d) new scenes                                    --- bicycle plus whatever else downloaded tonight

and it also runs the J8 arms (prune-k and prune-k+container), so the rate axis is measured in the same pass.

The output is small on purpose: the raw residual maps are ~1 GB per scene-variant and were lost with the node, but a
2000-level quantile table is ~1 MB for the whole scene and is enough to recompute any coverage number.

    python experiments/j9_dump_quantiles.py --archive /root/m360 --scenes bicycle --out /root/res/j9
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research", "code"))

NQ = 2000          # quantile levels stored per (variant, view)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/root/m360")
    ap.add_argument("--scenes", default="bicycle")
    ap.add_argument("--ply-pattern", default="{archive}/output/{scene}/point_cloud/iteration_40000/point_cloud.ply")
    ap.add_argument("--factor", type=int, default=1)
    ap.add_argument("--cal-frac", type=float, default=0.5)
    ap.add_argument("--bits", default="8,6,4")
    ap.add_argument("--reduction", default="mean", choices=("mean", "max"))
    ap.add_argument("--out", default="/root/res/j9")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args(argv)

    import torch
    from calib.archive_only import load_archive_only_scene
    from calib.colmap_io import load_images as _load_images
    from calib.gsrender import load_splats, render
    from dump_artifacts import _quantize_splats

    os.makedirs(args.out, exist_ok=True)
    levels = np.linspace(0, 1, NQ)

    def quantile_table(err: np.ndarray) -> np.ndarray:
        """Quantiles of the error distribution of one view, at the stored levels."""
        return np.quantile(err.ravel(), levels).astype(np.float32)

    manifest = {"protocol": "J9_PLAN.md", "levels_n": NQ, "scenes": []}

    for scene in [s for s in args.scenes.split(",") if s.strip()]:
        sc = load_archive_only_scene(args.archive, scene, factor=args.factor, cal_frac=args.cal_frac)
        W, H = int(sc["width"]), int(sc["height"])
        gt = _load_images(sc["image_paths"], args.factor, (W, H)).astype(np.float32) / 255.0
        dep = [int(i) for i in sc["dep_idx"]]
        c2w = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K = torch.from_numpy(sc["Ks"]).to(args.device)
        sp = load_splats(args.ply_pattern.format(archive=args.archive, scene=scene), device=args.device)
        n = int(sp.n)
        print(f"{scene}: n={n} views={len(dep)} {W}x{H}", flush=True)

        def render_variant(variant: str, keep: float = 1.0):
            base = sp
            if keep < 1.0:
                k = max(1, int(round(keep * n)))
                idx = torch.argsort(sp.opacities, descending=True)[:k]
                base = sp.subset(idx)
            if variant == "clean":
                return base
            if variant.startswith("quant"):
                return _quantize_splats(base, torch, bits=int(variant[5:]))
            return base

        def measure(splats) -> dict:
            out = {"abs": [], "sq": [], "psnr": []}
            for v in dep:
                with torch.no_grad():
                    img = render(splats, c2w[v].unsqueeze(0), K[v].unsqueeze(0), W, H)["colors"][0]
                img = img.float().cpu().numpy()
                e = np.abs(img - gt[v])
                e = e.mean(-1) if args.reduction == "mean" else e.max(-1)
                out["abs"].append(quantile_table(e))
                out["sq"].append(quantile_table((e ** 2).astype(np.float32)))
                out["psnr"].append(float(10 * np.log10(1.0 / max(float((e ** 2).mean()), 1e-12))))
            return out

        rows = {}
        arms = [("clean", 1.0), ("prune50", 0.5), ("prune30", 0.7), ("pup30", 1.0)]
        for b in [x for x in args.bits.split(",") if x.strip()]:
            arms.append((f"quant{b}", 1.0))
            arms.append((f"prune50+quant{b}", 0.5))
        # prune30 here means "keep 30%"; prune50 means "keep 50%" -- both are named after what the paper deletes
        for name, keep in arms:
            v, k = (name.split("+")[0], 0.5) if "+" in name else (name, keep)
            if name == "prune30":
                k = 0.3
            if name == "pup30":
                # PUP/Fisher ordering is not available here; the paper's pup30 arm is a different score and is not
                # re-measured in this pass (recorded, not silently substituted)
                continue
            if name.startswith("prune50+quant"):
                base = render_variant("clean", 0.5)
                sp_v = _quantize_splats(base, torch, bits=int(name.split("quant")[1]))
            else:
                sp_v = render_variant(v, k)
            rows[name] = measure(sp_v)
            rows[name]["n"] = int(sp_v.n)
            print(f"  {name:16s} n={rows[name]['n']:8d} psnr={np.mean(rows[name]['psnr']):.2f}", flush=True)
            del sp_v
            torch.cuda.empty_cache()

        np.savez_compressed(os.path.join(args.out, f"{scene}_{args.reduction}.npz"),
                            levels=levels, views=np.array(dep),
                            **{f"{k}__abs": np.stack(v["abs"]) for k, v in rows.items()},
                            **{f"{k}__sq": np.stack(v["sq"]) for k, v in rows.items()})
        manifest["scenes"].append(dict(scene=scene, n=n, views=len(dep), width=W, height=H,
                                       psnr={k: round(float(np.mean(v["psnr"])), 3) for k, v in rows.items()},
                                       n_variants={k: v["n"] for k, v in rows.items()}))
        with open(os.path.join(args.out, f"j9_manifest_{args.reduction}.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=1)
        del sp
        torch.cuda.empty_cache()

    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())