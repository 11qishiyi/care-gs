#!/usr/bin/env bash
set -euo pipefail
CODE=/workspace/code
D=/workspace/data/mip360_colmap/bicycle
O=/workspace/data/norm
mkdir -p "$O"
run_one() {
  local name="$1"; shift
  mkdir -p "$O/$name"
  cd "$CODE"
  PYTHONPATH="$CODE/research/code" python3 research/code/scripts/train_gs.py \
    --data "$D" --out "$O/$name" --factor 4 --steps 6000 --sh_degree 3 \
    --split interleaved --gt-convention archive --keep_all_views \
    --refine_stop_frac 0.6 --eval_every 2000 --normalize_scene "$@" \
    > "$O/$name/train.log" 2>&1
}
run_one n1 &
run_one n2 --grow_grad2d 5e-5 &
wait
echo DONE_NORM