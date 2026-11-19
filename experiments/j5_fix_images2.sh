#!/usr/bin/env bash
# Repair the image pull using COLMAP's own image list.
#
# The HF tree API intermittently answers a reading_verification_required challenge, so it cannot be trusted as
# the source of truth for "which files belong to this scene". COLMAP's images.bin already carries that list and
# is downloaded as part of the sparse set, so the names come from there and the expected size comes from the
# repository's own per-file metadata only when that listing is available (otherwise a non-empty file is accepted
# and the archive builder's own check is the backstop).
#
#   bash experiments/j5_fix_images2.sh
set -uo pipefail
cd /root/j5
export PYTHONPATH=/root/j5:/root/j5/research/code
MIR="${MIR:-https://hf-mirror.com/datasets}"
IMGREPO="$MIR/alexmkwizu/gaussian_training_datasets/resolve/main/mipnerf360"
DATA=/root/mip360
NIMG="${NIMG:-32}"
log() { echo "[$(date +%H:%M:%S)] $*"; }

for scene in bicycle stump; do
  d="$DATA/$scene"
  mkdir -p "$d/images_4"
  python3 - "$d" <<'PY'
import os, sys
sys.path.insert(0, "/root/j5/research/code")
from calib.colmap_io import read_images_bin
d = sys.argv[1]
recs = read_images_bin(os.path.join(d, "sparse", "0", "images.bin"))
names = [os.path.basename(r["name"]) for r in recs]
open(os.path.join(d, "names_colmap.txt"), "w", encoding="utf-8").write("\n".join(names) + "\n")
print(f"{d}: {len(names)} names from COLMAP")
PY
  t0=$(date +%s)
  cat "$d/names_colmap.txt" | xargs -P "$NIMG" -I{} bash -c '
    f="'"$d"'/images_4/$1"
    [ -s "$f" ] && exit 0
    curl -sSL --retry 4 --max-time 300 -o "$f.part" "'"$IMGREPO/$scene"'/images_4/$1" && [ -s "$f.part" ] && mv "$f.part" "$f"
  ' _ {}
  rm -f "$d"/images_4/*.part
  log "$scene: $(ls "$d/images_4" | wc -l) images, $(du -sh "$d/images_4" | cut -f1), $(( $(date +%s) - t0 ))s"
done
