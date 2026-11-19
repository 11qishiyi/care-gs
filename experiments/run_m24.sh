#!/usr/bin/env bash
# M24: choose the alphabet per stream.  Nothing about the codes changes, so the render is a null test:
# if the PSNR moves, the container is wrong.
#
#   bash experiments/run_m24.sh setup    # deps + bicycle data + archive (one scene is enough)
#   bash experiments/run_m24.sh encode   # auto and legacy containers, per-stream table, PLYs
#   bash experiments/run_m24.sh render   # held-out PSNR of both
set -euo pipefail
ROOT="${ROOT:-/workspace/code}"
DATA="${DATA:-/workspace/data}"
ARCH="${ARCH:-$DATA/m360std}"
COLMAP="${COLMAP:-$DATA/mip360_colmap}"
MODELS="${MODELS:-$DATA/models}"
OUT="${OUT:-/workspace/res/m24}"
PY="${PY:-python3}"
SCENE="${SCENE:-bicycle}"
FACTOR="${FACTOR:-1}"
PLANS="${PLANS:-16:48}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT"
REF="$MODELS/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply"
log() { echo "[$(date +%H:%M:%S)] $*"; }

case "${1:-all}" in
  setup)
    SCENE="$SCENE" bash "$ROOT/experiments/run_m17.sh" deps
    SCENE="$SCENE" bash "$ROOT/experiments/run_m17.sh" data
    SCENE="$SCENE" bash "$ROOT/experiments/run_m17.sh" base
    ;;
  encode)
    cd "$ROOT"
    log "=== alphabet per stream, plans $PLANS ==="
    "$PY" -u experiments/m24_alpha.py --ply "$REF" --plans "$PLANS" --out "$OUT" 2>&1 \
      | tee "$OUT/encode.log"
    ;;
  render)
    cd "$ROOT"
    for ply in "$OUT"/*.ply; do
      [ -s "$ply" ] || continue
      name="${SCENE}_$(basename "$ply" .ply)"
      log "--- render $name ---"
      rm -rf "${ARCH:?}/output/${name}"
      "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
        --archive "$ARCH" --name "$name" 2>&1 | tail -1
      bash experiments/probe_render.sh "$name" "$FACTOR" 2>&1 | tail -1 | tee -a "$OUT/render.log"
    done
    ;;
  all) bash "$0" setup; bash "$0" encode; bash "$0" render ;;
  *) echo "use setup|encode|render|all" >&2; exit 2 ;;
esac
