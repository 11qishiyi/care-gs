#!/usr/bin/env bash
# J5 data pull that survives a throttled mirror.
#
# The mirror serves single connections at ~250-290 KB/s but scales to ~1.7 MB/s at 16-24 connections, so every
# large object is fetched as byte ranges in parallel and every small object with a 32-way xargs pool. Chunks are
# written to `<dest>.partN` and only concatenated once the byte count matches the expected size, so a truncated
# pull is loud instead of silently producing a corrupt PLY (this project has already been bitten once by a
# truncated images.bin).
#
#   bash experiments/j5_fetch_all.sh            # fetch + archives + render + pack
set -uo pipefail
cd /root/j5
export PYTHONPATH=/root/j5:/root/j5/research/code:/root/j5/experiments
MIR="${MIR:-https://hf-mirror.com/datasets}"
IMGREPO="$MIR/alexmkwizu/gaussian_training_datasets/resolve/main/mipnerf360"
PLYREPO="$MIR/dylanebert/3dgs/resolve/main"
DATA=/root/mip360
PLYDIR=/root/ply
NCHUNK="${NCHUNK:-24}"
NIMG="${NIMG:-32}"
log() { echo "[$(date +%H:%M:%S)] $*"; }

fetch_images() {
  local scene="$1"
  local d="$DATA/$scene"
  mkdir -p "$d/images_4" "$d/sparse/0"
  for f in cameras.bin images.bin points3D.bin; do
    [ -s "$d/sparse/0/$f" ] || curl -sSL --retry 5 -o "$d/sparse/0/$f" "$IMGREPO/$scene/sparse/0/$f"
  done
  curl -sSL --retry 5 "$MIR/alexmkwizu/gaussian_training_datasets/tree/main/mipnerf360/$scene/images_4" \
    -o "$d/list.json"
  python3 - "$d" <<'PY'
import json, os, sys
d = sys.argv[1]
items = json.load(open(os.path.join(d, "list.json"), encoding="utf-8"))
with open(os.path.join(d, "names.txt"), "w", encoding="utf-8") as fh:
    for it in items:
        if it.get("type") == "file":
            fh.write(it["path"].split("/")[-1] + "\t" + str(it.get("size", 0)) + "\n")
print(f"{len(open(os.path.join(d, 'names.txt')).readlines())} images listed")
PY
  t0=$(date +%s)
  awk -F'\t' '{print $1}' "$d/names.txt" | xargs -P "$NIMG" -I{} \
    sh -c "[ -s '$d/images_4/{}' ] || curl -sSL --retry 4 --max-time 300 -o '$d/images_4/{}.part' '$IMGREPO/$scene/images_4/{}' && [ -s '$d/images_4/{}.part' ] && mv '$d/images_4/{}.part' '$d/images_4/{}' || true"
  log "$scene images: $(ls "$d/images_4" | wc -l) files, $(du -sh "$d/images_4" | cut -f1) in $(( $(date +%s) - t0 ))s"
}

fetch_ply() {
  local scene="$1"
  local out="$PLYDIR/$scene.ply"
  local url="$PLYREPO/$scene/point_cloud/iteration_30000/point_cloud.ply"
  mkdir -p "$PLYDIR"
  if [ -s "$out" ]; then log "$scene ply cached $(du -h "$out" | cut -f1)"; return 0; fi
  local size
  size=$(curl -sSIL --max-time 90 "$url" | awk 'tolower($1)=="content-length:"{v=$2} END{gsub(/\r/,"",v); print v}')
  if [ -z "${size:-}" ] || [ "$size" -lt 1000000 ]; then log "$scene: cannot read size"; return 1; fi
  local chunk=$(( (size + NCHUNK - 1) / NCHUNK ))
  log "$scene ply: $size B in $NCHUNK chunks of $chunk B"
  local t0=$(date +%s)
  for i in $(seq 0 $((NCHUNK - 1))); do
    local s=$((i * chunk)); local e=$((s + chunk - 1))
    [ "$e" -ge "$size" ] && e=$((size - 1))
    ( curl -sSL --retry 4 --max-time 900 -r "$s-$e" -o "$out.part$i" "$url" ) &
  done
  wait
  cat $(for i in $(seq 0 $((NCHUNK - 1))); do echo "$out.part$i"; done) > "$out"
  rm -f "$out".part*
  local got=$(stat -c %s "$out")
  log "$scene ply: got $got / $size in $(( $(date +%s) - t0 ))s"
  [ "$got" = "$size" ]
}

log "=== images"
fetch_images bicycle
fetch_images stump

log "=== plies"
fetch_ply bicycle || { log "ply bicycle FAILED"; echo 7 > /root/j5.done; exit 7; }
fetch_ply stump   || { log "ply stump FAILED";   echo 7 > /root/j5.done; exit 7; }

log "=== archives"
for s in bicycle stump; do
  python3 experiments/make_m360_archive.py --scene-dir "$DATA/$s" --ply "$PLYDIR/$s.ply" \
    --archive /root/m360std --name "$s" --factor 4 --holdout 8 >> /root/j5_archive.log 2>&1 \
    || log "archive $s FAILED"
done
ls /root/m360std

log "=== render"
python3 experiments/j5_render.py --archive /root/m360std --scenes bicycle,stump \
  --variants clean,gp6-6-6_c8_sh6,gp6-6-6_c8_sh3,p50 \
  --out /root/res/j5 --factor 1 --gt-convention archive --device cuda > /root/j5_render.log 2>&1
rc=$?
log "render rc=$rc"
if [ "$rc" = "0" ]; then
  log "=== pack"
  python3 experiments/j5_pack.py --res /root/res/j5 --out /root/res/j5/pack > /root/j5_pack.log 2>&1
  rc=$?
  log "pack rc=$rc"
fi
echo "$rc" > /root/j5.done
log "done rc=$rc"
