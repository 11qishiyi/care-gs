#!/usr/bin/env bash
# Build archive entries for the self-trained BungeeNeRF scenes and audit them.
# Assumes training finished: /workspace/data/selftrain/<scene>/point_cloud.ply
set -eu
cd /workspace/code
ARCH=/workspace/data/selftrain_archive
REC=/workspace/res/selftrain
SCENES=${SCENES:-"barcelona bilbao chicago"}
mkdir -p "$REC"

for s in $SCENES; do
  name="${s}_st"
  python experiments/make_selftrain_archive.py \
      --scene-dir "/data/bungeenerf/bungeenerf/$s" \
      --ply "/workspace/data/selftrain/$s/point_cloud.ply" \
      --archive "$ARCH" --name "$name" --factor 4 2>&1 | tail -4
done

SCENE_LIST=$(echo $SCENES | tr ' ' '\n' | sed 's/$/_st/' | paste -sd, -)
echo "dumping: $SCENE_LIST"
python experiments/dump_artifacts.py --archive "$ARCH" --out "$REC/dump" \
    --scenes "$SCENE_LIST" \
    --variants clean,prune50,prune30,shdeg1,quant8,quant6,quant4 \
    --profile full --gt-convention archive --factor 4 --device cuda --budget-mb 900 2>&1 | tail -8

bash experiments/run_per_scene.sh "$REC/dump" "$REC" 3 2>&1 | tail -12
echo SELFTRAIN_AUDIT_DONE
