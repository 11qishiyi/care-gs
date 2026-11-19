#!/usr/bin/env bash
# M37 -- the rate pressure on the full model, where the headline number lives.
#
#   bash experiments/run_m37.sh arm a|b     # fine-tune the published model, 12k steps, factor 4
#   bash experiments/run_m37.sh encode a|b  # container at the M35 shipping configuration
#   bash experiments/run_m37.sh render a|b  # PSNR on the 25 held-out views
#   bash experiments/run_m37.sh all
#
# arm a = plain (control: what 12k steps of factor-4 fine-tuning do by themselves)
# arm b = same + the 5 %-share log rate term from M36 (lambda recalibrated at step 0, then frozen)
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m37
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
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/m37.log"; }
PLY="$DATA/m20/$SCENE.ply"

arm_flags() {
  case "$1" in
    a) echo "" ;;
    b) echo "--rate-lambda -1 --rate-kind log --rate-groups shN,sh0,scales,opacities --rate_share 0.05" ;;
    *) echo "arm must be a or b" >&2; exit 2 ;;
  esac
}

case "${1:-all}" in
  arm)
    A="${2:?arm a|b}"
    log "arm $A on the full model: $STEPS steps, factor 4"
    t0=$(date +%s)
    "$PY" -u "$ROOT/research/code/scripts/train_gs.py" \
      --data "$COLMAP/$SCENE" --out "$OUT/arm_$A" --factor 4 --steps "$STEPS" \
      --init_ply "$PLY" --no_densify --no_scene_scale --lr_scale 0.3 --grad_clip 1.0 \
      --sh_degree 3 --split interleaved --gt-convention archive --keep_all_views \
      --eval_every 2000 $(arm_flags "$A") > "$OUT/train_$A.log" 2>&1
    t1=$(date +%s)
    echo "wall_$A $((t1-t0)) s" >> "$OUT/m37_time.txt"
    tail -2 "$OUT/train_$A.log"
    ;;
  encode)
    A="${2:?arm a|b}"
    "$PY" -u "$ROOT/experiments/m24_alpha.py" --ply "$OUT/arm_$A/point_cloud.ply" \
      --plans "$SPEC:16:48" --out "$OUT/enc_$A" --no-ply --no-legacy --suffix "_m37$A" \
      > "$OUT/encode_$A.log" 2>&1
    ls -l "$OUT/enc_$A"/*.gs1 | tee -a "$OUT/m37_sizes.txt"
    ;;
  render)
    A="${2:?arm a|b}"
    f=$(ls "$OUT/enc_$A"/*.gs1 | head -1)
    ply="$OUT/enc_$A/m37$A.ply"
    "$PY" -u "$ROOT/experiments/m19_codec.py" --to-ply "$f" --out "$ply" >> "$OUT/decode_$A.log" 2>&1
    "$PY" "$ROOT/experiments/make_m360_archive.py" --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
      --archive "$ARCH" --name "m37_$A" 2>&1 | tail -1
    r=$(bash "$ROOT/experiments/probe_render.sh" "m37_$A" 1 2>&1 | tail -1)
    echo "$A $(stat -c %s "$f") $r" | tee -a "$OUT/render.txt"
    rm -f "$ply"
    ;;
  all)
    for A in a b; do
      bash "$0" arm "$A" || { log "arm $A failed"; continue; }
      bash "$0" encode "$A" || { log "encode $A failed"; continue; }
      bash "$0" render "$A" || log "render $A failed"
    done
    cat "$OUT/render.txt" "$OUT/m37_time.txt"
    ;;
  *) echo "use arm|encode|render|all <arm>" >&2; exit 2 ;;
esac
