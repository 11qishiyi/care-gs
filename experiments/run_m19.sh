#!/usr/bin/env bash
# M19: prove the byte model is a format -- encode to a file, decode it back, render the decoded
# model, and check the PSNR is the one the encoder promised.  Also prices the two dimensions the
# paper lists but never measured: decode time/memory, and what a lost byte costs.
#
#   bash experiments/run_m19.sh deps data base
#   bash experiments/run_m19.sh encode     # .gs1 files + encode/decode timing + PLY export
#   bash experiments/run_m19.sh render     # archive entries from the decoded PLYs + clean PSNR
#   bash experiments/run_m19.sh damage     # damage table on the headline file
set -euo pipefail
ROOT=/workspace/code
DATA=/workspace/data
ARCH=$DATA/m360std
COLMAP=$DATA/mip360_colmap
OUT=/workspace/res/m19
SCENE=bicycle
SPECS="${SPECS:-c10_o8_sh3,c8_o8_sh3,vq12_c8_o8}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT"

log() { echo "[$(date +%H:%M:%S)] $*"; }

stage_encode() {
  cd "$ROOT"
  log "=== encode $SPECS ==="
  python3 -u experiments/m19_codec.py --archive "$ARCH" --scenes "$SCENE" --specs "$SPECS" \
    --out "$OUT/models" --deck 2>&1 | tee "$OUT/encode.log" | tail -20
  log "=== files ==="
  ls -l "$OUT/models" | tail -12
}

stage_render() {
  cd "$ROOT"
  for spec in ${SPECS//,/ }; do
    ply="$OUT/models/${SCENE}_${spec}.ply"
    [ -s "$ply" ] || { log "$spec: no PLY"; continue; }
    log "--- $spec: archive + render ---"
    #: ``make_m360_archive`` hard-links the PLY, so an entry built from an older file keeps that
    #: inode and silently renders the stale model (cost: one debugging afternoon, M19).  Removing
    #: the entry first is the difference between "the decode is broken" and "the probe saw a
    #: two-hour-old PLY".
    rm -rf "${ARCH:?}/output/${SCENE}_${spec}_dec"
    python3 experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
      --archive "$ARCH" --name "${SCENE}_${spec}_dec" 2>&1 | tail -1
    bash experiments/probe_render.sh "${SCENE}_${spec}_dec" 1 2>&1 | tail -2
  done
}

stage_damage() {
  cd "$ROOT"
  log "=== damage table (c10_o8_sh3) ==="
  python3 -u experiments/m19_codec.py --damage "$OUT/models/${SCENE}_c10_o8_sh3.gs1" 2>&1 | tee "$OUT/damage.log"
}

case "${1:-all}" in
  deps)   bash "$ROOT/experiments/run_m17.sh" deps ;;
  data)   bash "$ROOT/experiments/run_m17.sh" data ;;
  base)   bash "$ROOT/experiments/run_m17.sh" base ;;
  encode) stage_encode ;;
  render) stage_render ;;
  damage) stage_damage ;;
  *) echo "use deps|data|base|encode|render|damage" >&2; exit 2 ;;
esac
