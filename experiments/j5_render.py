"""J5 --- qualitative render grid: ground truth vs clean vs quantised vs pruned, one fixed view per scene.

The paper's five figures are all quantitative; a JVCIR compression paper normally carries one figure a reader can
*look* at. This round produces it under a protocol fixed in advance (`experiments/J5_PLAN.md`):

  * scene set: the two scenes that are also the cross-paper rows (`bicycle`, `stump`);
  * view: the held-out view whose **clean** PSNR is the median over the held-out views --- a rule, not a choice;
  * arms: `clean`, the shipped container point, one mid-rate container point, and a Fisher prune at the same
    family comparison the paper argues about;
  * crop: chosen afterwards, on the ground-truth image, as the window with the largest gradient energy --- also a
    rule, so the panel that gets magnified is not selected by looking at the failure modes;
  * every number printed here (PSNR/SSIM/LPIPS per arm) is written to `j5_render.json` and the figure script reads
    it back, so the caption cannot drift from the render.

Runs on a node with CUDA + gsplat; reuses `qfp_rd` for the codec so the arms are byte-identical to the tables.

    python experiments/j5_render.py --archive /root/m360std --scenes bicycle,stump \
        --variants clean,gp6-6-6_c8_sh6,gp6-6-6_c8_sh3,p50 --out /root/res/j5 --factor 1 --device cuda
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qfp_rd as Q  # noqa: E402


def _save_png(path: str, rgb: np.ndarray) -> None:
    from PIL import Image
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(np.clip(rgb * 255.0 + 0.5, 0, 255).astype(np.uint8)).save(path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="/root/m360std")
    ap.add_argument("--scenes", default="bicycle,stump")
    ap.add_argument("--variants", default="clean,gp6-6-6_c8_sh6,gp6-6-6_c8_sh3,p50")
    ap.add_argument("--out", default="/root/res/j5")
    ap.add_argument("--factor", type=int, default=1)
    ap.add_argument("--cal-frac", type=float, default=0.5)
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--n-fisher-views", type=int, default=4)
    ap.add_argument("--gt-convention", default="archive", choices=["archive", "normalized"])
    ap.add_argument("--ply-pattern", default="{archive}/output/{scene}/point_cloud/iteration_40000/point_cloud.ply")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--lpips-net", default="alex")
    ap.add_argument("--chunk", type=int, default=4)
    args = ap.parse_args(argv)

    C = Q._C()
    C.add_code_root()
    import torch
    from calib.archive_only import load_archive_only_scene
    from calib.colmap_io import load_images, normalize_exposure
    from calib.gsrender import load_splats
    import dump_artifacts as D

    specs = [Q.parse_spec(v) for v in args.variants.split(",") if v.strip()]
    os.makedirs(args.out, exist_ok=True)
    manifest = {"protocol": "J5_PLAN.md", "factor": args.factor, "gt_convention": args.gt_convention,
                "view_rule": "median clean PSNR over held-out views", "variants": [s.name for s in specs],
                "scenes": []}

    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        t0 = time.time()
        sc = load_archive_only_scene(args.archive, scene, factor=args.factor, cal_frac=args.cal_frac)
        W, H = int(sc["width"]), int(sc["height"])
        _gt = load_images(sc["image_paths"], args.factor, (W, H))
        gt_np = (normalize_exposure(_gt) if args.gt_convention == "normalized" else _gt.astype(np.float32) / 255.0)
        gt = torch.from_numpy(gt_np).float().to(args.device)
        c2w_all = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K_all = torch.from_numpy(sc["Ks"]).to(args.device)
        dep = sorted(int(i) for i in sc["dep_idx"])
        cal = sorted(int(i) for i in sc["cal_idx"])

        ply = args.ply_pattern.format(archive=args.archive, scene=scene)
        base = load_splats(ply, device=args.device)
        deg = base.sh_degree
        st = Q.SceneState(base=base)
        C.log(f"[{C.stamp()}] {scene}: {base.n} primitives, SH {deg}, {len(dep)} held-out views, {W}x{H}")

        # ---- 1. clean render over the held-out views, to apply the view rule
        dep_t = torch.as_tensor(dep, device=args.device)
        c2w_d, K_d = c2w_all[dep_t], K_all[dep_t]
        gt_d = gt[dep_t].permute(0, 3, 1, 2).contiguous()
        cols, _ = Q._render_variant(base, c2w_d, K_d, W, H, chunk=args.chunk)
        gt_hwc = gt_d.permute(0, 2, 3, 1).cpu()
        psnrs = [C.psnr_np(cols[i].numpy(), gt_hwc[i].numpy()) for i in range(len(dep))]
        order = np.argsort(np.asarray(psnrs))
        pick = int(order[len(order) // 2])
        view = dep[pick]
        C.log(f"  view rule: median clean PSNR -> view {view} "
              f"(rank {pick + 1}/{len(dep)}, clean PSNR {psnrs[pick]:.2f} dB, "
              f"range {min(psnrs):.2f}-{max(psnrs):.2f})")

        one = torch.as_tensor([view], device=args.device)
        c2w_1, K_1 = c2w_all[one], K_all[one]
        gt_1_hwc = gt[one].cpu()
        gt_1 = gt[one].permute(0, 3, 1, 2).contiguous()
        gt_png = os.path.join(args.out, "png", f"{scene}_gt.png")
        _save_png(gt_png, gt_1_hwc[0].numpy())

        # ---- 2. one render per arm at that view
        if any(s.keep < 1.0 for s in specs):
            import calib.sensitivity as sens
            st.fisher = sens.sensitivity_scores(base, c2w_all, K_all, gt, cal, W, H,
                                                n_views=args.n_fisher_views, device=args.device)
            C.log("  Fisher scores computed once for the prune arm")

        fid_args = SimpleNamespace(lpips_net=args.lpips_net)
        arms = {}
        for spec in specs:
            t = time.time()
            sp, _ = Q.realize(spec, st, args.device)
            deg_out = spec.out_degree(deg)
            cols1, _ = Q._render_variant(sp, c2w_1, K_1, W, H, chunk=1, sh_degree=deg_out)
            psnr = C.psnr_np(cols1.numpy(), gt_1_hwc.numpy())
            fid = D._fidelity_stats(cols1, gt_1, fid_args)
            png = os.path.join(args.out, "png", f"{scene}_{spec.name}.png")
            _save_png(png, cols1[0].numpy())
            arms[spec.name] = dict(
                png=os.path.relpath(png, args.out), psnr=round(float(psnr), 3),
                ssim=None if fid.get("ssim") is None else round(float(fid["ssim"]), 4),
                lpips=None if fid.get("lpips") is None else round(float(fid["lpips"]), 4),
                rate=round(float(spec.rate_vs_fp32(deg, n_stored=int(sp.n))), 3),
                bytes_per_prim=round(float(spec.bytes_per_prim(deg, n_stored=int(sp.n))), 2),
                n_primitives=int(sp.n), family=spec.family,
                seconds=round(time.time() - t, 1))
            C.log(f"  {spec.name:18s} {arms[spec.name]['rate']:6.2f}x  PSNR {psnr:6.2f}  "
                  f"ssim {arms[spec.name]['ssim']}  lpips {arms[spec.name]['lpips']}")
            if spec.name != "clean":
                del sp
            torch.cuda.empty_cache()

        manifest["scenes"].append(dict(
            scene=scene, width=W, height=H, n_primitives=int(base.n), sh_degree=int(deg),
            view_index=int(view), view_rank=int(pick + 1), n_held_out=len(dep),
            clean_psnr_range=[round(float(min(psnrs)), 2), round(float(max(psnrs)), 2)],
            view_psnr_clean=round(float(psnrs[pick]), 3), gt_png=os.path.relpath(gt_png, args.out),
            arms=arms, seconds=round(time.time() - t0, 1)))
        C.json_dump(os.path.join(args.out, "j5_render.json"), manifest)
        del base, st, cols, gt
        torch.cuda.empty_cache()

    C.json_dump(os.path.join(args.out, "j5_render.json"), manifest)
    C.log(f"[{C.stamp()}] WROTE {os.path.join(args.out, 'j5_render.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
