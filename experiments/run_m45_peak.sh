#!/usr/bin/env bash
# M45 -- peak RSS and md5 of the split build (M3 + M2).
set -uo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m43
CACHE=/mnt/m35cache
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
cd "$ROOT" || exit 1
for S in bicycle stump bonsai; do
  [ -s "$CACHE/$S.ply" ] || continue
  python3 -u -m tools.m43_ab --ply "$CACHE/$S.ply" --variant m44 --jobs 4 \
    --out "$OUT" --json "$OUT/m45_peak_${S}.json" 2>&1 | tee -a "$OUT/m45_peak.log"
done
echo DONE_M45_PEAK
