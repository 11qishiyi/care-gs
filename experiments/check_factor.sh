#!/usr/bin/env bash
# The COLMAP mirrors already ship images_4, so --factor must be 1.  Training at factor 4 fits a
# 309x205 model that is then rendered at 1236x822: the result is a blur that scores 8.7 dB, which
# is what looked like a broken trainer.
set -euo pipefail
CODE=/workspace/code
D=/workspace/data/mip360_colmap/bicycle
O=/workspace/data/fac1
mkdir -p "$O/b1"
cd "$CODE"
PYTHONPATH="$CODE/research/code" python3 research/code/scripts/train_gs.py \
  --data "$D" --out "$O/b1" --factor 1 --steps 3000 --sh_degree 3 \
  --split interleaved --gt-convention archive --keep_all_views \
  --refine_stop_frac 0.6 --eval_every 1000 --grow_grad2d 5e-5 \
  > "$O/b1/train.log" 2>&1
echo DONE_FAC1