#!/usr/bin/env bash
# M22: one colour basis for six million Gaussians.
#
#   bash experiments/run_m22.sh probe     # rank/budget vs coefficient error, against the ladder
#   bash experiments/run_m22.sh encode    # per plan: container + decoded PLY
#   bash experiments/run_m22.sh render    # held-out PSNR per plan
#
# The plan list is "rank:bits" pairs, e.g. PLANS="16:48,16:64,32:64" (48 bits = 6 B per primitive).
set -euo pipefail
ROOT="${ROOT:-/workspace/code}"
DATA="${DATA:-/workspace/data}"
ARCH="${ARCH:-$DATA/m360std}"
COLMAP="${COLMAP:-$DATA/mip360_colmap}"
MODELS="${MODELS:-$DATA/models}"
OUT="${OUT:-/workspace/res/m22}"
PY="${PY:-python3}"
SCENE="${SCENE:-bicycle}"
FACTOR="${FACTOR:-1}"
PLANS="${PLANS:-16:48,16:64,32:64}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT"
REF="$MODELS/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply"
log() { echo "[$(date +%H:%M:%S)] $*"; }

stage_probe() {
  cd "$ROOT"
  log "=== spectrum and allocation on $SCENE ==="
  "$PY" -u experiments/m22_basis.py --probe "$REF" --ranks 8,16,32 \
    --budgets 24,32,48,64,96,128,165 --json "$OUT/probe_${SCENE}.json" 2>&1 | tee "$OUT/probe.log"
}

stage_encode() {
  cd "$ROOT"
  log "=== encode plans $PLANS ==="
  "$PY" -u experiments/m22_basis.py --encode "$REF" --plans "$PLANS" --layouts bits \
    --out "$OUT/models" --json "$OUT/encode_${SCENE}.json" 2>&1 | tee "$OUT/encode.log"
}

stage_render() {
  cd "$ROOT"
  for ply in "$OUT"/models/*.ply; do
    [ -s "$ply" ] || continue
    name="${SCENE}_$(basename "$ply" .ply)_b"
    log "--- render $name ---"
    rm -rf "${ARCH:?}/output/${name}"
    "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
      --archive "$ARCH" --name "$name" 2>&1 | tail -1
    bash experiments/probe_render.sh "$name" "$FACTOR" 2>&1 | tail -1 | tee -a "$OUT/render.log"
  done
}

case "${1:-all}" in
  probe)  stage_probe ;;
  encode) stage_encode ;;
  render) stage_render ;;
  all)    stage_probe; stage_encode; stage_render ;;
  *) echo "use probe|encode|render|all" >&2; exit 2 ;;
esac
