#!/usr/bin/env bash
set -euo pipefail
CODE=/workspace/code
D=/workspace/data/mip360_colmap/bicycle
O=/workspace/data/nan
mkdir -p "$O/a" "$O/b" "$O/c"
cd "$CODE"
run() {
  PYTHONPATH="$CODE/research/code" python3 research/code/scripts/train_gs.py \
    --data "$D" --out "$O/$1" --factor 4 --steps 700 --sh_degree 3 \
    --split interleaved --gt-convention archive --keep_all_views \
    --refine_stop_frac 0.6 --eval_every 100000 "${@:2}" > "$O/$1/train.log" 2>&1 || true
}
run a --no_ssim &
run b --means_lr_fix 1.6e-5 &
run c &
wait
echo DONE_NAN