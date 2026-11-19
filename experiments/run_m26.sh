#!/usr/bin/env bash
# M26: is the mid-rate gap a training-recipe artefact?  Two finetune arms at the same primitive count,
# the same seed and the same held-out views, differing only in the image factor used during training.
#
#   bash experiments/run_m26.sh setup
#   bash experiments/run_m26.sh prune        # keep 25 %, volume score, render before finetune
#   bash experiments/run_m26.sh finetune 4   # arm A (control, the M17/M18 recipe)
#   bash experiments/run_m26.sh finetune 2   # arm B (4x the pixels per step)
#   bash experiments/run_m26.sh encode 4     # codec at a budget that lands near 27.5 MB
set -euo pipefail
ROOT="${ROOT:-/workspace/code}"
DATA="${DATA:-/workspace/data}"
ARCH="${ARCH:-$DATA/m360std}"
COLMAP="${COLMAP:-$DATA/mip360_colmap}"
OUT="${OUT:-/workspace/res/m26}"
PY="${PY:-python3}"
SCENE="${SCENE:-bicycle}"
KEEP="${KEEP:-0.25}"
STEPS="${STEPS:-30000}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT"
#: prune the *published* model, not one we trained: the mid-rate comparison is against methods that
#: start from the same 3DGS release, so the starting point must be that release and not our mirror
REF="${REF:-$DATA/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply}"
log() { echo "[$(date +%H:%M:%S)] $*"; }

case "${1:-all}" in
  setup)
    #: deps + data only: the prune source is the published PLY, so there is no base training stage
    SCENE="$SCENE" bash "$ROOT/experiments/run_m17.sh" deps
    SCENE="$SCENE" bash "$ROOT/experiments/run_m17.sh" data
    ;;
  prune)
    cd "$ROOT"
    [ -s "$REF" ] || REF=$(ls "$DATA"/models/output/"$SCENE"/point_cloud/*/point_cloud.ply | head -1)
    log "prune $SCENE keep=$KEEP from $REF"
    "$PY" experiments/prune_ply.py --in "$REF" --out "$OUT/pruned.ply" --keep-frac "$KEEP" \
      --score volume 2>&1 | tail -2
    "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$OUT/pruned.ply" \
      --archive "$ARCH" --name "${SCENE}_m26k${KEEP}" 2>&1 | tail -1
    bash experiments/probe_render.sh "${SCENE}_m26k${KEEP}" 1 2>&1 | tail -1 | tee "$OUT/prune_render.log"
    ;;
  finetune)
    FACTOR="${2:-4}"
    MODE="${3:-freeze}"
    STEPS="${STEPS:-20000}"
    TAG="f${FACTOR}_${MODE}"
    cd "$ROOT"
    EXTRA="--no_scene_scale --lr_scale ${LR_SCALE:-0.3} --grad_clip 1.0"
    if [ "$MODE" = "freeze" ]; then EXTRA="$EXTRA --no_densify"; else EXTRA="$EXTRA --max_gaussians 1532988"; fi
    log "finetune arm $TAG steps=$STEPS"
    "$PY" research/code/scripts/train_gs.py --data "$COLMAP/$SCENE" --out "$OUT/ft_$TAG" \
      --factor "$FACTOR" --steps "$STEPS" --sh_degree 3 --split interleaved --gt-convention archive \
      --keep_all_views --init_ply "$OUT/pruned.ply" --eval_every 2000 $EXTRA \
      > "$OUT/ft_$TAG.log" 2>&1
    grep -e final -e WROTE "$OUT/ft_$TAG.log" | tail -2
    "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" \
      --ply "$OUT/ft_$TAG/point_cloud.ply" --archive "$ARCH" --name "${SCENE}_m26$TAG" 2>&1 | tail -1
    bash experiments/probe_render.sh "${SCENE}_m26$TAG" 1 2>&1 | tail -1 | tee "$OUT/render_$TAG.log"
    ;;
  encode)
    TAG="${2:-f4_freeze}"
    cd "$ROOT"
    PLANS="${PLANS:-gp8-8-8_c10_sh3:16:64,gp8-8-8_c10_sh3:16:48,gp8-6-6_c9_sh3:16:48}"
    log "encode arm $TAG plans=$PLANS"
    "$PY" -u experiments/m24_alpha.py --ply "$OUT/ft_$TAG/point_cloud.ply" \
      --plans "$PLANS" --out "$OUT/enc_$TAG" 2>&1 | tee "$OUT/encode_$TAG.log"
    for ply in "$OUT/enc_$TAG"/*_auto.ply; do
      [ -s "$ply" ] || continue
      name="${SCENE}_$(basename "$ply" .ply)"
      "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
        --archive "$ARCH" --name "$name" 2>&1 | tail -1
      bash experiments/probe_render.sh "$name" 1 2>&1 | tail -1 | tee -a "$OUT/render_$TAG.log"
    done
    ;;
  all) bash "$0" setup; bash "$0" prune; bash "$0" finetune 4 freeze; bash "$0" finetune 2 freeze ;;
  *) echo "use setup|prune|finetune <factor> <freeze|grow>|encode <tag>|all" >&2; exit 2 ;;
esac
