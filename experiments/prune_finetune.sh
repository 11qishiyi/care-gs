#!/usr/bin/env bash
# M17 pilot: prune to a fraction, write a PLY, finetune it without densification, and report the
# clean PSNR before and after.  Pruning alone costs several dB; the finetune is what has to buy
# them back at a fifth of the primitives.
#
#   bash experiments/prune_finetune.sh bicycle_mirror 0.2 2500
set -euo pipefail
SCENE="${1:?scene}"
KEEP="${2:-0.2}"
STEPS="${3:-2500}"
CODE=/workspace/code
ARCH=/workspace/data/m360std
OUT=/workspace/res/m17/$SCENE
COLMAP=/workspace/data/mip360_colmap
CANON="${SCENE%_mirror}"
mkdir -p "$OUT"
cd "$CODE"

PLY="$ARCH/output/$SCENE/point_cloud/iteration_40000/point_cloud.ply"
[ -e "$PLY" ] || PLY=$(ls "$ARCH/output/$SCENE"/point_cloud/*/point_cloud.ply | head -1)

PYTHONPATH="$CODE/research/code:/workspace/code" python3 experiments/prune_ply.py \
  --in "$PLY" --out "$OUT/pruned.ply" --keep-frac "$KEEP" --score volume 2>&1 | tail -2

PYTHONPATH="$CODE/research/code:/workspace/code" python3 experiments/make_m360_archive.py \
  --scene-dir "$COLMAP/$CANON" --ply "$OUT/pruned.ply" \
  --archive "$ARCH" --name "${SCENE}_k${KEEP}" 2>&1 | tail -2

bash experiments/probe_render.sh "${SCENE}_k${KEEP}" 1 2>&1 | tail -2

PYTHONPATH="$CODE/research/code" python3 research/code/scripts/train_gs.py \
  --data "$COLMAP/$CANON" --out "$OUT/ft" --factor 4 --steps "$STEPS" --sh_degree 3 \
  --split interleaved --gt-convention archive --keep_all_views \
  --init_ply "$OUT/pruned.ply" --no_densify --eval_every 1000 ${EXTRA:-} \
  > "$OUT/ft.log" 2>&1
grep -e final -e WROTE "$OUT/ft.log" | tail -2

PYTHONPATH="$CODE/research/code:/workspace/code" python3 experiments/make_m360_archive.py \
  --scene-dir "$COLMAP/$CANON" --ply "$OUT/ft/point_cloud.ply" \
  --archive "$ARCH" --name "${SCENE}_ft" 2>&1 | tail -1
bash experiments/probe_render.sh "${SCENE}_ft" 1 2>&1 | tail -2
echo "M17_PILOT_DONE $SCENE"