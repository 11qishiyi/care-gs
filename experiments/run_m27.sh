#!/usr/bin/env bash
# M27 -- the anchor representation: one attribute record per voxel, offsets per primitive.
#   bash experiments/run_m27.sh setup          # published bicycle + colmap + base archive
#   bash experiments/run_m27.sh encode         # ppa 4/8/16 at 3-bit offsets, plus 4-bit at ppa 8
#   bash experiments/run_m27.sh render         # PSNR for every container written by `encode`
#   bash experiments/run_m27.sh all
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m27
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
DATA=/workspace/data
SCENE="${SCENE:-bicycle}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3

mkdir -p "$OUT"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/m27.log"; }

PLANS="${PLANS:-4:3,8:3,16:3,8:4}"

case "${1:-all}" in
  setup)
    bash "$ROOT/experiments/run_m17.sh" deps  2>&1 | tail -3
    bash "$ROOT/experiments/run_m17.sh" data  2>&1 | tail -3
    bash "$ROOT/experiments/run_m17.sh" base  2>&1 | tail -3
    ;;
  encode)
    mkdir -p "$OUT/enc"
    for plan in ${PLANS//,/ }; do
      ppa="${plan%%:*}"; ob="${plan##*:}"
      name="${SCENE}_a${ppa}_o${ob}"
      log "encode $name"
      "$PY" -u experiments/m27_anchor.py \
        --ply "$DATA/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply" \
        --out "$OUT/enc/$name.gs1" --ppa "$ppa" --rank 16 --bits 48 --pos-bits 10 --offset-bits "$ob" \
        --attr-bits 8 --dc-bits 3 --json "$OUT/enc/$name.json" > "$OUT/enc/$name.log" 2>&1
      grep -E '"bytes"|"b_per_prim"|"ppa"|"n_anchor"|"voxel"' "$OUT/enc/$name.log" | tr -d '\n' \
        | tee -a "$OUT/encode_sizes.txt" >/dev/null
      echo " <- $name" >> "$OUT/encode_sizes.txt"
    done
    cat "$OUT/encode_sizes.txt"
    ;;
  render)
    for f in "$OUT"/enc/*.gs1; do
      [ -s "$f" ] || continue
      name="${SCENE}_$(basename "$f" .gs1)"
      #: the archive builder wants a PLY, so decode the container to one first: the round trip through
      #: to_ply is the decoder's own output, not the encoder's memory.
      "$PY" -u experiments/m19_codec.py --to-ply "$f" --out "$OUT/enc/$(basename "$f" .gs1).ply" \
        >> "$OUT/decode.log" 2>&1 || { echo "decode failed $f" | tee -a "$OUT/render.log"; continue; }
      "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" \
        --ply "$OUT/enc/$(basename "$f" .gs1).ply" --archive "$ARCH" --name "$name" 2>&1 | tail -1
      bash experiments/probe_render.sh "$name" 1 2>&1 | tail -1 | tee -a "$OUT/render.log"
    done
    ;;
  all) bash "$0" setup; bash "$0" encode; bash "$0" render ;;
  *) echo "use setup|encode|render|all" >&2; exit 2 ;;
esac
