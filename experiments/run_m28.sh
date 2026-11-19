#!/usr/bin/env bash
# M28 -- predicted anchors.  setup | train | render | all
#   train : encode two containers (6-bit DC at ppa 8, and 4-bit DC at ppa 8) and log the training curve
#   render: decode each container to a PLY, archive it, render the 25 standard views
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m28
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
DATA=/workspace/data
SCENE="${SCENE:-bicycle}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3

mkdir -p "$OUT/enc"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/m28.log"; }

PLANS="${PLANS:-o4_dc6,o4_dc4}"

case "${1:-all}" in
  setup)
    bash "$ROOT/experiments/run_m17.sh" deps 2>&1 | tail -2
    bash "$ROOT/experiments/run_m17.sh" data 2>&1 | tail -2
    bash "$ROOT/experiments/run_m17.sh" base 2>&1 | tail -2
    ;;
  train)
    for plan in ${PLANS//,/ }; do
      ob="${plan%%_*}"; ob="${ob#o}"; dcb="${plan##*dc}"
      name="${SCENE}_p${ob}_dc${dcb}"
      log "encode $name (offset bits $ob, dc bits $dcb)"
      "$PY" -u experiments/m28_pred.py \
        --ply "$DATA/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply" \
        --out "$OUT/enc/$name.gs1" --ppa 8 --rank 16 --bits 48 --offset-bits "$ob" \
        --dc-bits "$dcb" --steps 12000 --hidden 64 --json "$OUT/enc/$name.json" \
        > "$OUT/enc/$name.log" 2>&1
      grep -E "step (0|1000|4000|8000|11999)|bytes|b_per_prim" "$OUT/enc/$name.log" | tail -6
    done
    ;;
  render)
    for f in "$OUT"/enc/*.gs1; do
      [ -s "$f" ] || continue
      stem="$(basename "$f" .gs1)"
      ply="$OUT/enc/$stem.ply"
      [ -s "$ply" ] || "$PY" -u experiments/m19_codec.py --to-ply "$f" --out "$ply" >> "$OUT/decode.log" 2>&1
      "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
        --archive "$ARCH" --name "bicycle_$stem" 2>&1 | tail -1
      bash "$ROOT/experiments/probe_render.sh" "bicycle_$stem" 1 2>&1 | tail -1 | tee -a "$OUT/render.log"
      rm -f "$ply"
    done
    ;;
  all) bash "$0" setup; bash "$0" train; bash "$0" render ;;
  *) echo "use setup|train|render|all" >&2; exit 2 ;;
esac
