#!/usr/bin/env bash
# J6 data fetch through the CAS bridge --- the mirror's own redirect is broken from MatPool's network.
#
# Diagnosis from instance 2143825: `https://hf-mirror.com/...` answers **502** to the node, but the signed
# `cas-bridge.xethub.hf.co` URL it points at answers **206** at ~100 KB/s. So the fix is not "wait for the
# mirror", it is **resolve the redirect once and download from the CAS URL directly**.
#
# Every transfer therefore costs one HEAD (for the signed URL) plus the body. PLYs are pulled as 48 byte ranges
# with 10 in flight (the CAS bridge throttles per connection but scales with connection count), images with 32.
#
#   bash experiments/j6_cas_fetch.sh          # images + PLYs + archives + dump + audit
set -uo pipefail
cd /root/j6
export PYTHONPATH=/root/j6:/root/j6/research/code:/root/j6/experiments
log() { echo "[$(date +%H:%M:%S)] $*"; }
rm -f /root/j6.done
MIR="${MIR:-https://hf-mirror.com/datasets}"
IMGREPO="$MIR/alexmkwizu/gaussian_training_datasets/resolve/main/mipnerf360"
PLYREPO="$MIR/dylanebert/3dgs/resolve/main"
DATA=/root/mip360
PLYDIR=/root/ply
NIMG="${NIMG:-28}"
NCHUNK="${NCHUNK:-48}"

loc_of() {   # signed CAS url for one mirror url
  curl -sSI --max-time 30 "$1" | awk 'tolower($1)=="location:"{v=$2} END{gsub(/\r/,"",v);print v}'
}

fetch_img() {  # fetch_img <mirror-url> <dest>
  local dst="$2"
  [ -s "$dst" ] && return 0
  local loc; loc=$(loc_of "$1")
  [ -z "${loc:-}" ] && return 1
  curl -sSL --retry 3 --max-time 300 -o "$dst.part" "$loc" && [ -s "$dst.part" ] && mv "$dst.part" "$dst"
}
export -f loc_of fetch_img
export MIR IMGREPO

log "=== images (sparse first)"
for s in bicycle stump; do
  d="$DATA/$s"; mkdir -p "$d/sparse/0" "$d/images_4"
  for f in cameras.bin images.bin points3D.bin; do
    [ -s "$d/sparse/0/$f" ] || fetch_img "$IMGREPO/$s/sparse/0/$f" "$d/sparse/0/$f"
    log "$s/$f $(stat -c %s "$d/sparse/0/$f" 2>/dev/null || echo 0) B"
  done
  python3 - "$d" <<'PY'
import os, sys
sys.path.insert(0, "/root/j6/research/code")
from calib.colmap_io import read_images_bin
d = sys.argv[1]
recs = read_images_bin(os.path.join(d, "sparse", "0", "images.bin"))
names = [os.path.basename(r["name"]) for r in recs]
open(os.path.join(d, "names_colmap.txt"), "w").write("\n".join(names) + "\n")
print(f"{d}: {len(names)} names")
PY
  t0=$(date +%s)
  cat "$d/names_colmap.txt" | xargs -P "$NIMG" -I{} bash -c 'fetch_img "'"$IMGREPO/$s"'/images_4/{}" "'"$d"'/images_4/{}"' \
    || true
  rm -f "$d"/images_4/*.part
  log "$s images: $(ls "$d/images_4" | wc -l) files in $(( $(date +%s) - t0 ))s"
done

fetch_ply() {   # fetch_ply <scene> <size>
  local scene="$1" size="$2"
  local out="$PLYDIR/$scene.ply"
  local url="$PLYREPO/$scene/point_cloud/iteration_30000/point_cloud.ply"
  mkdir -p "$PLYDIR"
  if [ -s "$out" ] && [ "$(stat -c %s "$out")" = "$size" ]; then log "$scene ply cached"; return 0; fi
  local chunk=$(( (size + NCHUNK - 1) / NCHUNK ))
  log "$scene ply: $size B, $NCHUNK chunks"
  local t0=$(date +%s)
  for i in $(seq 0 $((NCHUNK - 1))); do
    local s=$((i * chunk)); local e=$((s + chunk - 1))
    [ "$e" -ge "$size" ] && e=$((size - 1))
    (
      local part="$out.part$i" want=$((e - s + 1))
      for t in $(seq 1 12); do
        local have; have=$(stat -c %s "$part" 2>/dev/null || echo 0)
        [ "$have" -eq "$want" ] && break
        [ "$have" -gt "$want" ] && rm -f "$part" && have=0
        local loc; loc=$(loc_of "$url")
        [ -z "${loc:-}" ] && { sleep 2; continue; }
        curl -sSL --max-time 500 -r $((s + have))-"$e" -o "$part.tmp" "$loc" || true
        cat "$part.tmp" >> "$part" 2>/dev/null || true
        rm -f "$part.tmp"
      done
      echo "[$(date +%H:%M:%S)] $scene chunk $i: $(stat -c %s "$part" 2>/dev/null || echo 0)/$want"
    ) &
    while [ "$(jobs -rp | wc -l)" -ge 10 ]; do sleep 2; done
  done
  wait
  local ok=1
  for i in $(seq 0 $((NCHUNK - 1))); do
    local s=$((i * chunk)); local e=$((s + chunk - 1)); [ "$e" -ge "$size" ] && e=$((size - 1))
    local want=$((e - s + 1)) have=$(stat -c %s "$out.part$i" 2>/dev/null || echo 0)
    [ "$have" -ne "$want" ] && { echo "chunk $i short $have/$want"; ok=0; }
  done
  [ "$ok" = "1" ] || { log "$scene ply INCOMPLETE"; return 1; }
  cat $(for i in $(seq 0 $((NCHUNK - 1))); do echo "$out.part$i"; done) > "$out"
  rm -f "$out".part*
  log "$scene ply: assembled $(stat -c %s "$out") B in $(( $(date +%s) - t0 ))s"
  [ "$(stat -c %s "$out")" = "$size" ]
}

log "=== PLYs"
fetch_ply bicycle 1520726124 || { echo 7 > /root/j6.done; exit 7; }
fetch_ply stump   1230527188 || { echo 7 > /root/j6.done; exit 7; }

log "=== archives"
for s in bicycle stump; do
  python3 experiments/make_m360_archive.py --scene-dir "$DATA/$s" --ply "$PLYDIR/$s.ply" \
    --archive /root/m360std --name "$s" --factor 4 --holdout 8 >> /root/j6_arch.log 2>&1 \
    || log "archive $s FAILED"
done

log "=== dump"
python3 experiments/dump_artifacts.py --archive /root/m360std --scenes bicycle,stump \
  --variants clean,prune50,prune30,shdeg1,quant8,quant6,quant4 \
  --out /root/dump --factor 1 --gt-convention archive --device cuda --budget-mb 2000 \
  > /root/j6_dump.log 2>&1
rc=$?
log "dump rc=$rc"
if [ "$rc" = "0" ]; then
  log "=== audit"
  python3 experiments/audit_bound.py --npz /root/dump --out /root/audit_single.json --save-splits \
    > /root/j6_audit.log 2>&1
  rc=$?
  log "audit rc=$rc"
fi
echo "$rc" > /root/j6.done
log "done rc=$rc"
