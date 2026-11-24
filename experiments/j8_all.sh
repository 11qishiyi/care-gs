#!/usr/bin/env bash
# J8 --- does a coverage-aware pruning score rescue pruning?  One command, unattended.
#
# Depends on the instrument built and self-tested on 2026-11-20:
#   experiments/j8_run.py   the score (8 CPU checks pass; top-50% overlaps opacity by only 53%)
#   experiments/j8_run.py     prune -> render -> coverage/PSNR per (scene, keep, score)
#   experiments/j8_report.py  the pre-registered verdict (5 checks pass)
#
# Data path is the one that worked on 2026-11-19: the mirror's redirect is unreliable from MatPool, so every file
# goes HEAD -> signed CAS URL -> body (`experiments/casget.sh`), sparse before images, PLY as resumable ranges.
#
#   bash experiments/j8_all.sh
set -uo pipefail
cd /root/j8
export PYTHONPATH=/root/j8:/root/j8/research/code:/root/j8/experiments
log() { echo "[$(date +%H:%M:%S)] $*"; }
rm -f /root/j8.done

PLY="https://hf-mirror.com/datasets/dylanebert/3dgs/resolve/main/bicycle/point_cloud/iteration_30000/point_cloud.ply"

log "gate"
LOC=$(bash experiments/locof.sh "$PLY" || true)
if [ -z "${LOC:-}" ]; then log "gate FAILED (no signed url)"; echo 3 > /root/j8.done; exit 3; fi
code=$(curl -sSL --max-time 60 -r 0-1048575 -o /tmp/g.bin -w '%{http_code}' "$LOC")
bytes=$(stat -c %s /tmp/g.bin 2>/dev/null || echo 0)
log "gate: cas http=$code bytes=$bytes"
if [ "$code" != "206" ] || [ "$bytes" -lt 1000000 ]; then
  log "gate FAILED (no 206)"; echo 3 > /root/j8.done; exit 3
fi
# Throughput gate: the 2026-11-23 round died at 100 KB/s, where 1.52 GB is five hours. Refuse to start below 700 KB/s.
t0=$(date +%s)
curl -sSL --max-time 60 -r 0-8388607 -o /tmp/s.bin "$LOC"
dt=$(( $(date +%s) - t0 + 1 ))
kbs=$(( $(stat -c %s /tmp/s.bin) / dt / 1024 ))
log "gate: throughput ${kbs} KB/s"
if [ "$kbs" -lt 700 ]; then log "gate FAILED (slow)"; echo 4 > /root/j8.done; exit 4; fi

log "deps"
python3 -m pip install -q packaging rich jaxtyping ninja plyfile zstandard scikit-image pillow \
  > /root/j8_pip.log 2>&1
python3 -m pip install -q "gsplat==1.5.3" --no-deps >> /root/j8_pip.log 2>&1
export TORCH_EXTENSIONS_DIR=/root/tx; mkdir -p /root/tx
python3 -c "import gsplat, torch; print('gsplat', gsplat.__version__, torch.__version__)" >> /root/j8_pip.log 2>&1 \
  || { log "gsplat FAILED"; echo 9 > /root/j8.done; exit 9; }

log "data: sparse + images"
bash experiments/j6_fix_data.sh > /root/j8_data.log 2>&1 || log "image stage reported a problem"
for s in bicycle stump; do log "$s images: $(ls /root/mip360/$s/images_4 2>/dev/null | wc -l)"; done

log "data: PLYs"
NCHUNK=48 TRIES=20 bash experiments/j5_ply_resume.sh bicycle 1520726124 > /root/j8_ply.log 2>&1 \
  || log "bicycle ply incomplete"
NCHUNK=48 TRIES=20 bash experiments/j5_ply_resume.sh stump 1230527188 >> /root/j8_ply.log 2>&1 \
  || log "stump ply incomplete"
ls -la /root/ply/*.ply 2>/dev/null

log "archives"
for s in bicycle stump; do
  [ -s "/root/ply/$s.ply" ] || { log "skip $s (no ply)"; continue; }
  python3 experiments/make_m360_archive.py --scene-dir "/root/mip360/$s" --ply "/root/ply/$s.ply" \
    --archive /root/m360std --name "$s" --factor 4 --holdout 8 >> /root/j8_arch.log 2>&1 \
    || log "archive $s FAILED"
done

scenes=$(ls /root/m360std/output 2>/dev/null | tr '\n' ',' | sed 's/,$//')
log "scenes with archives: ${scenes:-none}"
if [ -z "${scenes:-}" ]; then echo 6 > /root/j8.done; exit 6; fi

log "run"
python3 experiments/j8_run.py --archive /root/m360std --scenes "$scenes" \
  --keeps 1.0,0.9,0.7,0.5 --out /root/res/j8 > /root/j8_run.log 2>&1
rc=$?
log "run rc=$rc"
echo "$rc" > /root/j8.done
log "done rc=$rc"
