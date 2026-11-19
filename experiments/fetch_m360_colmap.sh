#!/usr/bin/env bash
# Fetch the Mip-NeRF 360 scenes in COLMAP layout (images_4 + sparse/0) so that 3DGS can be
# trained *here*, on the published protocol (1/4 resolution, every 8th view held out).
#
# Why: the official 30k checkpoints (models.zip, 14.7 GB) reach this node at 25 KB/s and the
# HuggingFace mirror that does serve INRIA-format PLYs carries only bicycle, bonsai and stump of
# the nine tabulated scenes.  Training the baseline ourselves is the only route to a like-for-like
# comparison, and it is what the published papers do as well: they train 3DGS, then compress it.
#
# Source: hf-mirror.com/datasets/alexmkwizu/gaussian_training_datasets (COLMAP layout: images,
# images_2, images_4, images_8 and sparse/0 for the seven scenes that also have checkpoints).
set -euo pipefail
ROOT="${ROOT:-/workspace/data/mip360_colmap}"
SCENES="${SCENES:-bicycle,garden,stump,room,counter,kitchen,bonsai}"
JOBS="${JOBS:-7}"
REPO="https://hf-mirror.com/datasets/alexmkwizu/gaussian_training_datasets/resolve/main/mipnerf360"
API="https://hf-mirror.com/api/datasets/alexmkwizu/gaussian_training_datasets/tree/main/mipnerf360"

log() { echo "[$(date +%H:%M:%S)] $*"; }

fetch_one() {
  local scene="$1"
  local d="$ROOT/$scene"
  if [ -f "$d/sparse/0/images.bin" ] && [ -f "$d/.done" ]; then
    log "$scene: cached ($(ls "$d/images_4" | wc -l) images)"
    return 0
  fi
  mkdir -p "$d/sparse/0" "$d/images_4"
  #: the three sparse files are checked against the repository's own size before they are kept: on
  #: 2026-11-16 the mirror handed back an images.bin of 19.9 MB where the repository says 68.4 MB, and
  #: the truncated file parsed as a valid header followed by a struct.error 200 records in.  A size check
  #: is the difference between a broken download and a broken model.
  curl -sSL --retry 5 "$API/$scene/sparse/0?recursive=true" -o "$d/sparse_sizes.json"
  python3 - "$d" "$REPO" "$scene" <<'PY'
import json, os, subprocess, sys, time
d, repo, scene = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    items = json.load(open(os.path.join(d, "sparse_sizes.json"), encoding="utf-8"))
    want = {it["path"].split("/")[-1]: it.get("size", 0) for it in items if it.get("type") == "file"}
except Exception as exc:                                  # noqa: BLE001 - fall back to no check
    print(f"{scene}: sparse sizes unavailable ({exc}); downloading blind")
    want = {}
for f in ("cameras.bin", "images.bin", "points3D.bin"):
    dst = os.path.join(d, "sparse", "0", f)
    size = want.get(f, 0)
    for attempt in range(4):
        have = os.path.getsize(dst) if os.path.exists(dst) else -1
        if size and have == size:
            break
        if not size and have > 0:
            break
        subprocess.run(["curl", "-sSL", "--retry", "5", "--retry-delay", "3",
                        f"{repo}/{scene}/sparse/0/{f}", "-o", dst + ".part"], check=False)
        os.replace(dst + ".part", dst)
        have = os.path.getsize(dst)
        if size and have != size:
            print(f"{scene}/{f}: {have} != {size}, retrying")
            time.sleep(2)
    print(f"{scene}/{f}: {os.path.getsize(dst)} B" + (f" (want {size})" if size else ""))
PY
  # images_4 is the published protocol resolution; the file list comes from the repository tree so
  # a mirror that stopped early cannot silently truncate the scene, and sizes are checked per file.
  curl -sSL --retry 5 "$API/$scene/images_4?recursive=true" -o "$d/list.json"
  python3 - "$d" "$REPO" "$scene" <<'PY'
import json, os, subprocess, sys
d, repo, scene = sys.argv[1], sys.argv[2], sys.argv[3]
items = json.load(open(os.path.join(d, "list.json"), encoding="utf-8"))
files = [(it["path"].split("/")[-1], it.get("size", 0)) for it in items if it.get("type") == "file"]
todo = [(n, s) for n, s in files
        if not (os.path.isfile(os.path.join(d, "images_4", n))
                and os.path.getsize(os.path.join(d, "images_4", n)) == s)]
print(f"{scene}: {len(files)} images, {len(todo)} to fetch, {sum(s for _, s in todo)/1e6:.0f} MB",
      flush=True)
for n, _s in todo:
    dst = os.path.join(d, "images_4", n)
    subprocess.run(["curl", "-sSL", "--retry", "5", "--retry-delay", "2",
                    f"{repo}/{scene}/images_4/{n}", "-o", dst + ".part"], check=True)
    os.replace(dst + ".part", dst)
PY
  rm -f "$d/list.json"
  touch "$d/.done"
  log "$scene: done ($(ls "$d/images_4" | wc -l) images, $(du -sh "$d" | cut -f1))"
}

export -f fetch_one log
export ROOT REPO API

mkdir -p "$ROOT"
log "=== $SCENES ($JOBS parallel) ==="
echo "$SCENES" | tr ',' '\n' | xargs -P "$JOBS" -I{} bash -c 'fetch_one "$@"' _ {}
log "=== all scenes under $ROOT ==="
du -sh "$ROOT"
for s in ${SCENES//,/ }; do printf '%-9s %5s images %s\n' "$s" "$(ls "$ROOT/$s/images_4" 2>/dev/null | wc -l)" "$(du -sh "$ROOT/$s" 2>/dev/null | cut -f1)"; done
