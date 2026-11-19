#!/usr/bin/env bash
# Second pass over the M17 pilot: the first dump wrote five compressed variants and no `clean`
# row, and m1_analyse needs the uncompressed render on the same splits to define drop_pp (it
# stopped with `ValueError: 'clean' is not in list`).  Every byte measurement is already done, so
# this pass only re-renders, then analyses and reports.
set -uo pipefail
cd /workspace/code
OUT=/workspace/res/m17
ARCH=/workspace/data/m360std
VARS="clean,vq12_c8_o8,c8_o8_sh3,c10_o8_sh3,m16_o8_sh2,msc12-6-a1_c8_o8"
export PYTHONPATH=/workspace/code/research/code:/workspace/code:/workspace/code/experiments

for sc in bicycle bicycle_k50l3_ft bicycle_k35l3_ft bicycle_k50l3_pre bicycle_k35l3_pre \
          bicycle_k50_pre bicycle_k35_pre; do
  echo "[$(date +%H:%M:%S)] dump $sc"
  python3 -u experiments/qfp_rd.py \
    --archive "$ARCH" --out "$OUT/dump" --scenes "$sc" --variants "$VARS" \
    --factor 1 --cal-frac 0.5 --alpha 0.1 --n-fisher-views 4 \
    --gt-convention archive --downsample 1 --budget-mb 900 --device cuda \
    --fidelity --lpips-net vgg > "$OUT/dump_$sc.log" 2>&1
  echo "[$(date +%H:%M:%S)] dump $sc exit $? ($(grep -c PSNR= "$OUT/dump_$sc.log") rows)"
done

python3 -u experiments/m1_analyse.py --dump "$OUT/dump" --out "$OUT/m17_rd.json" \
  --bytes-json "$OUT/m17_bytes.json" \
  --rates 1,2,3,5,7,9,12,16,24,40,60 --n-splits 400 --protocol m3 --rate-need 3
python3 -u experiments/m17_report.py --rd "$OUT/m17_rd.json" --bytes "$OUT/m17_bytes.json" \
  --out "$OUT/m17_report.md" --json "$OUT/m17_report.json"
echo "M17_PASS2_DONE"
