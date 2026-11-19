#!/usr/bin/env bash
# M46 -- sequential vs pooled colour search, one host, one process per scene.
set -uo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m46
CACHE=/mnt/m35cache
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
cd "$ROOT" || exit 1
mkdir -p "$OUT"
for S in bicycle stump bonsai; do
  [ -s "$CACHE/$S.ply" ] || { echo "missing $S"; continue; }
  python3 -u -m tools.m46_probe --ply "$CACHE/$S.ply" --jobs 1,2,4 --json "$OUT/m46_${S}.json" 2>&1 | tee -a "$OUT/m46.log"
done
echo DONE_M46
