#!/usr/bin/env bash
set -euo pipefail
ROOT=${ROOT:-/workspace/code}
OUT=${OUT:-/workspace/res/frontier_i7k}
PY=${PY:-python3}
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
"$PY" -u "$ROOT/experiments/m1_analyse.py" \
  --dump "$OUT/dump" --out "$OUT/m13_i7k.json" \
  --bytes-json "$OUT/i7k_bytes.json" \
  --rates 1,2,3,5,7,9,12,16 --n-splits 400 --protocol m3 --rate-need 2 2>&1 | tail -40
