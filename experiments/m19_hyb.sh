#!/usr/bin/env bash
# Render the two M19 hybrids: decoded geometry + reference colour, and the reverse.
set -euo pipefail
cd /workspace/code
COL=/workspace/data/mip360_colmap/bicycle
for n in geo_dec_col_ref geo_ref_col_dec; do
  rm -rf "/workspace/data/m360std/output/bicycle_hyb_$n"
  python3 experiments/make_m360_archive.py --scene-dir "$COL" \
    --ply "/workspace/res/m19/hyb/$n.ply" --archive /workspace/data/m360std \
    --name "bicycle_hyb_$n" 2>&1 | tail -1
  bash experiments/probe_render.sh "bicycle_hyb_$n" 1 2>&1 | tail -1
done
