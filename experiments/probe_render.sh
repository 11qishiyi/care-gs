#!/usr/bin/env bash
# Diagnostic: render one variant of one archive entry at a given factor and print the PSNR.
#   bash experiments/probe_render.sh <scene> <factor> [variant]
set -euo pipefail
SCENE="${1:?scene}"
FACTOR="${2:-4}"
VARIANT="${3:-clean}"
cd /workspace/code
export PYTHONPATH=/workspace/code/research/code:/workspace/code:/workspace/code/experiments
python3 -u experiments/qfp_rd.py \
  --archive /workspace/data/m360std --out "/workspace/res/m16/probe_f${FACTOR}" \
  --scenes "$SCENE" --variants "$VARIANT" --factor "$FACTOR" \
  --cal-frac 0.5 --alpha 0.1 --n-fisher-views 2 --gt-convention archive \
  --downsample 1 --budget-mb 900 --device cuda --fidelity --lpips-net vgg 2>&1 \
  | grep -E "primitives|PSNR=" | tail -4
