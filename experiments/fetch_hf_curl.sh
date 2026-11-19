#!/usr/bin/env bash
# curl-based replacement for fetch_hf_data.py on this node (urllib gets EADDRNOTAVAIL
# against hf-mirror; curl is fine).  Downloads the released 3DGS checkpoint(s) and the
# held-out ground-truth views, in the layout build_archive.py expects:
#   <models>/output/<scene>/cameras.json
#   <models>/output/<scene>/point_cloud/iteration_<N>/point_cloud.ply
#   <images>/<scene>/images/<stem>.JPG   (held-out only, llffhold=8)
set -eu
HF=${HF_ENDPOINT:-https://hf-mirror.com}
NB=$HF/datasets/nvs-bench/mipnerf360/resolve/main
MODELS=${MODELS:-/workspace/data/models}
IMAGES=${IMAGES:-/workspace/data/mip360}
SCENE=${1:-bonsai}
ITERS=${2:-"iteration_30000 iteration_7000"}
HOLD=${3:-8}

out=$MODELS/output/$SCENE
mkdir -p "$out" "$IMAGES/$SCENE/images"
echo "[$SCENE] cameras.json"
curl -sSL --retry 3 -o "$out/cameras.json" "$HF/datasets/dylanebert/3dgs/resolve/main/$SCENE/cameras.json"

for it in $ITERS; do
  dst="$out/point_cloud/$it/point_cloud.ply"
  mkdir -p "$(dirname "$dst")"
  if [ -s "$dst" ]; then echo "[$SCENE] $it cached $(du -h "$dst" | cut -f1)"; continue; fi
  echo "[$SCENE] $it downloading"
  curl -sSL --retry 3 -o "$dst.part" "$HF/datasets/dylanebert/3dgs/resolve/main/$SCENE/point_cloud/$it/point_cloud.ply"
  mv "$dst.part" "$dst"
  echo "[$SCENE] $it $(du -h "$dst" | cut -f1)"
done

python - "$out/cameras.json" "$IMAGES" "$SCENE" "$HOLD" <<'PY' > /tmp/${SCENE}_stems.txt
import json, os, sys
cams = json.load(open(sys.argv[1], encoding="utf-8"))
cams.sort(key=lambda c: c["img_name"])
hold = int(sys.argv[4])
sel = [cams[i] for i in range(len(cams)) if i % hold == 0]
for c in sel:
    print(os.path.splitext(os.path.basename(c["img_name"]))[0])
PY

n=0; ok=0
while read -r stem; do
  n=$((n+1))
  dst="$IMAGES/$SCENE/images/$stem.JPG"
  [ -s "$dst" ] && { ok=$((ok+1)); continue; }
  for ext in JPG jpg png; do
    if curl -sSfL --retry 2 -o "$dst" "$NB/$SCENE/images/$stem.$ext"; then ok=$((ok+1)); break; fi
    rm -f "$dst"
  done
done < /tmp/${SCENE}_stems.txt
echo "[$SCENE] gt views $ok/$n"
echo "CURLFETCH_DONE $SCENE"
