#!/usr/bin/env bash
# J6, second attempt --- with the gate first.
#
# The first attempt (instance 2143578) failed on the data source: the mirror answered 502 and then 429 to every
# ranged request, and a single stream ran at 43 KB/s. Lesson written into J6_RESULTS.md: **probe the通路 before
# doing anything expensive**, and treat 502 (upstream broken) and 429 (our IP throttled) differently.
#
# So this script starts with a gate that must be passed before a single byte of the 2.7 GB is requested:
#   * a 1 MiB ranged request must return 206 (not 302/429/502);
#   * 8 parallel ranged requests must aggregate >= 300 KB/s.
# If the gate fails it exits 3 without touching the archives, and the caller releases the node.
#
#   bash experiments/j6_all.sh
set -uo pipefail
cd /root/j6
export PYTHONPATH=/root/j6:/root/j6/research/code:/root/j6/experiments
log() { echo "[$(date +%H:%M:%S)] $*"; }
rm -f /root/j6.done

PLY="https://hf-mirror.com/datasets/dylanebert/3dgs/resolve/main/bicycle/point_cloud/iteration_30000/point_cloud.ply"

log "gate: ranged request"
code=$(curl -sSL --max-time 60 -r 0-1048575 -o /tmp/gate.bin -w '%{http_code}' "$PLY")
bytes=$(stat -c %s /tmp/gate.bin 2>/dev/null || echo 0)
log "gate: http=$code bytes=$bytes"
if [ "$code" != "206" ] || [ "$bytes" -lt 1000000 ]; then
  log "gate FAILED (mirror not serving ranges)"; echo 3 > /root/j6.done; exit 3
fi

log "gate: 8-way throughput"
rm -rf /tmp/g8; mkdir -p /tmp/g8
t0=$(date +%s)
for i in $(seq 0 7); do
  s=$((i * 4194304)); e=$((s + 4194303))
  ( curl -sSL --max-time 120 -r "$s-$e" -o "/tmp/g8/$i.bin" "$PLY" ) &
done
wait
t1=$(date +%s); sz=$(du -sb /tmp/g8 | cut -f1); dt=$((t1 - t0)); [ "$dt" -lt 1 ] && dt=1
kbs=$((sz / dt / 1024))
log "gate: ${sz} B in ${dt}s => ${kbs} KB/s"
rm -rf /tmp/g8
if [ "$kbs" -lt 300 ]; then
  log "gate FAILED (too slow: ${kbs} KB/s)"; echo 4 > /root/j6.done; exit 4
fi

log "deps"
python3 -m pip install -q packaging rich jaxtyping ninja plyfile zstandard scikit-image pillow > /root/j6_pip.log 2>&1
python3 -m pip install -q "gsplat==1.5.3" --no-deps >> /root/j6_pip.log 2>&1
python3 -c "import gsplat, torch; print('gsplat', gsplat.__version__, torch.__version__)" >> /root/j6_pip.log 2>&1 \
  || { log "gsplat FAILED"; echo 9 > /root/j6.done; exit 9; }

log "sparse + images"
bash experiments/j6_fetch_sparse_images.sh > /root/j6_img.log 2>&1 || log "image stage reported a problem"

log "PLYs"
NCHUNK=48 TRIES=20 bash experiments/j5_ply_resume.sh bicycle 1520726124 > /root/j6_ply.log 2>&1 \
  || { log "ply bicycle FAILED"; echo 7 > /root/j6.done; exit 7; }
NCHUNK=48 TRIES=20 bash experiments/j5_ply_resume.sh stump 1230527188 >> /root/j6_ply.log 2>&1 \
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
