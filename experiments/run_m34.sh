#!/usr/bin/env bash
# M34 -- sweep the zstd frame size and measure what one lost frame costs.
# stages: setup <scene> | build <scene> <bytes> | damage <scene> <bytes> | all <scene> | every
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m34
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
DATA=/workspace/data
SCENE="${2:-bicycle}"
FRAME="${3:-4194304}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
mkdir -p "$OUT/$SCENE"

tag_for() {                      # 4194304 -> f4096k, 1048576 -> f1024k, 262144 -> f0256k
  local k=$(( $1 / 1024 ))
  printf 'f%04dk' "$k"
}

case "${1:-all}" in
  setup)
    bash "$ROOT/experiments/run_m17.sh" deps 2>&1 | tail -1
    SCENES="$SCENE" bash "$ROOT/experiments/m20_setup.sh" 2>&1 | tail -1
    SCENES="$SCENE" bash "$ROOT/experiments/run_m17.sh" data 2>&1 | tail -1
    SCENES="$SCENE" bash "$ROOT/experiments/run_m17.sh" base 2>&1 | tail -3
    ;;
  build)
    t=$(tag_for "$FRAME")
    PLY="$DATA/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply"
    "$PY" -u "$ROOT/experiments/m24_alpha.py" --ply "$PLY" --plans "gp6-6-6_c8_sh3:16:48" \
      --out "$OUT/$SCENE" --no-ply --no-legacy --min-frame "$FRAME" --suffix "_$t" \
      >> "$OUT/build_${SCENE}_$t.log" 2>&1
    ls -l "$OUT/$SCENE"/*_"$t"_auto.gs1 | tee "$OUT/sizes_${SCENE}_$t.txt"
    ;;
  damage)
    t=$(tag_for "$FRAME")
    f="$OUT/$SCENE/gp6_6_6_c8_sh3_r16_b048_${t}_auto.gs1"
    "$PY" -u "$ROOT/tools/m33_damage.py" --gs1 "$f" --out "$OUT/$SCENE/dmg_$t" \
      --archive "$ARCH" --scene-dir "$COLMAP/$SCENE" --tag "${SCENE}_$t" --render \
      --burst 0.001,0.01,0.05 2>&1 | tee "$OUT/damage_${SCENE}_$t.log"
    ;;
  all)
    bash "$0" build "$SCENE" "$FRAME"
    bash "$0" damage "$SCENE" "$FRAME"
    ;;
  every)
    for s in bicycle stump bonsai; do
      bash "$0" setup "$s"
      for fr in 4194304 1048576 262144; do
        bash "$0" all "$s" "$fr"
      done
    done
    ;;
  *) echo "use setup|build|damage|all|every <scene> [frame-bytes]" >&2; exit 2 ;;
esac
