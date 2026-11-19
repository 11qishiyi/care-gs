#!/usr/bin/env bash
# M47 -- prune by gradient saliency vs by volume, same node, same session, same recipe.
#   stages: setup | importance | prune | arm <v|g> | encode <v|g> | all
set -euo pipefail
ROOT="${ROOT:-/workspace/code}"
DATA="${DATA:-/workspace/data}"
ARCH="${ARCH:-$DATA/m360std}"
COLMAP="${COLMAP:-$DATA/mip360_colmap}"
OUT="${OUT:-/workspace/res/m47}"
PY="${PY:-python3}"
SCENE="${SCENE:-bicycle}"
KEEP="${KEEP:-0.25}"
STEPS="${STEPS:-12000}"
IMP_STEPS="${IMP_STEPS:-800}"
PEER="${PEER:-}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT"
REF="$DATA/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply"

setup() {
  SCENE="$SCENE" bash "$ROOT/experiments/run_m17.sh" deps
  SCENE="$SCENE" bash "$ROOT/experiments/run_m17.sh" data
  #: M26's finetune reads the archive GT; build it once from the published model
  [ -d "$ARCH/output/$SCENE" ] || "$PY" "$ROOT/experiments/make_m360_std.py" 2>&1 | tail -2
}

importance() {
  cd "$ROOT"
  "$PY" -u research/code/scripts/train_gs.py --data "$COLMAP/$SCENE" \
    --steps "$IMP_STEPS" --factor 4 --sh_degree 3 --no_densify --no_scene_scale --lr_scale 0.3 \
    --grad_clip 1.0 --split interleaved --gt-convention archive --keep_all_views \
    --init_ply "$REF" --importance_out "$OUT/imp_$SCENE.npy" --importance_steps "$IMP_STEPS" \
    --eval_every 400 --out "$OUT/imp_run" 2>&1 | tee "$OUT/importance.log" | tail -3
}

prune() {
  cd "$ROOT"
  "$PY" experiments/prune_ply.py --in "$REF" --out "$OUT/pruned_g.ply" \
    --keep-frac "$KEEP" --score importance --importance "$OUT/imp_$SCENE.npy" 2>&1 | tail -1
  "$PY" experiments/prune_ply.py --in "$REF" --out "$OUT/pruned_v.ply" \
    --keep-frac "$KEEP" --score volume 2>&1 | tail -1
  #: S2: how much do the two selections actually differ?
  "$PY" "$ROOT/tools/m47_overlap.py" --imp "$OUT/imp_$SCENE.npy" \
    --ply "$REF" --keep "$KEEP" --json "$OUT/overlap.json" 2>&1 | tail -3
}

arm() {
  local A=$1
  cd "$ROOT"
  "$PY" -u research/code/scripts/train_gs.py --data "$COLMAP/$SCENE" --out "$OUT/arm_$A" \
    --factor 4 --steps "$STEPS" --sh_degree 3 --split interleaved --gt-convention archive \
    --keep_all_views --init_ply "$OUT/pruned_$A.ply" --eval_every 2000 \
    --no_densify --no_scene_scale --lr_scale 0.3 --grad_clip 1.0 \
    > "$OUT/train_$A.log" 2>&1
  grep -e final -e WROTE "$OUT/train_$A.log" | tail -2
}

encode() {
  local A=$1
  cd "$ROOT"
  "$PY" -u experiments/m24_alpha.py --ply "$OUT/arm_$A/point_cloud.ply" \
    --plans "gp6-6-6_c8_sh3:16:48" --out "$OUT/enc_$A" 2>&1 | tee "$OUT/enc_$A.log" | tail -2
  for ply in "$OUT"/enc_$A/*_auto.ply; do
    [ -s "$ply" ] || continue
    local name="${SCENE}_m47$(basename "$ply" .ply)"
    "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
      --archive "$ARCH" --name "$name" 2>&1 | tail -1
    bash experiments/probe_render.sh "$name" 1 2>&1 | tail -1 | tee -a "$OUT/render_$A.log"
  done
}

case "${1:-all}" in
  setup) setup ;;
  importance) importance ;;
  prune) prune ;;
  arm) arm "${2:?arm needs v or g}" ;;
  encode) encode "${2:?encode needs v or g}" ;;
  all) setup; importance; prune; arm v; arm g; encode v; encode g ;;
  *) echo "usage: $0 {setup|importance|prune|arm v|g|encode v|g|all}"; exit 2 ;;
esac
