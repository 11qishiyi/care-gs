#!/usr/bin/env bash
# M36 -- put the rate in the loss: three arms, one pruning source, identical everything else.
#
#   bash experiments/run_m36.sh setup              # cached model + COLMAP + GT archive
#   bash experiments/run_m36.sh prune              # 25 % keep, volume score (M26's source)
#   bash experiments/run_m36.sh arm a|b|c          # fine-tune one arm, 12k steps, factor 4
#   bash experiments/run_m36.sh encode a|b|c       # container + size
#   bash experiments/run_m36.sh render a|b|c       # PSNR on the held-out views
#
# Arms differ only in the loss: a = plain (M17 recipe), b = + log rate term, c = + L2 control.
# Both b and c calibrate their own lambda to the same 5 % gradient share, because an equal lambda is not
# an equal pressure for two different functionals -- that is what makes c a control for b.
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m36
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
DATA=/workspace/data
CACHE=/mnt/m35cache
SCENE=bicycle
STEPS=12000
SPEC="gp6-6-6_c8_sh3"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
mkdir -p "$OUT"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/m36.log"; }
PLY="$DATA/m20/$SCENE.ply"
PRUNED="$OUT/pruned.ply"

arm_flags() {   # $1 = a|b|c|d
  case "$1" in
    a) echo "" ;;
    b) echo "--rate-lambda -1 --rate-kind log --rate-groups shN,sh0,scales,opacities" ;;
    c) echo "--rate-lambda -1 --rate-kind l2  --rate-groups shN,sh0,scales,opacities" ;;
    # d = the same log term at a 15 % gradient share: the sensitivity point of the pressure, declared in
    # tools/m36_amend.md before it was run (does the return keep rising with lambda, or saturate?)
    d) echo "--rate-lambda -1 --rate-kind log --rate-groups shN,sh0,scales,opacities --rate_share 0.15" ;;
    *) echo "arm must be a, b, c or d" >&2; exit 2 ;;
  esac
}

case "${1:-all}" in
  setup)
    bash "$ROOT/experiments/run_m17.sh" deps 2>&1 | tail -1
    if [ -s "$CACHE/$SCENE.ply" ]; then
      mkdir -p "$(dirname "$PLY")"; ln -sf "$CACHE/$SCENE.ply" "$PLY"
      log "model from cache: $(stat -c %s "$CACHE/$SCENE.ply") B"
    else
      log "no cached model -- fetch it"
      curl -sSL --retry 5 -o "$PLY" \
        "https://hf-mirror.com/datasets/dylanebert/3dgs/resolve/main/$SCENE/point_cloud/iteration_30000/point_cloud.ply"
    fi
    SCENES="$SCENE" bash "$ROOT/experiments/fetch_m360_colmap.sh" 2>&1 | tail -1
    SCENES="$SCENE" bash "$ROOT/experiments/run_m17.sh" data 2>&1 | tail -1
    SCENES="$SCENE" bash "$ROOT/experiments/run_m17.sh" base 2>&1 | tail -2
    ;;
  prune)
    "$PY" -u "$ROOT/experiments/prune_ply.py" --in "$PLY" --out "$PRUNED" \
      --keep-frac 0.25 --score volume 2>&1 | tail -3 | tee -a "$OUT/m36.log"
    ;;
  arm)
    A="${2:?arm a|b|c}"
    log "arm $A: $STEPS steps, factor 4, $( [ "$A" = a ] && echo 'no rate term' || echo 'rate term' )"
    t0=$(date +%s)
    "$PY" -u "$ROOT/research/code/scripts/train_gs.py" \
      --data "$COLMAP/$SCENE" --out "$OUT/arm_$A" --factor 4 --steps "$STEPS" \
      --init_ply "$PRUNED" --no_densify --no_scene_scale --lr_scale 0.3 --grad_clip 1.0 \
      --sh_degree 3 --split interleaved --gt-convention archive --keep_all_views \
      --eval_every 2000 $(arm_flags "$A") > "$OUT/train_$A.log" 2>&1
    t1=$(date +%s)
    echo "wall_$A $((t1-t0)) s" | tee -a "$OUT/m36_time.txt"
    tail -3 "$OUT/train_$A.log"
    ;;
  encode)
    A="${2:?arm a|b|c}"
    "$PY" -u "$ROOT/experiments/m24_alpha.py" --ply "$OUT/arm_$A/point_cloud.ply" \
      --plans "$SPEC:16:48" --out "$OUT/enc_$A" --no-ply --no-legacy \
      --suffix "_$A" > "$OUT/encode_$A.log" 2>&1
    ls -l "$OUT/enc_$A"/*.gs1 | tee -a "$OUT/m36_sizes.txt"
    ;;
  render)
    A="${2:?arm a|b|c}"
    f=$(ls "$OUT/enc_$A"/*.gs1 | head -1)
    ply="$OUT/enc_$A/arm_$A.ply"
    "$PY" -u "$ROOT/experiments/m19_codec.py" --to-ply "$f" --out "$ply" >> "$OUT/decode_$A.log" 2>&1
    "$PY" "$ROOT/experiments/make_m360_archive.py" --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
      --archive "$ARCH" --name "m36_$A" 2>&1 | tail -1
    r=$(bash "$ROOT/experiments/probe_render.sh" "m36_$A" 1 2>&1 | tail -1)
    echo "$A $(stat -c %s "$f") $r" | tee -a "$OUT/render.txt"
    rm -f "$ply"
    ;;
  all)
    bash "$0" setup; bash "$0" prune
    for A in a b c; do bash "$0" arm "$A"; bash "$0" encode "$A"; bash "$0" render "$A"; done
    ;;
  *) echo "use setup|prune|arm|encode|render|all <arm>" >&2; exit 2 ;;
esac
