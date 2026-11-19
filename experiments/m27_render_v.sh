#!/usr/bin/env bash
# Render every ablation container and print one PSNR line each.
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m27
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
SCENE="${SCENE:-bicycle}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
cd "$ROOT"

for f in "$OUT"/enc/v_*.gs1 "$OUT"/enc/bicycle_*.gs1; do
  [ -s "$f" ] || continue
  stem="$(basename "$f" .gs1)"
  name="bicycle_$stem"
  ply="$OUT/enc/$stem.ply"
  if [ ! -s "$ply" ]; then
    python3 -u experiments/m19_codec.py --to-ply "$f" --out "$ply" >> "$OUT/decode.log" 2>&1 \
      || { echo "decode failed $f" | tee -a "$OUT/render.log"; continue; }
  fi
  python3 experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
    --archive "$ARCH" --name "$name" 2>&1 | tail -1
  bash experiments/probe_render.sh "$name" 1 2>&1 | tail -1 | tee -a "$OUT/render.log"
  rm -f "$ply"
done
