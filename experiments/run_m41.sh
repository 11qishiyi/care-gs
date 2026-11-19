#!/usr/bin/env bash
# M41 -- the same container written with 1, 2, 4 and 8 workers, on three scenes.
set -uo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m41
CACHE=/mnt/m35cache
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
mkdir -p "$OUT"
for S in bicycle stump bonsai; do
  [ -s "$CACHE/$S.ply" ] || { echo "no model $S"; continue; }
  "$PY" -u -m experiments.m41_par --ply "$CACHE/$S.ply" --jobs 1,2,4,8 \
    --out "$OUT/$S" --json "$OUT/m41_${S}.json" 2>&1 | tee "$OUT/m41_$S.log"
done
echo DONE_M41