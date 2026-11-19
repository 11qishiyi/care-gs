#!/usr/bin/env bash
# M20 setup: the two reference models and the zstd binding.  No images, no GT -- the probe
# re-arranges bytes that already exist, and fidelity is checked by decoding the codes back
# and comparing arrays, not by rendering.
#
# huggingface.co is reset from this node (curl: (35) ... Connection reset by peer); the
# hf-mirror endpoint answers at ~2 MB/s, which is enough for 2.7 GB.
set -uo pipefail

DATA=${DATA:-/workspace/data/m20}
MIRROR=${MIRROR:-https://hf-mirror.com}
mkdir -p "$DATA"

python -c 'import zstandard' 2>/dev/null || pip install -q zstandard

fetch() {
  s=$1
  f="$DATA/$s.ply"
  if [ -s "$f" ]; then
    echo "[$s] present $(stat -c%s "$f") B"
    return 0
  fi
  url="$MIRROR/datasets/dylanebert/3dgs/resolve/main/$s/point_cloud/iteration_30000/point_cloud.ply"
  echo "[$s] fetching $url"
  curl -sL --retry 3 --retry-delay 5 --max-time 5400 -o "$f.part" "$url"
  sz=$(stat -c%s "$f.part" 2>/dev/null || echo 0)
  if [ "$sz" -lt 100000000 ]; then
    echo "[$s] FAILED ($sz B)"
    rm -f "$f.part"
    return 1
  fi
  mv "$f.part" "$f"
  echo "[$s] $sz B"
}

for s in ${SCENES:-bicycle stump}; do
  fetch "$s" &
done
wait
ls -l "$DATA"
