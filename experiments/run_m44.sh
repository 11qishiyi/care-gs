#!/usr/bin/env bash
# M44 -- same three scenes, the current code, one process per encode.
set -uo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m43
CACHE=/mnt/m35cache
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
cd "$ROOT" || exit 1
for S in bicycle stump bonsai; do
  [ -s "$CACHE/$S.ply" ] || continue
  python3 -u -m tools.m43_ab --ply "$CACHE/$S.ply" --variant m44 --jobs 4 \
    --out "$OUT" --json "$OUT/enc_${S}_m44.json" 2>&1 | tee -a "$OUT/ab_m44.log"
done
echo DONE_M44
