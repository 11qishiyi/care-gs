#!/usr/bin/env bash
# J6 finisher #2: the last two bicycle chunks, then stump, then the missing images, then archives -> dump -> audit.
#
# The CAS bridge served most ranges at ~2 MB/s but stalled on two of the 48 bicycle chunks (~40 KB/s each, then a
# 500 s timeout), so `j6_cas_fetch.sh` reported the PLY incomplete. Ranges are resumable, and each retry asks the
# mirror for a *fresh* signed URL, so a stalled chunk is retried rather than restarted.
#
#   bash experiments/j6_finish2.sh
set -uo pipefail
cd /root/j6
export PYTHONPATH=/root/j6:/root/j6/research/code:/root/j6/experiments
log() { echo "[$(date +%H:%M:%S)] $*"; }
rm -f /root/j6.done

log "bicycle resume"
NCHUNK=48 TRIES=20 bash experiments/j5_ply_resume.sh bicycle 1520726124 >> /root/j6_ply3.log 2>&1 \
  || { log "bicycle still incomplete"; }
log "stump"
NCHUNK=48 TRIES=20 bash experiments/j5_ply_resume.sh stump 1230527188 >> /root/j6_ply3.log 2>&1 \
  || { log "stump incomplete"; }

log "image top-up"
NIMG=4 bash experiments/j6_fix_data.sh >> /root/j6_data3.log 2>&1 || true

for s in bicycle stump; do
  n=$(ls "/root/mip360/$s/images_4" 2>/dev/null | wc -l)
  log "$s: $n images"
done

log "archives"
for s in bicycle stump; do
  python3 experiments/make_m360_archive.py --scene-dir "/root/mip360/$s" --ply "/root/ply/$s.ply" \
    --archive /root/m360std --name "$s" --factor 4 --holdout 8 >> /root/j6_arch.log 2>&1 \
    || log "archive $s FAILED"
done
ls /root/m360std 2>/dev/null | head -4

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
