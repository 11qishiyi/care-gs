#!/usr/bin/env bash
# Render the four M19 attribute-swap hybrids.
set -euo pipefail
cd /workspace/code
export PYTHONPATH=/workspace/code/research/code:/workspace/code:/workspace/code/experiments
COL=/workspace/data/mip360_colmap/bicycle
python3 -u experiments/m19_swap.py \
  /workspace/data/m360std/output/bicycle/point_cloud/iteration_40000/point_cloud.ply \
  /workspace/res/m19/models/bicycle_c10_o8_sh3.ply /workspace/res/m19/swap
for f in means scales quats opacities; do
  rm -rf "/workspace/data/m360std/output/bicycle_sw_$f"
  python3 experiments/make_m360_archive.py --scene-dir "$COL" \
    --ply "/workspace/res/m19/swap/swap_$f.ply" --archive /workspace/data/m360std \
    --name "bicycle_sw_$f" 2>&1 | tail -1
  bash experiments/probe_render.sh "bicycle_sw_$f" 1 2>&1 | tail -1
done
echo SWAP_DONE
