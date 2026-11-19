"""Fetch a released 30k-iteration checkpoint plus its held-out ground truth from HF mirrors.

Source layout (HF dataset ``dylanebert/3dgs``): standard INRIA output tree
``<scene>/cameras.json`` and ``<scene>/point_cloud/iteration_30000/point_cloud.ply``.
Ground-truth images come from ``nvs-bench/mipnerf360`` (``<scene>/images/*.JPG``), which is
the same capture the checkpoints were trained on.  Set HF_ENDPOINT to a mirror if huggingface.co is slow from your network.  Only the
held-out views are downloaded:
cameras sorted by image name, every eighth is a test view (llffhold = 8, as in 3DGS).

    python experiments/fetch_hf_data.py --scenes bicycle,bonsai \
        --models /workspace/data/models --images /workspace/data/mip360
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

HF = "https://huggingface.co/datasets/dylanebert/3dgs/resolve/main"
NB = "https://huggingface.co/datasets/nvs-bench/mipnerf360/resolve/main"


def get(url: str, dst: str, retries: int = 3) -> bool:
    if os.path.isfile(dst) and os.path.getsize(dst) > 0:
        return True
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=120) as r, open(dst + ".part", "wb") as f:
                while True:
                    buf = r.read(1 << 20)
                    if not buf:
                        break
                    f.write(buf)
            os.replace(dst + ".part", dst)
            return True
        except Exception as e:                                   # noqa: BLE001
            print(f"    retry {k + 1}/{retries} {os.path.basename(dst)}: {e}", flush=True)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", default="bicycle,bonsai")
    ap.add_argument("--models", default="/workspace/data/models")
    ap.add_argument("--images", default="/workspace/data/mip360")
    ap.add_argument("--llffhold", type=int, default=8)
    ap.add_argument("--skip-ply", action="store_true")
    args = ap.parse_args()

    for scene in [s.strip() for s in args.scenes.split(",") if s.strip()]:
        base = os.path.join(args.models, "output", scene)
        os.makedirs(base, exist_ok=True)
        if not get(f"{HF}/{scene}/cameras.json", os.path.join(base, "cameras.json")):
            print(f"[{scene}] cameras.json FAILED")
            continue
        cams = json.load(open(os.path.join(base, "cameras.json"), encoding="utf-8"))
        cams.sort(key=lambda c: c["img_name"])
        print(f"[{scene}] {len(cams)} cameras, first={cams[0]['img_name']} "
              f"{cams[0]['width']}x{cams[0]['height']}", flush=True)

        if not args.skip_ply:
            ply = os.path.join(base, "point_cloud", "iteration_30000", "point_cloud.ply")
            print(f"[{scene}] downloading checkpoint -> {ply}", flush=True)
            if not get(f"{HF}/{scene}/point_cloud/iteration_30000/point_cloud.ply", ply):
                print(f"[{scene}] checkpoint FAILED")
                continue
            print(f"[{scene}] checkpoint {os.path.getsize(ply) / 1e6:.0f} MB", flush=True)

        test = [cams[i] for i in range(len(cams)) if i % args.llffhold == 0]
        ok = 0
        for c in test:
            stem = os.path.splitext(os.path.basename(c["img_name"]))[0]
            dst_dir = os.path.join(args.images, scene, "images")
            done = False
            for ext in (".JPG", ".jpg", ".png"):
                dst = os.path.join(dst_dir, stem + ext)
                if get(f"{NB}/{scene}/images/{stem}{ext}", dst, retries=1):
                    ok += 1
                    done = True
                    break
            if not done:
                print(f"    missing image {stem}", flush=True)
        print(f"[{scene}] ground-truth test views: {ok}/{len(test)}", flush=True)

    print("FETCH_DONE")


if __name__ == "__main__":
    main()
