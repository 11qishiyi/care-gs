#!/usr/bin/env bash
# Compare two supposedly identical ground-truth sources for one Mip-NeRF 360 view:
#   alexmkwizu/gaussian_training_datasets  images_4  (what the COLMAP mirror ships)
#   nvs-bench/mipnerf360                   images    (full resolution, official held-out)
# If the shipped images_4 is a *second* downsampling (or a different filter), every clean-render
# PSNR against it is depressed by 2-4 dB and the cross-paper comparison is invalid.
#   bash experiments/probe_gt.sh bonsai _DSC9074.JPG
set -euo pipefail
SCENE="${1:?scene}"
NAME="${2:?file name, e.g. _DSC9074.JPG}"
STEM="${NAME%.*}"
mkdir -p /tmp/gtprobe
curl -sSL "https://hf-mirror.com/datasets/alexmkwizu/gaussian_training_datasets/resolve/main/mipnerf360/$SCENE/images_4/$NAME" -o "/tmp/gtprobe/${STEM}_mirror.JPG"
for ext in JPG jpg png; do
  if curl -sSfL "https://hf-mirror.com/datasets/nvs-bench/mipnerf360/resolve/main/$SCENE/images/$STEM.$ext" -o "/tmp/gtprobe/${STEM}_full.$ext"; then
    break
  fi
done
python3 - "$SCENE" "$STEM" <<'PY'
import glob, os, sys
import numpy as np
from PIL import Image
scene, stem = sys.argv[1], sys.argv[2]
mirror = Image.open(f"/tmp/gtprobe/{stem}_mirror.JPG").convert("RGB")
full = Image.open(glob.glob(f"/tmp/gtprobe/{stem}_full.*")[0]).convert("RGB")
print(f"{scene}/{stem}: mirror images_4 {mirror.size}, nvs full {full.size}")
w, h = mirror.size
for filt, name in ((Image.BILINEAR, "bilinear"), (Image.BICUBIC, "bicubic"), (Image.LANCZOS, "lanczos")):
    ref = np.asarray(full.resize((w, h), filt), np.float32) / 255.0
    m = np.asarray(mirror, np.float32) / 255.0
    mse = float(((ref - m) ** 2).mean())
    print(f"  full/{name} -> {w}x{h} vs shipped images_4: PSNR {10*np.log10(1/max(mse,1e-12)):6.2f} dB  "
          f"mean|diff| {float(np.abs(ref-m).mean()):.4f}")
PY
