#!/usr/bin/env bash
# J6 --- measure the single-pass audit for real.
#
# The manuscript now says the 56/56 of Table 8 is the *split-averaged* decision, and that a single pass,
# with its 2.0 pp error, would mis-decide some cells; the numbers for that claim were a Gaussian model. This
# round replaces the model with a measurement on the cells we can still rebuild: the two cross-paper assets
# (bicycle, stump) x the six dose-sweep edits, with the per-split (audit estimate, true loss) pairs dumped.
#
# The four *_i7k twins of the original 56-cell grid no longer exist (they were trained on a released node), so a
# faithful 56-cell re-run is impossible; the paper will report the measured subset and keep the model for the rest.
#
#   bash experiments/j6_singlepass.sh
set -uo pipefail
cd /root/j6
export PYTHONPATH=/root/j6:/root/j6/research/code:/root/j6/experiments
log() { echo "[$(date +%H:%M:%S)] $*"; }
rm -f /root/j6.done

log "deps"
python3 -m pip install -q packaging rich jaxtyping ninja plyfile zstandard scikit-image pillow \
  > /root/j6_pip.log 2>&1
python3 -m pip install -q "gsplat==1.5.3" --no-deps >> /root/j6_pip.log 2>&1
if ! python3 -c "import gsplat, torch; print('gsplat', gsplat.__version__, torch.__version__)" >> /root/j6_pip.log 2>&1; then
  log "gsplat import FAILED"; echo 9 > /root/j6.done; exit 9
fi
tail -1 /root/j6_pip.log

log "images + sparse"
bash experiments/j5_fix_images2.sh > /root/j6_img.log 2>&1 || log "image fetch reported a problem"

log "released PLYs"
NCHUNK=48 bash experiments/j5_ply_resume.sh bicycle 1520726124 > /root/j6_ply.log 2>&1 \
  || { log "ply bicycle FAILED"; echo 7 > /root/j6.done; exit 7; }
NCHUNK=48 bash experiments/j5_ply_resume.sh stump 1230527188 >> /root/j6_ply.log 2>&1 \
  || { log "ply stump FAILED"; echo 7 > /root/j6.done; exit 7; }

log "archives"
for s in bicycle stump; do
  python3 experiments/make_m360_archive.py --scene-dir "/root/mip360/$s" --ply "/root/ply/$s.ply" \
    --archive /root/m360std --name "$s" --factor 4 --holdout 8 >> /root/j6_arch.log 2>&1 \
    || log "archive $s FAILED"
done

log "dump (6 edits + clean, residual dumps)"
python3 experiments/dump_artifacts.py --archive /root/m360std --scenes bicycle,stump \
  --variants clean,prune50,prune30,shdeg1,quant8,quant6,quant4 \
  --out /root/dump --factor 1 --gt-convention archive --device cuda --budget-mb 2000 \
  > /root/j6_dump.log 2>&1
rc=$?
log "dump rc=$rc"

if [ "$rc" = "0" ]; then
  log "audit with per-split pairs"
  python3 experiments/audit_bound.py --npz /root/dump --out /root/audit_single.json --save-splits \
    > /root/j6_audit.log 2>&1
  rc=$?
  log "audit rc=$rc"
fi
echo "$rc" > /root/j6.done
log "done rc=$rc"
