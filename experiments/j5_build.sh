#!/usr/bin/env bash
# J5 second half: pull the remaining PLY, build both archives, render the four arms, cut the patches.
# Separated from the download so a failed PLY can be resumed without redoing the archives or the render.
#
#   bash experiments/j5_build.sh
set -uo pipefail
cd /root/j5
export PYTHONPATH=/root/j5:/root/j5/research/code:/root/j5/experiments
PLYDIR=/root/ply
DATA=/root/mip360
log() { echo "[$(date +%H:%M:%S)] $*"; }
rm -f /root/j5.done

for pair in "bicycle 1520726124" "stump 1230527188"; do
  set -- $pair
  scene=$1; size=$2
  if [ -s "$PLYDIR/$scene.ply" ] && [ "$(stat -c %s "$PLYDIR/$scene.ply")" = "$size" ]; then
    log "$scene ply ok ($size B)"
  else
    log "$scene ply missing/incomplete -> fetch"
    NCHUNK=${NCHUNK:-48} bash experiments/j5_ply_resume.sh "$scene" "$size" >> /root/j5_ply3.log 2>&1 \
      || { log "$scene ply FAILED"; echo 7 > /root/j5.done; exit 7; }
  fi
done

for s in bicycle stump; do
  n=$(ls "$DATA/$s/images_4" 2>/dev/null | wc -l)
  log "$s: $n images on disk"
done

log "archives"
for s in bicycle stump; do
  python3 experiments/make_m360_archive.py --scene-dir "$DATA/$s" --ply "$PLYDIR/$s.ply" \
    --archive /root/m360std --name "$s" --factor 4 --holdout 8 >> /root/j5_archive.log 2>&1 \
    || { log "archive $s FAILED"; echo 6 > /root/j5.done; exit 6; }
done
ls -la /root/m360std

log "render"
python3 experiments/j5_render.py --archive /root/m360std --scenes bicycle,stump \
  --variants clean,gp6-6-6_c8_sh6,gp6-6-6_c8_sh3,p50 \
  --out /root/res/j5 --factor 1 --gt-convention archive --device cuda > /root/j5_render.log 2>&1
rc=$?
log "render rc=$rc"

if [ "$rc" = "0" ]; then
  log "pack"
  python3 experiments/j5_pack.py --res /root/res/j5 --out /root/res/j5/pack > /root/j5_pack.log 2>&1
  rc=$?
  log "pack rc=$rc"
fi
echo "$rc" > /root/j5.done
log "done rc=$rc"
