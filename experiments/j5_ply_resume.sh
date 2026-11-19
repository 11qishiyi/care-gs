#!/usr/bin/env bash
# Resume-safe PLY fetch: each byte range is retried with `curl -C -` until the part file reaches its exact
# expected length, so a connection that stalls at 30 MB of 63 MB costs one retry instead of the whole file.
#
#   bash experiments/j5_ply_resume.sh bicycle 1520726124
#   bash experiments/j5_ply_resume.sh stump   1228738356
set -uo pipefail
MIR="${MIR:-https://hf-mirror.com/datasets}"
PLYREPO="$MIR/dylanebert/3dgs/resolve/main"
PLYDIR=/root/ply
NCHUNK="${NCHUNK:-48}"
TRIES="${TRIES:-14}"
scene="${1:?scene}"
size="${2:?size}"
url="$PLYREPO/$scene/point_cloud/iteration_30000/point_cloud.ply"
out="$PLYDIR/$scene.ply"
mkdir -p "$PLYDIR"
log() { echo "[$(date +%H:%M:%S)] $*"; }

if [ -s "$out" ] && [ "$(stat -c %s "$out")" = "$size" ]; then log "$scene: already complete"; exit 0; fi
chunk=$(( (size + NCHUNK - 1) / NCHUNK ))
log "$scene: $size B, $NCHUNK chunks of $chunk B, $TRIES tries each"

for i in $(seq 0 $((NCHUNK - 1))); do
  s=$((i * chunk))
  e=$((s + chunk - 1))
  [ "$e" -ge "$size" ] && e=$((size - 1))
  want=$((e - s + 1))
  part="$out.part$i"
  (
    for t in $(seq 1 "$TRIES"); do
      have=$(stat -c %s "$part" 2>/dev/null || echo 0)
      [ "$have" -eq "$want" ] && break
      [ "$have" -gt "$want" ] && rm -f "$part" && have=0
      curl -sSL --max-time 420 -r $((s + have))-"$e" -o "$part.tmp" "$url" 2>/dev/null
      cat "$part.tmp" >> "$part" 2>/dev/null || true
      rm -f "$part.tmp"
      now=$(stat -c %s "$part" 2>/dev/null || echo 0)
      [ "$now" -ge "$want" ] && break
      sleep 2
    done
    now=$(stat -c %s "$part" 2>/dev/null || echo 0)
    echo "[$(date +%H:%M:%S)] chunk $i: $now/$want"
  ) &
  # keep the pool bounded so the mirror does not throttle every connection at once
  while [ "$(jobs -rp | wc -l)" -ge 10 ]; do sleep 2; done
done
wait

ok=1
for i in $(seq 0 $((NCHUNK - 1))); do
  s=$((i * chunk)); e=$((s + chunk - 1)); [ "$e" -ge "$size" ] && e=$((size - 1))
  want=$((e - s + 1)); have=$(stat -c %s "$out.part$i" 2>/dev/null || echo 0)
  [ "$have" -ne "$want" ] && { echo "chunk $i short: $have/$want"; ok=0; }
done
if [ "$ok" = "1" ]; then
  cat $(for i in $(seq 0 $((NCHUNK - 1))); do echo "$out.part$i"; done) > "$out"
  rm -f "$out".part*
  log "$scene: assembled $(stat -c %s "$out") / $size"
  [ "$(stat -c %s "$out")" = "$size" ]
else
  log "$scene: incomplete, keeping parts"
  exit 1
fi
