#!/usr/bin/env bash
# Densification sweep: which grow_grad2d / grow_scale3d reaches the reference primitive count and
# PSNR on bicycle within a fixed step budget?  6 000 steps is enough to rank the settings, and it
# costs ~7 minutes each instead of ~40.
#
#   bash experiments/sweep_densify.sh <node-tag> <steps> <settings...>
#   bash experiments/sweep_densify.sh a 6000 "5e-5:0.01" "2e-5:0.01" "5e-5:0.005"
set -euo pipefail
TAG="${1:?tag}"
STEPS="${2:-6000}"
shift 2
CODE=/workspace/code
D=/workspace/data/mip360_colmap/bicycle
O=/workspace/data/sweep_$TAG
mkdir -p "$O"

run_one() {
  local spec="$1"
  local grad="${spec%%:*}"
  local gs="${spec##*:}"
  local name="g${grad}_s${gs}"
  local out="$O/$name"
  mkdir -p "$out"
  cd "$CODE"
  PYTHONPATH="$CODE/research/code" python3 research/code/scripts/train_gs.py \
    --data "$D" --out "$out" --factor 4 --steps "$STEPS" --sh_degree 3 \
    --split interleaved --gt-convention archive --keep_all_views \
    --grow_grad2d "$grad" --grow_scale3d "$gs" --refine_stop_frac 0.6 \
    --eval_every 2000 > "$out/train.log" 2>&1
  echo "== $name: $(grep -h '^\[final\]' "$out/train.log" | tail -1) n=$(grep -o 'n= *[0-9]*' "$out/train.log" | tail -1)"
}

for spec in "$@"; do
  run_one "$spec" &
done
wait
echo "=== sweep $TAG done ==="
for d in "$O"/*/; do
  printf '%-22s %s\n' "$(basename "$d")" "$(grep -h '^\[final\]' "$d/train.log" | tail -1)"
done
