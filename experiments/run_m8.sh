#!/usr/bin/env bash
# M8 round: the high-rate corner (band truncation + cluster positions).
#   bash experiments/run_m8.sh
set -eu
ROOT=${ROOT:-/workspace/code}
OUT=${OUT:-/workspace/res/m8}
PY=${PY:-python3}
export FIDELITY=0
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
cd "$ROOT"
mkdir -p "$OUT"
SCENES=${SCENES:-bicycle,flowers,stump,treehill,bicycle_i7k,flowers_i7k,stump_i7k,treehill_i7k}
VARIANT_SET=m8 OUT="$OUT" SCENES="$SCENES" bash experiments/run_m1.sh dump
echo "=== m8 dump done ==="
SPECS="clean,p30,p20,p10,p05,c8_o8_sh3,c10_o8_sh3,c12_o8_sh2,d1_c8_o8_sh4,d1_c10_o8_sh4,d1_c8_o8_sh5,d2_c8_o8_sh4,d2_c10_o8_sh3,d1_c12_o8_sh4,p50_d1_c8_o8_sh4"
$PY experiments/m4_bytes.py --archive /workspace/data/out3dgs --scenes "$SCENES" \
  --specs "$SPECS" --level 12 --skip-flat --out "$OUT/m8_bytes.json"
echo "=== m8 bytes done ==="
$PY experiments/m1_analyse.py --dump "$OUT/dump" --out "$OUT/m8_rd.json" \
  --rates 2,3,5,7,9,12,16,24 --n-splits 400 --protocol m3 --rate-need 4 \
  --bytes-json "$OUT/m8_bytes.json"
echo "=== m8 analyse done ==="
