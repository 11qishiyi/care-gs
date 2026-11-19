#!/usr/bin/env bash
# J5 unattended setup + render on a fresh node. Writes /root/j5.done when finished.
# Protocol: experiments/J5_PLAN.md.  Everything is logged under /root/j5_*.log so a failure can be
# diagnosed from the pulled logs instead of a re-run.
set -uo pipefail
cd /root/j5
export PYTHONPATH=/root/j5:/root/j5/research/code:/root/j5/experiments
rm -f /root/j5.done
log() { echo "[$(date +%H:%M:%S)] $*"; }

log "pip base"
python3 -m pip install -q packaging rich jaxtyping ninja plyfile zstandard scikit-image lpips pillow \
  > /root/j5_pip.log 2>&1
python3 -m pip install -q "gsplat==1.5.3" --no-deps >> /root/j5_pip.log 2>&1
if ! python3 -c "import gsplat, torch; print('gsplat', gsplat.__version__, 'torch', torch.__version__)" \
     >> /root/j5_pip.log 2>&1; then
  log "gsplat import FAILED"; echo 9 > /root/j5.done; exit 9
fi
tail -1 /root/j5_pip.log

log "colmap + images_4"
ROOT=/root/mip360 SCENES=bicycle,stump JOBS=2 bash experiments/fetch_m360_colmap.sh \
  > /root/j5_colmap.log 2>&1 || { log "colmap fetch FAILED"; echo 8 > /root/j5.done; exit 8; }

log "released PLYs"
for s in bicycle stump; do
  MODELS=/root/models IMAGES=/root/mip360 bash experiments/fetch_hf_curl.sh "$s" iteration_30000 8 \
    > "/root/j5_ply_$s.log" 2>&1 || log "ply $s FAILED"
done
ls -la /root/models/output/*/point_cloud/iteration_30000/point_cloud.ply 2>/dev/null | tee -a /root/j5_setup.log

log "archives"
for s in bicycle stump; do
  python3 experiments/make_m360_archive.py --scene-dir "/root/mip360/$s" \
    --ply "/root/models/output/$s/point_cloud/iteration_30000/point_cloud.ply" \
    --archive /root/m360std --name "$s" --factor 4 --holdout 8 \
    >> /root/j5_archive.log 2>&1 || log "archive $s FAILED"
done

log "render"
python3 experiments/j5_render.py --archive /root/m360std --scenes bicycle,stump \
  --variants clean,gp6-6-6_c8_sh6,gp6-6-6_c8_sh3,p50 \
  --out /root/res/j5 --factor 1 --gt-convention archive --device cuda \
  > /root/j5_render.log 2>&1
rc=$?
echo "$rc" > /root/j5.done
log "done rc=$rc"
