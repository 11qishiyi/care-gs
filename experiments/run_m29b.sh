#!/usr/bin/env bash
# M29b -- the rate-distortion sweep the probe pointed at (amendment F1-F3).
#   build  : four containers, differing only in quantiser widths
#   render : decode each and render the 25 standard views
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m29
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
DATA=/workspace/data
SCENE="${SCENE:-bicycle}"
PLANS="${PLANS:-gp8-8-8_c9_sh3:16:48,gp7-7-7_c9_sh3:16:48,gp6-6-7_c8_sh3:16:48,gp6-6-6_c8_sh3:16:48}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
mkdir -p "$OUT/rd"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/m29b.log"; }

case "${1:-all}" in
  build)
    for plan in ${PLANS//,/ }; do
      log "build $plan"
      "$PY" -u experiments/m24_alpha.py --ply "$DATA/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply" \
        --plans "$plan" --out "$OUT/rd" --no-ply > "$OUT/rd/$(echo "$plan" | tr ':/' '__').log" 2>&1
    done
    ls -l "$OUT/rd"/*.gs1
    ;;
  render)
    for f in "$OUT"/rd/*_auto.gs1; do
      [ -s "$f" ] || continue
      stem="$(basename "$f" .gs1)"
      ply="$OUT/rd/$stem.ply"
      [ -s "$ply" ] || "$PY" -u experiments/m19_codec.py --to-ply "$f" --out "$ply" >> "$OUT/rd/decode.log" 2>&1
      "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
        --archive "$ARCH" --name "bicycle_$stem" 2>&1 | tail -1
      bash "$ROOT/experiments/probe_render.sh" "bicycle_$stem" 1 2>&1 | tail -1 | tee -a "$OUT/rd/render.log"
      rm -f "$ply"
    done
    ;;
  all) bash "$0" build; bash "$0" render ;;
  *) echo "use build|render|all" >&2; exit 2 ;;
esac
