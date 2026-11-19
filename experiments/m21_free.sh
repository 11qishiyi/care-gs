#!/usr/bin/env bash
# M21 follow-up: the *free* boundary.  The best-rate file is already ordered geometry -> colour, so
# cutting it just before the SH rest block leaves a complete degree-0 model at no extra bytes.
# This measures what that prefix renders as, which is the honest baseline for the bit-plane ladder.
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m21
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT/ply2"

for scene in bicycle stump; do
  f="$OUT/models/${scene}_c10_o8_sh3.gs1"
  python3 -u experiments/m21_ladder.py --file "$f" --out "$OUT/cut2" --ply-dir "$OUT/ply2" \
    --json "$OUT/ladder2_${scene}.json" | tee -a "$OUT/ladder2.log"
done

for ply in "$OUT"/ply2/*_dc.ply; do
  [ -s "$ply" ] || continue
  name="$(basename "$ply" .ply)_b"      # b = best-rate file, as opposed to the _p ladder
  rm -rf "${ARCH:?}/output/${name}"
  python3 experiments/make_m360_archive.py --scene-dir "$COLMAP/$(echo "$name" | cut -d_ -f1)" \
    --ply "$ply" --archive "$ARCH" --name "$name" 2>&1 | tail -1
  bash experiments/probe_render.sh "$name" 1 2>&1 | tail -1 | tee -a "$OUT/render2.log"
done
echo FREE_BOUNDARY_DONE
