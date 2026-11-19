#!/usr/bin/env bash
# Dump the four iteration-7000 twins (they were not in the first pass).
set -u
cd /workspace/code
export FIDELITY=0
export PYTHONPATH="/workspace/code/research/code:/workspace/code:/workspace/code/experiments"
OUT=${OUT:-/workspace/res/m7}
for s in bicycle_i7k flowers_i7k stump_i7k treehill_i7k; do
  echo "=== $s ==="
  python3 experiments/qfp_rd.py \
    --archive /workspace/data/out3dgs \
    --out "$OUT/dump" \
    --scenes "$s" \
    --device cuda \
    --variant-set m7 \
    --factor 4 --gt-convention archive --downsample 1 --budget-mb 900
done
echo "I7K_DUMP_DONE"
