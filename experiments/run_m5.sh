#!/usr/bin/env bash
# M5: re-derive the RD axis from measured bytes (zstd + Morton) instead of the model.
# Stage 1 measures every M3 variant on every asset; stage 2 replays the M3 analysis
# with --bytes-json, so E1/E2/E3 are judged on the shipped format, not arithmetic.
set -u
cd /workspace/code || exit 2
ARCH=/workspace/data/out3dgs
OUT=${OUT:-/workspace/res/m5}
DUMP=${DUMP:-/workspace/res/m3/dump}
SCENES=${SCENES:-bicycle,flowers,stump,treehill,bicycle_i7k,flowers_i7k,stump_i7k,treehill_i7k}
SPECS=${SPECS:-clean,p90,p70,p50,p30,p20,p10,p05,m16_o8_sh8,m16_o8_sh6,m16_o8_sh4,m16_o8_sh3,m16_o8_sh2,m16_o6_sh3,m16_o6_sh2,m18_o6_sh3,d2_m16_o8_sh8,d1_m16_o8_sh8,d0_m16_o8_sh8,d2_m16_o8_sh4,d1_m16_o8_sh4}
LEVEL=${LEVEL:-12}
RATES=${RATES:-2,3,5,7,9,12,16,24}
mkdir -p "$OUT"

if [ "${1:-all}" = "bytes" ] || [ "${1:-all}" = "all" ]; then
  python -u experiments/m4_bytes.py \
    --archive "$ARCH" --scenes "$SCENES" --specs "$SPECS" \
    --level "$LEVEL" --skip-flat \
    --out "$OUT/m5_bytes.json" || exit 1
fi

if [ "${1:-all}" = "analyse" ] || [ "${1:-all}" = "all" ]; then
  python -u experiments/m1_analyse.py \
    --dump "$DUMP" --out "$OUT/m5_rd.json" \
    --rates "$RATES" --n-splits 400 \
    --protocol m3 --rate-need 4 \
    --bytes-json "$OUT/m5_bytes.json" || exit 1
fi
echo "=== m5 finished with 0 ==="
