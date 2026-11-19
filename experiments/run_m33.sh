#!/usr/bin/env bash
# M33 -- break the shipping container and measure what it renders.
# stages: setup <scene> | build <scene> | damage <scene> | all <scene> | every
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m33
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
DATA=/workspace/data
SCENE="${2:-bicycle}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
mkdir -p "$OUT/$SCENE"

case "${1:-all}" in
  setup)
    bash "$ROOT/experiments/run_m17.sh" deps 2>&1 | tail -1
    SCENES="$SCENE" bash "$ROOT/experiments/m20_setup.sh" 2>&1 | tail -1
    SCENES="$SCENE" bash "$ROOT/experiments/run_m17.sh" data 2>&1 | tail -1
    SCENES="$SCENE" bash "$ROOT/experiments/run_m17.sh" base 2>&1 | tail -3
    ;;
  build)
    PLY="$DATA/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply"
    "$PY" -u "$ROOT/experiments/m24_alpha.py" --ply "$PLY" --plans "gp6-6-6_c8_sh3:16:48" \
      --out "$OUT/$SCENE" --no-ply >> "$OUT/build_$SCENE.log" 2>&1
    ls -l "$OUT/$SCENE"/*.gs1 | tee "$OUT/sizes_$SCENE.txt"
    ;;
  damage)
    f="$OUT/$SCENE/gp6_6_6_c8_sh3_r16_b048_auto.gs1"
    "$PY" -u "$ROOT/tools/m33_damage.py" --gs1 "$f" --out "$OUT/$SCENE/dmg" \
      --archive "$ARCH" --scene-dir "$COLMAP/$SCENE" --tag "$SCENE" --render 2>&1 \
      | tee "$OUT/damage_$SCENE.log"
    ;;
  all) bash "$0" build "$SCENE"; bash "$0" damage "$SCENE" ;;
  every)
    for s in bicycle stump bonsai; do
      bash "$0" setup "$s"
      bash "$0" all "$s"
    done
    ;;
  *) echo "use setup|build|damage|all|every <scene>" >&2; exit 2 ;;
esac
