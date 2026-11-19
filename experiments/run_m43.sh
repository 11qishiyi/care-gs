#!/usr/bin/env bash
# M43 -- three encoder variants on one host, one process each.
set -uo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m43
CACHE=/mnt/m35cache
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
mkdir -p "$OUT"
for S in bicycle stump bonsai; do
  [ -s "$CACHE/$S.ply" ] || continue
  for V in legacy m42 m43; do
    "$PY" -u -m tools.m43_ab --ply "$CACHE/$S.ply" --variant "$V" --jobs 4 \
      --out "$OUT" --json "$OUT/enc_${S}_$V.json" 2>&1 | tee -a "$OUT/ab.log"
  done
done
echo DONE_M43
