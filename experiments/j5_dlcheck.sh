#!/usr/bin/env bash
# Decide whether the J5 data pull is feasible: (a) does the mirror honour Range requests, (b) what is the
# single-stream byte rate on the big PLY, (c) does aggregate throughput keep scaling with more connections.
set -uo pipefail
PLY='https://hf-mirror.com/datasets/dylanebert/3dgs/resolve/main/bicycle/point_cloud/iteration_30000/point_cloud.ply'
IMG='https://hf-mirror.com/datasets/alexmkwizu/gaussian_training_datasets/resolve/main/mipnerf360/bicycle/images_4'

echo "== HEAD on the PLY"
curl -sSI --max-time 40 "$PLY" | grep -Ei 'HTTP/|content-length|accept-ranges' | head -5

echo "== 1 MB range request"
t0=$(date +%s.%N)
code=$(curl -sS --max-time 90 -r 0-1048575 -o /tmp/range.bin -w '%{http_code}' "$PLY")
t1=$(date +%s.%N)
sz=$(stat -c %s /tmp/range.bin 2>/dev/null || echo 0)
python3 - "$code" "$sz" "$t0" "$t1" <<'PY'
import sys
code, sz, t0, t1 = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
dt = max(1e-3, t1 - t0)
print(f"http={code} bytes={sz} {dt:.1f}s => {sz/dt/1024:.0f} KB/s")
PY

echo "== 8 parallel range chunks of 4 MB each"
t0=$(date +%s)
for i in $(seq 0 7); do
  s=$((i * 4194304)); e=$((s + 4194303))
  curl -sS --max-time 180 -r "$s-$e" -o "/tmp/chunk_$i.bin" "$PLY" &
done
wait
t1=$(date +%s)
sz=$(du -cb /tmp/chunk_*.bin | tail -1 | cut -f1)
dt=$((t1 - t0)); [ "$dt" -lt 1 ] && dt=1
echo "parallel8-range: ${sz} B in ${dt}s => $((sz / dt / 1024)) KB/s"

echo "== 32 parallel small images"
rm -rf /tmp/ptest2; mkdir -p /tmp/ptest2
curl -sSL --max-time 60 \
  "https://hf-mirror.com/api/datasets/alexmkwizu/gaussian_training_datasets/tree/main/mipnerf360/bicycle/images_4" \
  | python3 -c "import json,sys;print('\n'.join(i['path'].split('/')[-1] for i in json.load(sys.stdin)[:32]))" \
  > /tmp/names32.txt
t0=$(date +%s)
cat /tmp/names32.txt | xargs -P 32 -I{} curl -sSL --max-time 300 -o /tmp/ptest2/{} "$IMG/{}"
t1=$(date +%s)
sz=$(du -sb /tmp/ptest2 | cut -f1)
dt=$((t1 - t0)); [ "$dt" -lt 1 ] && dt=1
echo "parallel32-images: ${sz} B in ${dt}s => $((sz / dt / 1024)) KB/s"
