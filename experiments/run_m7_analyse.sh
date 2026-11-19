#!/usr/bin/env bash
# M7 CPU analysis on the complete 8-asset dump, then the H1/H2/H3 report inputs.
set -eu
ROOT=${ROOT:-/workspace/code}
OUT=${OUT:-/workspace/res/m7}
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
cd "$ROOT"
python3 experiments/m1_analyse.py --dump "$OUT/dump" --out "$OUT/m7_rd.json" \
  --rates 2,3,5,7,9,12,16,24 --n-splits 400 --protocol m3 --rate-need 4 \
  --bytes-json "$OUT/m7_bytes.json"
echo "=== analyse done ==="
gzip -9 -c "$OUT/m7_rd.json" | wc -c
gzip -9 -c "$OUT/m7_bytes.json" | wc -c
