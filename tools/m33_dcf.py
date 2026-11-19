#!/usr/bin/env bash
# M33 diagnostic: the same streams in a DC-first physical order, so the 50 % prefix is a degree-0
# model instead of a colourless one.  Truncation ladder only.
set -uo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m33
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
for s in "$@"; do
  f="$OUT/$s/gp6_6_6_c8_sh3_r16_b048_auto.gs1"
  r="$OUT/$s/reordered.gs1"
  python3 "$ROOT/tools/m33_reorder.py" --gs1 "$f" --out "$r" || { echo "$s reorder FAILED"; continue; }
  python3 -u "$ROOT/tools/m33_damage.py" --gs1 "$r" --out "$OUT/$s/dmg_dc" --archive "$ARCH" \
    --scene-dir "$COLMAP/$s" --tag "${s}_dc" --only trunc --render 2>&1 | tee "$OUT/dmg_dc_$s.log"
done
echo "[$(date +%H:%M:%S)] dc-first done: $*"
