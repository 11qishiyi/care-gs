#!/usr/bin/env bash
# J6 second half: wait for the image fetch to quiesce, then finish the PLYs and run archives -> dump -> audit.
#
# The first full run failed at the PLY stage because the image fetch (32-way) and the PLY fetch (10-way) were
# competing for the mirror's per-connection budget: ten of the 48 chunks came back empty and the chunk loop
# exhausted its retries. Serialising the two fixes it; the existing 48-chunk parts are reused as-is, so
# NCHUNK must stay 48.
#
#   bash experiments/j6_finish.sh
set -uo pipefail
cd /root/j6
export PYTHONPATH=/root/j6:/root/j6/research/code:/root/j6/experiments
log() { echo "[$(date +%H:%M:%S)] $*"; }
rm -f /root/j6.done

log "waiting for the image fetch"
for i in $(seq 1 60); do
  if ! pgrep -f "j5_fix_images2" > /dev/null; then break; fi
  sleep 10
done
log "images: bicycle $(ls /root/mip360/bicycle/images_4 2>/dev/null | wc -l) / stump $(ls /root/mip360/stump/images_4 2>/dev/null | wc -l)"

log "ply bicycle"
NCHUNK=48 TRIES=20 bash experiments/j5_ply_resume.sh bicycle 1520726124 >> /root/j6_ply2.log 2>&1 \
  || { log "ply bicycle FAILED"; echo 7 > /root/j6.done; exit 7; }
log "ply stump"
NCHUNK=48 TRIES=20 bash experiments/j5_ply_resume.sh stump 1230527188 >> /root/j6_ply2.log 2>&1 \
  || { log "ply stump FAILED"; echo 7 > /root/j6.done; exit 7; }

log "archives"
for s in bicycle stump; do
  python3 experiments/make_m360_archive.py --scene-dir "/root/mip360/$s" --ply "/root/ply/$s.ply" \
    --archive /root/m360std --name "$s" --factor 4 --holdout 8 >> /root/j6_arch.log 2>&1 \
    || log "archive $s FAILED"
done

log "dump"
python3 experiments/dump_artifacts.py --archive /root/m360std --scenes bicycle,stump \
  --variants clean,prune50,prune30,shdeg1,quant8,quant6,quant4 \
  --out /root/dump --factor 1 --gt-convention archive --device cuda --budget-mb 2000 \
  > /root/j6_dump.log 2>&1
rc=$?
log "dump rc=$rc"
if [ "$rc" = "0" ]; then
  log "audit"
  python3 experiments/audit_bound.py --npz /root/dump --out /root/audit_single.json --save-splits \
    > /root/j6_audit.log 2>&1
  rc=$?
  log "audit rc=$rc"
fi
echo "$rc" > /root/j6.done
log "done rc=$rc"
