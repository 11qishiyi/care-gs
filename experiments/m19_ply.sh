#!/usr/bin/env bash
# Regenerate the decoded PLYs from the containers with the *current* codec, then render them.
# M19 roll: the first pass wrote PLYs with a decoder that had an off-by-half-range SH offset, and the
# archive hard-links its PLY, so a stale file survives a re-encode and renders at 10 dB.
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m19
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
for spec in ${SPECS:-c10_o8_sh3 c8_o8_sh3 vq12_c8_o8}; do
  gs1="$OUT/models/bicycle_${spec}.gs1"
  [ -s "$gs1" ] || { echo "MISSING $gs1"; continue; }
  python3 -u experiments/m19_codec.py --to-ply "$gs1" --out "$OUT/models/bicycle_${spec}.ply" | tail -1
done
echo PLYS_DONE
