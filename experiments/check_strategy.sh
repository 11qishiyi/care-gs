#!/usr/bin/env bash
# Two-way strategy check on bicycle at 6 000 steps: absolute densification thresholds (historical)
# versus scene-relative ones.  Ranked by the held-out PSNR of the *saved PLY*, which is the number
# that matters and the one the in-training eval was not giving us (the writer used to emit an
# empty PLY, so nothing could be re-rendered from disk).
#
#   bash experiments/check_strategy.sh 6000
set -euo pipefail
STEPS="${1:-6000}"
CODE=/workspace/code
D=/workspace/data/mip360_colmap/bicycle
O=/workspace/data/strat
mkdir -p "$O"

run_one() {
  local name="$1"; shift
  local out="$O/$name"
  mkdir -p "$out"
  cd "$CODE"
  PYTHONPATH="$CODE/research/code" python3 research/code/scripts/train_gs.py \
    --data "$D" --out "$out" --factor 4 --steps "$STEPS" --sh_degree 3 \
    --split interleaved --gt-convention archive --keep_all_views \
    --refine_stop_frac 0.6 --eval_every 2000 "$@" > "$out/train.log" 2>&1
  echo "done $name"
}

run_one abs --grow_grad2d 5e-5 --strategy_scene_scale 1 &
run_one rel --grow_grad2d 5e-5 --strategy_scene_scale auto --prune_scale3d 0.02 &
run_one rel2 --grow_grad2d 5e-5 --strategy_scene_scale auto --prune_scale3d 0.02 --grow_scale3d 0.002 &
wait
echo "=== strategy check ==="
for d in "$O"/abs "$O"/rel "$O"/rel2; do
  echo "== $(basename "$d")"
  grep -e strategy -e 'final' -e WROTE "$d/train.log" | tail -3
done
