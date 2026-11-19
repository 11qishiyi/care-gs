#!/usr/bin/env bash
# M3 analysis on the node (CPU): 8 assets x 21 variants, 400 splits.
# Protocol m3 = E1/E2/E3 (METHOD_PLAN.md M3.4 + M3.4a).  The rate grid is the full
# M1/M2 grid so the RD table is comparable across rounds; E1 only counts the rates
# the two curves actually share (2x and 16x have no QFP/prune pair).
set -u
cd /workspace/code || exit 2
OUT=${OUT:-/workspace/res/m3}
RATES=${RATES:-2,3,5,7,9,12,16,24}
python -u experiments/m1_analyse.py \
  --dump "$OUT/dump" \
  --out "$OUT/m3_rd.json" \
  --rates "$RATES" \
  --n-splits 400 \
  --protocol m3 \
  --rate-need 4
echo "=== analyse finished with $? ==="
