#!/usr/bin/env bash
# M42 -- old against new on the same node: peak RSS, wall clock, and the md5 both must share.
set -uo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m42
CACHE=/mnt/m35cache
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
mkdir -p "$OUT"
for S in bicycle stump bonsai; do
  [ -s "$CACHE/$S.ply" ] || continue
  for V in "" "--legacy"; do
    tag=legacy
    [ -z "$V" ] && tag=sliced
    "$PY" -u -m tools.m42_encode --ply "$CACHE/$S.ply" --jobs 4 $V \
      --out "$OUT" --json "$OUT/enc_${S}_$tag.json" 2>&1 | tee -a "$OUT/encode.log"
  done
done
echo DONE_M42
