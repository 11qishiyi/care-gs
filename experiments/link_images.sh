#!/usr/bin/env bash
# train_gs.py loads <scene>/images at factor 1; the mirrors ship images_4, so link it.
set -u
for s in bicycle bonsai counter garden kitchen room stump; do
  d=/workspace/data/mip360_colmap/$s
  if [ -d "$d/images_4" ] && [ ! -e "$d/images" ]; then
    ln -s "$d/images_4" "$d/images" && echo "linked $s"
  fi
done