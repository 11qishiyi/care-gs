#!/usr/bin/env bash
# M52/M53 probe -- the same render path as probe_render.sh, without --fidelity.
#   PSNR only (no 528 MB VGG download); `tail` is avoided because this image's shell wrapper
#   rejects options like `tail -4` ("option used in invalid context").
set -euo pipefail
SCENE="${1:?scene}"
FACTOR="${2:-1}"
VARIANT="${3:-clean}"
cd /workspace/code
export PYTHONPATH=/workspace/code/research/code:/workspace/code:/workspace/code/experiments
python3 -u experiments/qfp_rd.py \
  --archive /workspace/data/m360std --out "/workspace/res/m53/probe_f${FACTOR}" \
  --scenes "$SCENE" --variants "$VARIANT" --factor "$FACTOR" \
  --cal-frac 0.5 --alpha 0.1 --n-fisher-views 2 --gt-convention archive \
  --downsample 1 --budget-mb 900 --device cuda 2>&1 | grep -E "PSNR="
