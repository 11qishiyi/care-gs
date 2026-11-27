#!/usr/bin/env bash
# Close J9's C4 by training a scene ourselves.
#
# The public mirrors only carry a PLY for bicycle/bonsai/stump, so a second *new* scene cannot be borrowed. The scenes
# whose images are mirrored (garden, kitchen, room) can still be trained here, which is the same provenance the paper's
# own i7k twins had: a 3DGS trained in-house at the protocol resolution.
#
#   SCENE=garden STEPS=7000 bash experiments/j9_train_scene.sh
set -uo pipefail
cd /root/j9
export PYTHONPATH=/root/j9:/root/j9/research/code:/root/j9/experiments
export TORCH_EXTENSIONS_DIR=/root/tx
SCENE="${SCENE:-garden}"
STEPS="${STEPS:-7000}"
log() { echo "[$(date +%H:%M:%S)] $*"; }
rm -f "/root/train_$SCENE.done"

log "data"
SCENES="$SCENE" NIMG=6 timeout 2400 bash experiments/j9_data.sh > "/root/train_${SCENE}_data.log" 2>&1
n=$(ls "/root/mip360/$SCENE/images_4" 2>/dev/null | wc -l)
log "images: $n"
[ "$n" -lt 30 ] && { echo 2 > "/root/train_$SCENE.done"; exit 2; }

log "train $STEPS steps"
cd /root/j9/research/code/gsplat
python3 examples/simple_trainer.py default \
  --data_dir "/root/mip360/$SCENE" --data_factor 4 \
  --result_dir "/root/train/$SCENE" --max_steps "$STEPS" --eval_steps 0 \
  > "/root/train_${SCENE}.log" 2>&1
rc=$?
log "train rc=$rc"
[ "$rc" -ne 0 ] && { tail -20 "/root/train_${SCENE}.log"; echo 3 > "/root/train_$SCENE.done"; exit 3; }

ply=$(ls -S "/root/train/$SCENE"/ply/*.ply 2>/dev/null | head -1)
log "ply: ${ply:-none}"
[ -z "${ply:-}" ] && { echo 4 > "/root/train_$SCENE.done"; exit 4; }

log "archive"
cd /root/j9
python3 experiments/make_m360_archive.py --scene-dir "/root/mip360/$SCENE" --ply "$ply" \
  --archive /root/m360 --name "$SCENE" --factor 4 --holdout 8 >> "/root/train_${SCENE}_arch.log" 2>&1 \
  || { log "archive FAILED"; echo 5 > "/root/train_$SCENE.done"; exit 5; }

log "measure"
python3 experiments/j9_dump_quantiles.py --archive /root/m360 --scenes "$SCENE" --reduction mean \
  --out /root/res/j9 > "/root/train_${SCENE}_mean.log" 2>&1
python3 experiments/j9_dump_quantiles.py --archive /root/m360 --scenes "$SCENE" --reduction max \
  --out /root/res/j9 > "/root/train_${SCENE}_max.log" 2>&1
ls -la "/root/res/j9/${SCENE}"*.npz 2>/dev/null
echo 0 > "/root/train_$SCENE.done"
log "done"