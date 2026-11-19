#!/usr/bin/env bash
# M45 -- alphabet-search phase, both ways, one host, one process per scene.
set -uo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m43
CACHE=/mnt/m35cache
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
cd "$ROOT" || exit 1
mkdir -p "$OUT"
for S in bicycle stump bonsai; do
  [ -s "$CACHE/$S.ply" ] || { echo "missing $S"; continue; }
  python3 -u -m tools.m45_probe --ply "$CACHE/$S.ply" --json "$OUT/m45_${S}.json" 2>&1 | tee -a "$OUT/m45.log"
done
echo DONE_M45
