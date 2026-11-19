#!/usr/bin/env bash
# Second pass: the PLY endpoint answers 302, so every probe needs -L. Measures single-stream and
# 8-way parallel range throughput on the real 1.5 GB file.
set -uo pipefail
PLY='https://hf-mirror.com/datasets/dylanebert/3dgs/resolve/main/bicycle/point_cloud/iteration_30000/point_cloud.ply'

echo "== follow redirect, HEAD"
curl -sSIL --max-time 60 "$PLY" | grep -Ei 'HTTP/|content-length|accept-ranges' | tail -6

echo "== 4 MB range, single stream"
t0=$(date +%s.%N)
code=$(curl -sSL --max-time 120 -r 0-4194303 -o /tmp/r1.bin -w '%{http_code}' "$PLY")
t1=$(date +%s.%N)
sz=$(stat -c %s /tmp/r1.bin 2>/dev/null || echo 0)
python3 - "$code" "$sz" "$t0" "$t1" <<'PY'
import sys
code, sz, t0, t1 = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
dt = max(1e-3, t1 - t0)
print(f"single: http={code} bytes={sz} {dt:.1f}s => {sz/dt/1024:.0f} KB/s")
PY

echo "== 8 parallel 8 MB ranges"
rm -f /tmp/pc_*.bin
t0=$(date +%s)
for i in $(seq 0 7); do
  s=$((i * 8388608)); e=$((s + 8388607))
  curl -sSL --max-time 300 -r "$s-$e" -o "/tmp/pc_$i.bin" "$PLY" &
done
wait
t1=$(date +%s)
sz=$(du -cb /tmp/pc_*.bin | tail -1 | cut -f1)
dt=$((t1 - t0)); [ "$dt" -lt 1 ] && dt=1
echo "parallel8: ${sz} B in ${dt}s => $((sz / dt / 1024)) KB/s"

echo "== 16 parallel 8 MB ranges"
rm -f /tmp/pd_*.bin
t0=$(date +%s)
for i in $(seq 0 15); do
  s=$((i * 8388608)); e=$((s + 8388607))
  curl -sSL --max-time 300 -r "$s-$e" -o "/tmp/pd_$i.bin" "$PLY" &
done
wait
t1=$(date +%s)
sz=$(du -cb /tmp/pd_*.bin | tail -1 | cut -f1)
dt=$((t1 - t0)); [ "$dt" -lt 1 ] && dt=1
echo "parallel16: ${sz} B in ${dt}s => $((sz / dt / 1024)) KB/s"
