#!/usr/bin/env bash
# M38 -- joint geometry codebook: three codebook sizes, one fixed model, one fixed container otherwise.
#
#   bash experiments/run_m38.sh setup          # cached model + COLMAP + GT archive
#   bash experiments/run_m38.sh encode 4096    # container at k = 4096 (12-bit indices)
#   bash experiments/run_m38.sh render 4096
#   bash experiments/run_m38.sh all
set -uo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m38
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
DATA=/workspace/data
CACHE=/mnt/m35cache
SCENE=bicycle
SPEC="gp6-6-6_c8_sh3"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
mkdir -p "$OUT"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/m38.log"; }
PLY="$DATA/m20/$SCENE.ply"

case "${1:-all}" in
  setup)
    if [ -s "$CACHE/$SCENE.ply" ]; then
      mkdir -p "$(dirname "$PLY")"; ln -sf "$CACHE/$SCENE.ply" "$PLY"
      log "model from cache: $(stat -c %s "$CACHE/$SCENE.ply") B"
    else
      log "no cached model"; exit 1
    fi
    if [ ! -d "$ARCH/output/$SCENE" ]; then
      SCENES="$SCENE" bash "$ROOT/experiments/fetch_m360_colmap.sh" 2>&1 | tail -1
      SCENES="$SCENE" bash "$ROOT/experiments/run_m17.sh" base 2>&1 | tail -2
    else
      log "archive present"
    fi
    ;;
  encode)
    K="${2:?k}"
    log "encode k=$K"
    t0=$(date +%s)
    "$PY" -u "$ROOT/tools/m38_build.py" --ply "$PLY" --k "$K" --spec "$SPEC" \
      --out "$OUT/k$K.gs1" --json "$OUT/k$K.json" 2>&1 | tail -20 | tee -a "$OUT/m38.log"
    t1=$(date +%s)
    echo "enc_$K $((t1-t0)) s" >> "$OUT/m38_time.txt"
    ;;
  render)
    K="${2:?k}"
    ply="$OUT/k$K.ply"
    "$PY" -u "$ROOT/experiments/m19_codec.py" --to-ply "$OUT/k$K.gs1" --out "$ply" >> "$OUT/dec_$K.log" 2>&1
    "$PY" "$ROOT/experiments/make_m360_archive.py" --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
      --archive "$ARCH" --name "m38_k$K" 2>&1 | tail -1
    r=$(bash "$ROOT/experiments/probe_render.sh" "m38_k$K" 1 2>&1 | tail -1)
    echo "$K $(stat -c %s "$OUT/k$K.gs1") $r" | tee -a "$OUT/render.txt"
    rm -f "$ply"
    ;;
  all)
    for K in 4096 16384 65536; do
      bash "$0" encode "$K" || { log "encode $K failed"; continue; }
      bash "$0" render "$K" || log "render $K failed"
    done
    cat "$OUT/render.txt" "$OUT/m38_time.txt"
    ;;
  *) echo "use setup|encode|render|all <k>" >&2; exit 2 ;;
esac
