"""J5 packer --- run on the node after `j5_render.py`: cut the magnification patches and the thumbnails so the
pull is a few hundred KB instead of tens of megabytes.

The crop rule is the pre-registered one (`experiments/J5_PLAN.md`): the 200x200 window with the largest ground-truth
gradient energy, searched on a 20-px grid, ties broken top-left. It runs here rather than locally so the full-frame
renders never have to cross the wire, and it runs on the **ground truth** so the codec's output cannot influence
which patch is shown.

    python experiments/j5_pack.py --res /root/res/j5 --out /root/res/j5/pack
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
from PIL import Image

CROP, STRIDE, THUMB_W = 200, 20, 900


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default="/root/res/j5")
    ap.add_argument("--out", default="/root/res/j5/pack")
    args = ap.parse_args()

    man = json.load(open(os.path.join(args.res, "j5_render.json"), encoding="utf-8"))
    os.makedirs(args.out, exist_ok=True)
    out = {"source": "j5_render.json", "crop_px": CROP, "stride": STRIDE,
           "rule": "argmax mean GT gradient energy, ties top-left", "scenes": []}

    for sc in man["scenes"]:
        gt = np.asarray(Image.open(os.path.join(args.res, sc["gt_png"])).convert("RGB"), dtype=np.float32) / 255.0
        g = gt.mean(-1)
        gy, gx = np.gradient(g)
        energy = np.hypot(gy, gx)
        H, W = energy.shape
        best = (-1.0, 0, 0, float(g.std()))
        for y in range(0, max(1, H - CROP) + 1, STRIDE):
            for x in range(0, max(1, W - CROP) + 1, STRIDE):
                patch = g[y:y + CROP, x:x + CROP]
                if patch.std() < 0.02:          # J5-C3: no sky boxes
                    continue
                v = float(energy[y:y + CROP, x:x + CROP].mean())
                if v > best[0]:
                    best = (v, y, x, float(patch.std()))
        e, y, x, sd = best
        if e < 0:
            y = x = 0
            e = float(energy[:CROP, :CROP].mean())
            sd = float(g[:CROP, :CROP].std())
        thumb = Image.fromarray((np.clip(gt, 0, 1) * 255).astype(np.uint8))
        thumb.thumbnail((THUMB_W, THUMB_W * 4), Image.LANCZOS)
        thumb.save(os.path.join(args.out, f"{sc['scene']}_full.jpg"), quality=88)

        arms = {}
        for name, arm in sc["arms"].items():
            img = np.asarray(Image.open(os.path.join(args.res, arm["png"])).convert("RGB"), dtype=np.float32) / 255.0
            patch = (np.clip(img[y:y + CROP, x:x + CROP], 0, 1) * 255 + 0.5).astype(np.uint8)
            fn = f"{sc['scene']}_{name}.png"
            Image.fromarray(patch).save(os.path.join(args.out, fn))
            arms[name] = dict(png=fn, rate=arm["rate"], psnr=arm["psnr"], ssim=arm["ssim"],
                              lpips=arm["lpips"], n_primitives=arm["n_primitives"], family=arm["family"])
        gt_patch = (np.clip(gt[y:y + CROP, x:x + CROP], 0, 1) * 255 + 0.5).astype(np.uint8)
        Image.fromarray(gt_patch).save(os.path.join(args.out, f"{sc['scene']}_gt_patch.png"))
        out["scenes"].append(dict(scene=sc["scene"], view_index=sc["view_index"], view_rank=sc["view_rank"],
                                  n_held_out=sc["n_held_out"], width=sc["width"], height=sc["height"],
                                  crop=dict(y=int(y), x=int(x), size=CROP, gt_energy=round(e, 5),
                                            gt_std=round(sd, 4)),
                                  full=f"{sc['scene']}_full.jpg", arms=arms))
        print(f"{sc['scene']}: crop ({x},{y}) energy {e:.4f} std {sd:.3f}; arms {list(arms)}")

    json.dump(out, open(os.path.join(args.out, "j5_pack.json"), "w", encoding="utf-8"), indent=1)
    print(f"wrote {os.path.join(args.out, 'j5_pack.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
