#!/usr/bin/env bash
set -euo pipefail
CODE=/workspace/code
D=/workspace/data/mip360_colmap/bicycle
O=/workspace/data/fac2
mkdir -p "$O/a" "$O/b"
cd "$CODE"
run() {
  PYTHONPATH="$CODE/research/code" python3 research/code/scripts/train_gs.py \
    --data "$D" --out "$O/$1" --factor 4 --steps 6000 --sh_degree 3 \
    --split interleaved --gt-convention archive --keep_all_views \
    --refine_stop_frac 0.6 --eval_every 2000 "${@:2}" > "$O/$1/train.log" 2>&1
}
run a --grow_grad2d 5e-5 --normalize_scene &
run b --grow_grad2d 2e-4 &
wait
echo DONE_FAC2