#!/usr/bin/env bash
# J6 finisher #3: stump only, then archives -> dump -> audit (bicycle is already assembled and its archive built).
set -uo pipefail
cd /root/j6
export PYTHONPATH=/root/j6:/root/j6/research/code:/root/j6/experiments
log() { echo "[$(date +%H:%M:%S)] $*"; }
rm -f /root/j6.done

for attempt in 1 2 3; do
  log "stump attempt $attempt"
  NCHUNK=48 TRIES=24 bash experiments/j5_ply_resume.sh stump 1230527188 >> /root/j6_ply4.log 2>&1 && break
  sleep 5
done
if [ ! -s /root/ply/stump.ply ]; then log "stump still missing"; fi
ls -la /root/ply/*.ply 2>/dev/null

if [ -s /root/ply/stump.ply ]; then
  log "archive stump"
  python3 experiments/make_m360_archive.py --scene-dir /root/mip360/stump --ply /root/ply/stump.ply \
    --archive /root/m360std --name stump --factor 4 --holdout 8 >> /root/j6_arch.log 2>&1 \
    || log "archive stump FAILED"
fi
ls /root/m360std 2>/dev/null | head -5

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
