#!/usr/bin/env bash
# Repair the image pull: the HF tree API needs `?recursive=true` (without it the mirror answers a
# reading_verification_required challenge and the name list comes back empty), and files that were already
# downloaded must be size-checked before they are treated as done.
#
#   bash experiments/j5_fix_images.sh
set -uo pipefail
MIR="${MIR:-https://hf-mirror.com/datasets}"
IMGREPO="$MIR/alexmkwizu/gaussian_training_datasets/resolve/main/mipnerf360"
DATA=/root/mip360
NIMG="${NIMG:-32}"
log() { echo "[$(date +%H:%M:%S)] $*"; }

for scene in bicycle stump; do
  d="$DATA/$scene"
  mkdir -p "$d/images_4"
  curl -sSL --retry 5 --max-time 180 \
    "$MIR/alexmkwizu/gaussian_training_datasets/tree/main/mipnerf360/$scene/images_4?recursive=true" \
    -o "$d/list.json"
  python3 - "$d" <<'PY'
import json, os, sys
d = sys.argv[1]
items = json.load(open(os.path.join(d, "list.json"), encoding="utf-8"))
if not isinstance(items, list):
    raise SystemExit(f"listing is not a list: {str(items)[:120]}")
rows = [(it["path"].split("/")[-1], int(it.get("size", 0))) for it in items if it.get("type") == "file"]
with open(os.path.join(d, "names.txt"), "w", encoding="utf-8") as fh:
    for n, s in rows:
        fh.write(f"{n}\t{s}\n")
print(f"{d}: {len(rows)} images, {sum(s for _, s in rows)/1e6:.0f} MB")
PY
  t0=$(date +%s)
  awk -F'\t' '{print $1"\t"$2}' "$d/names.txt" | xargs -P "$NIMG" -I{} bash -c '
    line="$1"; name="${line%%$'"'"'\t'"'"'*}"; size="${line##*$'"'"'\t'"'"'}"
    f="'"$d"'/images_4/$name"
    if [ -s "$f" ] && [ "$(stat -c %s "$f")" = "$size" ]; then exit 0; fi
    curl -sSL --retry 4 --max-time 300 -o "$f.part" "'"$IMGREPO"'/'"$scene"'/images_4/$name" \
      && [ "$(stat -c %s "$f.part" 2>/dev/null || echo 0)" = "$size" ] && mv "$f.part" "$f"
  ' _ {}
  rm -f "$d"/images_4/*.part
  log "$scene: $(ls "$d/images_4" | wc -l) images, $(du -sh "$d/images_4" | cut -f1), $(( $(date +%s) - t0 ))s"
done
