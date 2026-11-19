#!/usr/bin/env bash
# M39 -- prune to 15 % and 10 %, fine-tune each with and without the rate pressure, encode, render.
#
#   bash experiments/run_m39.sh setup
#   bash experiments/run_m39.sh prune 0.15
#   bash experiments/run_m39.sh arm 0.15 a|b
#   bash experiments/run_m39.sh encode 0.15 a|b
#   bash experiments/run_m39.sh render 0.15 a|b
#   bash experiments/run_m39.sh all
set -uo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m39
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
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/m39.log"; }
PLY="$DATA/m20/$SCENE.ply"

tag_of() { printf 'p%02d' "$(awk -v f="$1" 'BEGIN{printf "%d", f*100 + 0.5}')"; }

arm_flags() {
  case "$1" in
    a) echo "" ;;
    b) echo "--rate-lambda -1 --rate-kind log --rate-groups shN,sh0,scales,opacities --rate_share 0.05" ;;
    *) echo "arm must be a or b" >&2; exit 2 ;;
  esac
}

case "${1:-all}" in
  setup)
    mkdir -p "$(dirname "$PLY")"
    [ -s "$CACHE/$SCENE.ply" ] && ln -sf "$CACHE/$SCENE.ply" "$PLY" || { log "no cached model"; exit 1; }
    [ -d "$ARCH/output/$SCENE" ] || {
      mkdir -p "$DATA/models/output/$SCENE/point_cloud/iteration_30000"
      ln -sf "$CACHE/$SCENE.ply" "$DATA/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply"
      SCENES="$SCENE" bash "$ROOT/experiments/fetch_m360_colmap.sh" 2>&1 | tail -1
      SCENES="$SCENE" bash "$ROOT/experiments/run_m17.sh" base 2>&1 | tail -1
    }
    log "setup ok"
    ;;
  prune)
    F="${2:?frac}"
    T=$(tag_of "$F")
    "$PY" -u "$ROOT/experiments/prune_ply.py" --in "$PLY" --out "$OUT/pruned_$T.ply" \
      --keep-frac "$F" --score volume 2>&1 | tail -1 | tee -a "$OUT/m39.log"
    ;;
  arm)
    F="${2:?frac}"; A="${3:?a|b}"; T=$(tag_of "$F")
    log "arm $T-$A: 12k steps, factor 4"
    t0=$(date +%s)
    "$PY" -u "$ROOT/research/code/scripts/train_gs.py" \
      --data "$COLMAP/$SCENE" --out "$OUT/${T}_$A" --factor 4 --steps "$STEPS" \
      --init_ply "$OUT/pruned_$T.ply" --no_densify --no_scene_scale --lr_scale 0.3 --grad_clip 1.0 \
      --sh_degree 3 --split interleaved --gt-convention archive --keep_all_views \
      --eval_every 2000 $(arm_flags "$A") > "$OUT/train_${T}_$A.log" 2>&1
    t1=$(date +%s)
    echo "wall_${T}_$A $((t1-t0)) s" >> "$OUT/m39_time.txt"
    tail -2 "$OUT/train_${T}_$A.log"
    ;;
  encode)
    F="${2:?frac}"; A="${3:?a|b}"; T=$(tag_of "$F")
    "$PY" -u "$ROOT/experiments/m24_alpha.py" --ply "$OUT/${T}_$A/point_cloud.ply" \
      --plans "$SPEC:16:48" --out "$OUT/enc_${T}_$A" --no-ply --no-legacy --suffix "_m39$T$A" \
      > "$OUT/encode_${T}_$A.log" 2>&1
    ls -l "$OUT/enc_${T}_$A"/*.gs1 | tee -a "$OUT/m39_sizes.txt"
    ;;
  render)
    F="${2:?frac}"; A="${3:?a|b}"; T=$(tag_of "$F")
    f=$(ls "$OUT/enc_${T}_$A"/*.gs1 | head -1)
    ply="$OUT/enc_${T}_$A/m39$T$A.ply"
    "$PY" -u "$ROOT/experiments/m19_codec.py" --to-ply "$f" --out "$ply" >> "$OUT/decode_${T}_$A.log" 2>&1
    "$PY" "$ROOT/experiments/make_m360_archive.py" --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
      --archive "$ARCH" --name "m39_$T$A" 2>&1 | tail -1
    r=$(bash "$ROOT/experiments/probe_render.sh" "m39_$T$A" 1 2>&1 | tail -1)
    echo "$T $A $(stat -c %s "$f") $r" | tee -a "$OUT/render.txt"
    rm -f "$ply"
    ;;
  all)
    for F in 0.15 0.10; do
      bash "$0" prune "$F"
      for A in a b; do
        bash "$0" arm "$F" "$A" || { log "arm $F $A failed"; continue; }
        bash "$0" encode "$F" "$A" || { log "encode $F $A failed"; continue; }
        bash "$0" render "$F" "$A" || log "render $F $A failed"
      done
    done
    cat "$OUT/render.txt" "$OUT/m39_time.txt"
    ;;
  *) echo "use setup|prune|arm|encode|render|all [frac] [a|b]" >&2; exit 2 ;;
esac
