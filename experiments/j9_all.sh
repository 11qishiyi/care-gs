#!/usr/bin/env bash
# J9 overnight: measure the family law at several tolerances, two functionals and several scenes, plus the J8 arms.
#
# Runs unattended. Scenes are tried in priority order; a scene that does not download inside its budget is skipped and
# the run continues, so a slow mirror costs coverage of the grid, not the whole night.
#
#   nohup bash experiments/j9_all.sh > /root/j9_main.log 2>&1 &
set -uo pipefail
cd /root/j9
export PYTHONPATH=/root/j9:/root/j9/research/code:/root/j9/experiments
log() { echo "[$(date +%H:%M:%S)] $*"; }
rm -f /root/j9.done

PLY="https://hf-mirror.com/datasets/dylanebert/3dgs/resolve/main/bicycle/point_cloud/iteration_30000/point_cloud.ply"
PLY_REPO="https://hf-mirror.com/datasets/dylanebert/3dgs/resolve/main"

log "gate"
LOC=$(bash experiments/locof.sh "$PLY" || true)
if [ -z "${LOC:-}" ]; then log "gate FAILED (no signed url)"; echo 3 > /root/j9.done; exit 3; fi
t0=$(date +%s)
curl -sSL --max-time 60 -r 0-8388607 -o /tmp/s.bin "$LOC"
dt=$(( $(date +%s) - t0 + 1 ))
kbs=$(( $(stat -c %s /tmp/s.bin) / dt / 1024 ))
log "gate: throughput ${kbs} KB/s"
if [ "$kbs" -lt 500 ]; then log "gate FAILED (slow)"; echo 4 > /root/j9.done; exit 4; fi

log "deps"
python3 -m pip install -q packaging rich jaxtyping ninja plyfile zstandard scikit-image pillow \
  > /root/j9_pip.log 2>&1
python3 -m pip install -q "gsplat==1.5.3" --no-deps >> /root/j9_pip.log 2>&1
export TORCH_EXTENSIONS_DIR=/root/tx; mkdir -p /root/tx
python3 -c "import gsplat, torch; print('gsplat', gsplat.__version__, torch.__version__)" >> /root/j9_pip.log 2>&1 \
  || { log "gsplat FAILED"; echo 9 > /root/j9.done; exit 9; }

# priority order: the paper's two cross-paper assets first, then public scenes that the paper already treats as
# internal-only measurements (protocol-excluded for cross-paper comparison, valid for a family comparison)
SCENES_ALL="bicycle flowers bonsai counter"
SCENES_OK=""
for s in $SCENES_ALL; do
  log "scene $s: sparse + images"
  SCENES="$s" NIMG=6 timeout 1800 bash experiments/j9_data.sh > /root/j9_data_$s.log 2>&1
  n=$(ls "/root/mip360/$s/images_4" 2>/dev/null | wc -l)
  log "scene $s: $n images"
  if [ "$n" -lt 20 ]; then log "scene $s skipped (images)"; continue; fi

  log "scene $s: ply (resumable, 20 tries per chunk)"
  # the resumer needs the exact expected length, so ask the signed URL rather than trusting the redirect
  plurl="$PLY_REPO/$s/point_cloud/iteration_30000/point_cloud.ply"
  ploc=$(bash experiments/locof.sh "$plurl" || true)
  psz=""
  if [ -n "${ploc:-}" ]; then
    psz=$(curl -sSI --max-time 30 "$ploc" | awk 'tolower($1)=="content-length:"{gsub(/\r/,"",$2);print $2}')
  fi
  log "scene $s: ply expected ${psz:-unknown} B"
  if [ -z "${psz:-}" ]; then log "scene $s skipped (no size)"; continue; fi
  NCHUNK=48 TRIES=20 timeout 5400 bash experiments/j5_ply_resume.sh "$s" "$psz" > /root/j9_ply_$s.log 2>&1 \
    || log "scene $s: ply incomplete, continuing with what arrived"

  ply="/root/ply/$s.ply"
  if [ ! -s "$ply" ]; then log "scene $s skipped (no ply)"; continue; fi

  python3 experiments/make_m360_archive.py --scene-dir "/root/mip360/$s" --ply "$ply" \
    --archive /root/m360 --name "$s" --factor 4 --holdout 8 >> /root/j9_arch.log 2>&1 \
    || { log "scene $s archive FAILED"; continue; }
  SCENES_OK="$SCENES_OK $s"
done

log "scenes with archives:${SCENES_OK:- none}"
if [ -z "${SCENES_OK// /}" ]; then echo 6 > /root/j9.done; exit 6; fi

log "measure"
python3 experiments/j9_dump_quantiles.py --archive /root/m360 --scenes "${SCENES_OK// /,}" \
  --out /root/res/j9 > /root/j9_run.log 2>&1
rc=$?
log "measure rc=$rc"
tail -5 /root/j9_run.log
echo "$rc" > /root/j9.done
log "done rc=$rc"