#!/usr/bin/env bash
# M29 -- where the last 13.6 bytes go.  probe | split | render
#   probe : entropy table over the shipped shelf container
#   split : re-write the shelf with context-split attribute streams, verify bit-identical decode
#   render: decode the split container and render the 25 standard views
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m29
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
DATA=/workspace/data
SCENE="${SCENE:-bicycle}"
G1="$OUT/shelf.gs1"
G2="$OUT/shelf_split.gs1"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
mkdir -p "$OUT"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/m29.log"; }

case "${1:-all}" in
  shelf)
    log "building the M24 shelf container"
    "$PY" -u experiments/m24_alpha.py --ply "$DATA/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply" \
      --plans "gp8-8-8_c10_sh3:16:48" --out "$OUT" --no-ply > "$OUT/shelf.log" 2>&1
    ls -l "$OUT"/*.gs1
    ;;
  probe)
    log "entropy probe"
    "$PY" -u experiments/m29_entropy.py --gs1 "$G1" --json "$OUT/entropy.json" 2>&1 | tail -14
    ;;
  split)
    log "context split"
    "$PY" -u experiments/m29_split.py --gs1 "$G1" --out "$G2" --json "$OUT/split.json" 2>&1 | tail -12
    ;;
  render)
    ply="$OUT/shelf_split.ply"
    "$PY" -u experiments/m19_codec.py --to-ply "$G2" --out "$ply" >> "$OUT/decode.log" 2>&1
    "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
      --archive "$ARCH" --name "bicycle_m29split" 2>&1 | tail -1
    bash "$ROOT/experiments/probe_render.sh" "bicycle_m29split" 1 2>&1 | tail -1 | tee -a "$OUT/render.log"
    ;;
  time)
    export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
    "$PY" tools/m25_time.py --dir "$OUT" --glob 'shelf*.gs1' 2>&1 | tail -3
    ;;
  all) bash "$0" shelf; bash "$0" probe; bash "$0" split; bash "$0" render ;;
  *) echo "use shelf|probe|split|render|time|all" >&2; exit 2 ;;
esac
