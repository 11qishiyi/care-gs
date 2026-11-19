#!/usr/bin/env bash
# M23: geometry, coded again.  Three variants of the same model, so the deltas and the quaternion
# change can be priced apart:
#
#   A  base      r=16/48, shelf geometry and shelf quaternions   (= the M22 point)
#   B  delta     A + Morton deltas on positions/scales/opacity    (lossless: identical tensors)
#   C  st3       A + smallest-three quaternions at 8 bits         (M15 measured this as free)
#   D  both      B + C
#
#   bash experiments/run_m23.sh encode      # four containers + four PLYs, byte-exactness checked
#   bash experiments/run_m23.sh render      # held-out PSNR of each
set -euo pipefail
ROOT="${ROOT:-/workspace/code}"
DATA="${DATA:-/workspace/data}"
ARCH="${ARCH:-$DATA/m360std}"
COLMAP="${COLMAP:-$DATA/mip360_colmap}"
MODELS="${MODELS:-$DATA/models}"
OUT="${OUT:-/workspace/res/m23}"
PY="${PY:-python3}"
SCENE="${SCENE:-bicycle}"
FACTOR="${FACTOR:-1}"
RANK="${RANK:-16}"
BITS="${BITS:-48}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT/models"
REF="$MODELS/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply"
log() { echo "[$(date +%H:%M:%S)] $*"; }

stage_encode() {
  cd "$ROOT"
  "$PY" -u experiments/m23_run.py --ply "$REF" --out "$OUT/models" --rank "$RANK" --bits "$BITS" \
    --json "$OUT/encode_${SCENE}.json" 2>&1 | tee "$OUT/encode.log"
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
  encode) stage_encode ;;
  render) stage_render ;;
  all)    stage_encode; stage_render ;;
  *) echo "use encode|render|all" >&2; exit 2 ;;
esac
