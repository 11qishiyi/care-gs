#!/usr/bin/env bash
# Sparse + images for an arbitrary scene list, one file at a time through `casget.sh`.
# Adapted from `j6_fix_data.sh`, which hardcoded bicycle/stump; here the scene list comes from $SCENES so the same
# script can serve J8 and J9.
#
#   SCENES="bicycle flowers" bash experiments/j9_data.sh
set -uo pipefail
cd /root/j9 || exit 1
export PYTHONPATH=/root/j9:/root/j9/research/code
MIR="${MIR:-https://hf-mirror.com/datasets}"
IMGREPO="$MIR/alexmkwizu/gaussian_training_datasets/resolve/main/mipnerf360"
DATA=/root/mip360
NIMG="${NIMG:-6}"
SCENES="${SCENES:-bicycle}"
log() { echo "[$(date +%H:%M:%S)] $*"; }

for s in $SCENES; do
  d="$DATA/$s"
  mkdir -p "$d/sparse/0" "$d/images_4"
  for f in cameras.bin images.bin points3D.bin; do
    bash experiments/casget.sh "$IMGREPO/$s/sparse/0/$f" "$d/sparse/0/$f" || true
    log "$s/$f $(stat -c %s "$d/sparse/0/$f" 2>/dev/null || echo MISSING) B"
  done
  python3 - "$d" <<'PY'
import os, sys
sys.path.insert(0, "/root/j9/research/code")
from calib.colmap_io import read_images_bin
d = sys.argv[1]
recs = read_images_bin(os.path.join(d, "sparse", "0", "images.bin"))
open(os.path.join(d, "names_colmap.txt"), "w").write(
    "\n".join(os.path.basename(r["name"]) for r in recs) + "\n")
print(f"{d}: {len(recs)} names")
PY
  t0=$(date +%s)
  cat "$d/names_colmap.txt" | xargs -P "$NIMG" -I{} \
    bash experiments/casget.sh "$IMGREPO/$s/images_4/{}" "$d/images_4/{}" || true
  rm -f "$d"/images_4/*.part
  log "$s: $(ls "$d/images_4" 2>/dev/null | wc -l) images in $(( $(date +%s) - t0 ))s"
done
log "data done"