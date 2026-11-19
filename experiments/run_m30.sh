#!/usr/bin/env bash
# M30 -- per-cluster position widths.  build | adapt | render | all
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m30
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
DATA=/workspace/data
SCENE="${SCENE:-bicycle}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
mkdir -p "$OUT"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/m30.log"; }

BASE="$OUT/base.gs1"

case "${1:-all}" in
  setup)
    bash "$ROOT/experiments/run_m17.sh" deps 2>&1 | tail -1
    bash "$ROOT/experiments/run_m17.sh" data 2>&1 | tail -1
    bash "$ROOT/experiments/run_m17.sh" base 2>&1 | tail -1
    ;;
  build)
    log "build the shipping container ($SCENE)"
    "$PY" -u experiments/m24_alpha.py --ply "$DATA/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply" \
      --plans "gp6-6-6_c8_sh3:16:48" --out "$OUT" --no-ply > "$OUT/build.log" 2>&1
    cp "$OUT"/gp6_6_6_c8_sh3_r16_b048_auto.gs1 "$BASE"
    ls -l "$BASE"
    ;;
  adapt)
    for div in 255 127 64; do
      log "adapt target_div=$div"
      "$PY" -u experiments/m30_adapt.py --gs1 "$BASE" --out "$OUT/adapt_$div.gs1" --nominal 8 \
        --target-div "$div" --json "$OUT/adapt_$div.json" 2>&1 | tail -4
    done
    ;;
  render)
    for f in "$OUT"/adapt_*.gs1; do
      [ -s "$f" ] || continue
      stem="$(basename "$f" .gs1)"
      ply="$OUT/$stem.ply"
      [ -s "$ply" ] || "$PY" -u experiments/m19_codec.py --to-ply "$f" --out "$ply" >> "$OUT/decode.log" 2>&1
      "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
        --archive "$ARCH" --name "bicycle_$stem" 2>&1 | tail -1
      bash "$ROOT/experiments/probe_render.sh" "bicycle_$stem" 1 2>&1 | tail -1 | tee -a "$OUT/render.log"
      rm -f "$ply"
    done
    ;;
  all) bash "$0" setup; bash "$0" build; bash "$0" adapt; bash "$0" render ;;
  *) echo "use setup|build|adapt|render|all" >&2; exit 2 ;;
esac
