#!/usr/bin/env bash
# M25: decoder footprint.  Same bitstream, cheaper decode.  The render is the null test: the pixels must
# not move, because nothing in this round touches what the bytes mean.
#
#   bash experiments/run_m25.sh setup     # deps + bicycle data + archive
#   bash experiments/run_m25.sh encode    # the 83.41 MB shelf container
#   bash experiments/run_m25.sh time      # decode wall time and peak RSS
#   bash experiments/run_m25.sh render    # held-out PSNR (must stay 24.08 dB)
set -euo pipefail
ROOT="${ROOT:-/workspace/code}"
DATA="${DATA:-/workspace/data}"
ARCH="${ARCH:-$DATA/m360std}"
COLMAP="${COLMAP:-$DATA/mip360_colmap}"
MODELS="${MODELS:-$DATA/models}"
OUT="${OUT:-/workspace/res/m25}"
PY="${PY:-python3}"
SCENE="${SCENE:-bicycle}"
FACTOR="${FACTOR:-1}"
PLANS="${PLANS:-gp8-6-6_c9_sh3:16:48}"
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
    "$PY" -u experiments/m24_alpha.py --ply "$REF" --plans "$PLANS" --out "$OUT" 2>&1 | tee "$OUT/encode.log"
    ;;
  time)
    cd "$ROOT"
    "$PY" -u tools/m25_time.py --dir "$OUT" 2>&1 | tee "$OUT/time.log"
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
  all) bash "$0" setup; bash "$0" encode; bash "$0" time; bash "$0" render ;;
  *) echo "use setup|encode|time|render|all" >&2; exit 2 ;;
esac
