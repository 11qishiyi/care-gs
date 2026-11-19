#!/usr/bin/env bash
# M31 -- the shipping configuration on four scenes, with the cost measured.
# stages: setup <scene> | build <scene> | cost <scene> | all <scene>
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m31
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
DATA=/workspace/data
SCENE="${2:-bicycle}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
mkdir -p "$OUT"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/m31_$SCENE.log"; }
PLY="$DATA/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply"

case "${1:-all}" in
  setup)
    bash "$ROOT/experiments/run_m17.sh" deps 2>&1 | tail -1
    SCENES="$SCENE" bash "$ROOT/experiments/m20_setup.sh" 2>&1 | tail -1
    SCENES="$SCENE" bash "$ROOT/experiments/run_m17.sh" data 2>&1 | tail -1
    SCENES="$SCENE" bash "$ROOT/experiments/run_m17.sh" base 2>&1 | tail -3
    ;;
  build)
    log "build $SCENE"
    t0=$(date +%s)
    "$PY" -u experiments/m24_alpha.py --ply "$PLY" --plans "gp6-6-6_c8_sh3:16:48" \
      --out "$OUT/$SCENE" --no-ply >> "$OUT/build_$SCENE.log" 2>&1
    t1=$(date +%s)
    echo "encode_wall $((t1-t0)) s" | tee "$OUT/enc_$SCENE.txt"
    ls -l "$OUT/$SCENE"/*.gs1 | tee -a "$OUT/sizes_$SCENE.txt"
    ;;
  render)
    f="$OUT/$SCENE/gp6_6_6_c8_sh3_r16_b048_auto.gs1"
    ply="$OUT/$SCENE/$SCENE.ply"
    [ -s "$ply" ] || "$PY" -u experiments/m19_codec.py --to-ply "$f" --out "$ply" >> "$OUT/decode_$SCENE.log" 2>&1
    "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
      --archive "$ARCH" --name "${SCENE}_ship" 2>&1 | tail -1
    bash "$ROOT/experiments/probe_render.sh" "${SCENE}_ship" 1 2>&1 | tail -1 | tee -a "$OUT/render_$SCENE.log"
    rm -f "$ply"
    ;;
  cost)
    f="$OUT/$SCENE/gp6_6_6_c8_sh3_r16_b048_auto.gs1"
    "$PY" -u "$ROOT/tools/m25_time.py" --dir "$OUT/$SCENE" --glob 'gp6_6_6_c8_sh3_r16_b048_auto.gs1' 2>&1 | tail -2 | tee -a "$OUT/cost_$SCENE.log"
    ;;
  streams)
    f="$OUT/$SCENE/gp6_6_6_c8_sh3_r16_b048_auto.gs1"
    "$PY" -u "$ROOT/tools/m31_streams.py" "$f" 2>&1 | tee "$OUT/streams_$SCENE.txt" | tail -14
    ;;
  all) bash "$0" build "$SCENE"; bash "$0" render "$SCENE"; bash "$0" cost "$SCENE"; bash "$0" streams "$SCENE" ;;
  *) echo "use setup|build|render|cost|streams|all <scene>" >&2; exit 2 ;;
esac
