#!/usr/bin/env bash
# J4 — coverage-rate sweep on the rented A100 (instance 2142563), unattended.
#
# Waits for the COLMAP/images_4 fetch, links the cached PLYs from /mnt/m35cache into an archive
# in the layout qfp_rd expects, then runs the J4 container ladder on bicycle + stump with
# per-view residuals dumped, so coverage / view-level coverage / audit error can be computed.
set -uo pipefail
cd /root/j4
export PYTHONPATH=/root/j4
log() { echo "[$(date +%H:%M:%S)] $*"; }

log "start; waiting for images"
for i in $(seq 1 180); do
  nb=$(ls /root/mip360/bicycle/images_4 2>/dev/null | wc -l)
  ns=$(ls /root/mip360/stump/images_4 2>/dev/null | wc -l)
  log "images bicycle=$nb stump=$ns"
  if [ "$nb" -ge 190 ] && [ "$ns" -ge 120 ]; then log "images ready"; break; fi
  sleep 60
done

for s in bicycle stump; do
  ply=/mnt/m35cache/$s.ply
  [ -f "$ply" ] || { log "missing ply $ply"; continue; }
  log "archive $s <- $ply"
  python make_m360_archive.py --scene-dir /root/mip360/$s --ply "$ply" \
      --archive /root/m360std --name "$s" --factor 4 --holdout 8 \
      && log "archive $s ok" || log "archive $s FAILED"
done

log "sweep start"
python qfp_rd.py --archive /root/m360std --scenes bicycle,stump --variant-set j4 \
    --out /root/res/j4 --factor 4 --gt-convention archive --device cuda \
    --budget-mb 2000 --fidelity --lpips-net alex > /root/j4_sweep.log 2>&1
rc=$?
log "sweep rc=$rc"
echo "$rc" > /root/j4.done
log "done"
