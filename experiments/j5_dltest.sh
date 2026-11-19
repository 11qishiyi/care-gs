#!/usr/bin/env bash
# Measure aggregate download throughput from the HF mirror with N parallel connections.
# Usage: bash experiments/j5_dltest.sh [N]
set -uo pipefail
N="${1:-12}"
R='https://hf-mirror.com/datasets/alexmkwizu/gaussian_training_datasets/resolve/main/mipnerf360/bicycle/images_4'
mkdir -p /tmp/ptest
rm -rf /tmp/ptest/* 2>/dev/null || true
ls /root/mip360/bicycle/images_4 2>/dev/null | head -"$N" > /tmp/names.txt
if [ ! -s /tmp/names.txt ]; then
  echo "no local names to reuse; listing the repository instead"
  curl -sSL --max-time 60 \
    "https://hf-mirror.com/api/datasets/alexmkwizu/gaussian_training_datasets/tree/main/mipnerf360/bicycle/images_4" \
    | python3 -c "import json,sys;print('\n'.join(i['path'].split('/')[-1] for i in json.load(sys.stdin)[:$N]))" \
    > /tmp/names.txt
fi
echo "files: $(wc -l < /tmp/names.txt)"
t0=$(date +%s)
cat /tmp/names.txt | xargs -P "$N" -I{} curl -sSL --max-time 240 -o /tmp/ptest/{} "$R/{}"
t1=$(date +%s)
sz=$(du -sb /tmp/ptest | cut -f1)
dt=$((t1 - t0))
[ "$dt" -lt 1 ] && dt=1
echo "parallel$N: ${sz} B in ${dt}s => $((sz / dt)) B/s"
