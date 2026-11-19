#!/usr/bin/env bash
# Sparse + images for bicycle/stump, in the order the archive builder needs them.
#
# `j5_fix_images2.sh` derives the image list from COLMAP's `images.bin`, so the sparse files have to exist first;
# in the J5 round they were downloaded by a different stage. This script fetches the three sparse files, then
# delegates the images to that script (32-way, size-checked).
#
#   bash experiments/j6_fetch_sparse_images.sh
set -uo pipefail
cd /root/j6
export PYTHONPATH=/root/j6:/root/j6/research/code
MIR="${MIR:-https://hf-mirror.com/datasets}"
IMGREPO="$MIR/alexmkwizu/gaussian_training_datasets/resolve/main/mipnerf360"
DATA=/root/mip360
log() { echo "[$(date +%H:%M:%S)] $*"; }

for s in bicycle stump; do
  d="$DATA/$s"
  mkdir -p "$d/sparse/0" "$d/images_4"
  for f in cameras.bin images.bin points3D.bin; do
    if [ -s "$d/sparse/0/$f" ]; then
      log "$s/$f cached $(stat -c %s "$d/sparse/0/$f") B"
      continue
    fi
    curl -sSL --retry 5 --max-time 600 -o "$d/sparse/0/$f" "$IMGREPO/$s/sparse/0/$f" \
      && log "$s/$f $(stat -c %s "$d/sparse/0/$f") B" || log "$s/$f FAILED"
  done
done

log "images"
bash experiments/j5_fix_images2.sh
log "done"
