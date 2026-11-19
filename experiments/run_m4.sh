#!/usr/bin/env bash
# M4: measure the preregistered byte model against a real codec (zstd, level 12).
# Runs on the node after (or alongside) the M3 dump: it only needs the PLY files.
set -u
cd /workspace/code || exit 2
ARCH=/workspace/data/out3dgs
OUT=/workspace/res/m4
SCENES=${SCENES:-bicycle,flowers,stump,treehill}
SPECS=${SPECS:-clean,sh4_g16,m16_o8_sh3,m16_o6_sh2,p30}
LEVEL=${LEVEL:-12}
mkdir -p "$OUT"
python -u experiments/m4_bytes.py \
  --archive "$ARCH" \
  --scenes "$SCENES" \
  --specs "$SPECS" \
  --level "$LEVEL" \
  --out "$OUT/m4_bytes.json"
echo "=== m4 finished with $? ==="
