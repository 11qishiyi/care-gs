#!/usr/bin/env bash
# Extension runs on the rented A40 (node 2138004).  Stage-wise, resumable, logs to /data/runs/.
#   bash /workspace/code/experiments/run_ext.sh stage1   # alias scenes @7k
#   bash /workspace/code/experiments/run_ext.sh stage2   # bonsai archive entry (HF mirror)
#   bash /workspace/code/experiments/run_ext.sh stage3   # PUP/Fisher top-30% PLY per scene
#   bash /workspace/code/experiments/run_ext.sh stage4   # GPU dump (all scenes x variants)
set -u
cd /workspace/code || exit 1
export HF_ENDPOINT=https://hf-mirror.com
ARCH=/workspace/data/out3dgs
REC=/workspace/res/rev
mkdir -p "$REC" /data/runs
LOG=/data/runs/$1.log
exec > >(tee -a "$LOG") 2>&1
echo "=== $(date -Is) $1 ==="

# scenes that should have a GPU dump: four released 40k checkpoints, their 7k twins,
# and bonsai (30k + 7k) as a fifth scene.
SCENES_40K="bicycle,flowers,stump,treehill"
SCENES_7K="bicycle_i7k,flowers_i7k,stump_i7k,treehill_i7k"
SCENES_ALL="$SCENES_40K,$SCENES_7K,bonsai,bonsai_i7k"
VARIANTS="clean,prune50,prune30,shdeg1,quant8,quant4,quant6"

case "$1" in
  stage1)
    python experiments/prep_aliases.py --archive "$ARCH" --scenes "bicycle,flowers,stump,treehill" --src-iter iteration_7000
    ;;
  stage2)
    # bonsai: fetch 30k checkpoint + held-out GT from the HF mirror, then stitch an
    # archive-shaped entry (build_archive reads <models>/output/<scene> and <images>/<scene>)
    python experiments/fetch_hf_data.py --scenes bonsai \
        --models /workspace/data/models --images /workspace/data/mip360
    python experiments/build_archive.py --models /workspace/data/models --images /workspace/data/mip360 \
        --archive "$ARCH" --scenes bonsai --iter-name iteration_30000 --report /data/runs/archive_bonsai.json
    python experiments/prep_aliases.py --archive "$ARCH" --scenes bonsai --src-iter iteration_7000
    ;;
  stage3)
    python experiments/make_pup_variant.py --archive "$ARCH" --out-dir "$REC/pup" \
        --scenes "$SCENES_ALL" --device cuda --n-views 4
    ;;
  stage4)
    python experiments/dump_artifacts.py --archive "$ARCH" --out "$REC/dump" \
        --pup-dir "$REC/pup" --scenes "$SCENES_ALL" --variants "$VARIANTS" \
        --profile full --device cuda --budget-mb 60
    ;;
  *)
    echo "unknown stage: $1"; exit 2;;
esac
echo "EXIT=$? $(date -Is)"
