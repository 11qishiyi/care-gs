#!/usr/bin/env bash
# M7 stage 2: data is already unpacked, so run dump -> measured bytes -> analysis.
set -eu
ROOT=${ROOT:-/workspace/code}
OUT=${OUT:-/workspace/res/m7}
PY=${PY:-python3}
export FIDELITY=0   # no perceptual metrics this round (backbone download is ~10 kB/s)
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
cd "$ROOT"
mkdir -p "$OUT"
SCENES=${SCENES:-bicycle,flowers,stump,treehill,bicycle_i7k,flowers_i7k,stump_i7k,treehill_i7k}
VARIANT_SET=m7 OUT="$OUT" SCENES="$SCENES" bash experiments/run_m1.sh dump
echo "=== dump done ==="
SPECS="clean,p50,p30,p20,p10,p05,m16_o8_sh3,m16_o8_sh4,m16_o8_sh2,c8_o8_sh3,c10_o8_sh3,c12_o8_sh3,c14_o8_sh3,c12_o8_sh4,c12_o8_sh2,c10_o8_sh2,p50_c12_o8_sh3,p30_c10_o8_sh3"
$PY experiments/m4_bytes.py --archive /workspace/data/out3dgs --scenes "$SCENES" \
  --specs "$SPECS" --level 12 --skip-flat --out "$OUT/m7_bytes.json"
echo "=== bytes done ==="
$PY experiments/m1_analyse.py --dump "$OUT/dump" --out "$OUT/m7_rd.json" \
  --rates 2,3,5,7,9,12,16,24 --n-splits 400 --protocol m3 --rate-need 4 \
  --bytes-json "$OUT/m7_bytes.json"
echo "=== analyse done ==="
