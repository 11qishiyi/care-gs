#!/usr/bin/env bash
# Train the 3DGS baseline ourselves on the published Mip-NeRF 360 protocol.
#
# Protocol (Kerbl et al. 2023, as used by HAC / PCGS / every compression paper):
#   * images_4, i.e. 1/4 linear resolution
#   * 30 000 iterations, SH degree 3, densification 500..15 000, opacity reset every 3 000
#   * every 8th view (i % 8 == 0, sorted by file name) held out; never optimised
#   * raw sRGB targets, 0.8 * L1 + 0.2 * (1 - SSIM)
#
# Hyper-parameters are the reference ones: densify_grad_threshold 0.0002, prune_opa 0.005,
# lr means 1.6e-4 * extent decaying to 1.6e-6, scales 5e-3, quats 1e-3, opacity 5e-2, SH 2.5e-3.
set -euo pipefail
COLMAP="${COLMAP:-/workspace/data/mip360_colmap}"
OUT="${OUT:-/workspace/data/m360_selftrain}"
SCENES="${SCENES:-bicycle,garden,stump,room,counter,kitchen,bonsai}"
STEPS="${STEPS:-30000}"
JOBS="${JOBS:-2}"
CODE="${CODE:-/workspace/code}"

log() { echo "[$(date +%H:%M:%S)] $*"; }
mkdir -p "$OUT"

train_one() {
  scene="$1"
  d="$COLMAP/$scene"
  o="$OUT/$scene"
  if [ -f "$o/point_cloud.ply" ] && [ -f "$o/DONE" ]; then
    log "$scene: cached ($(du -h "$o/point_cloud.ply" | cut -f1))"
    return 0
  fi
  mkdir -p "$o"
  log "$scene: training $STEPS steps"
  cd "$CODE"
  PYTHONPATH="$CODE/research/code" python3 research/code/scripts/train_gs.py \
    --data "$d" --out "$o" --factor 4 --steps "$STEPS" --sh_degree 3 \
    --split interleaved --gt-convention archive --keep_all_views \
    --grow_grad2d 0.0002 --refine_stop_frac 0.5 --eval_every 5000 \
    > "$o/train.log" 2>&1
  touch "$o/DONE"
  grep -E "^\[final\]|^DONE" "$o/train.log" | tail -2
  log "$scene: done"
}

export -f train_one log
export COLMAP OUT STEPS CODE

echo "$SCENES" | tr ',' '\n' | xargs -P "$JOBS" -I{} bash -c 'train_one "$@"' _ {}
log "all scenes trained"
for s in ${SCENES//,/ }; do
  [ -f "$OUT/$s/point_cloud.ply" ] && printf '%-10s %s %s\n' "$s" "$(du -h "$OUT/$s/point_cloud.ply" | cut -f1)" "$(grep -h '^\[final\]' "$OUT/$s/train.log" | tail -1)"
done
