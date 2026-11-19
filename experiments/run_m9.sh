#!/usr/bin/env bash
# M9: is a per-asset dictionary a better use of the same bytes than per-coefficient SH?
#
#   bash experiments/run_m9.sh setup     # deps + 9.5 GB archive -> /workspace/data/out3dgs
#   bash experiments/run_m9.sh dump      # 8 assets x 18 variants (dictionary + scalar)
#   bash experiments/run_m9.sh bytes     # measured bytes (morton + zstd, shipped format)
#   bash experiments/run_m9.sh analyse   # E1/K1/K2/K3 on the measured axis
#   bash experiments/run_m9.sh all
#
# FIDELITY=0 by default: K1/K2/K3 need PSNR (which always comes from the render), not
# SSIM/LPIPS, and the LPIPS backbone download is what stalled the M7 node.
set -euo pipefail

ROOT="${ROOT:-/workspace/code}"
DATA="${DATA:-/workspace/data}"
ARCH="${ARCH:-$DATA/out3dgs}"
OUT="${OUT:-/workspace/res/m9}"
PY="${PY:-python3}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
SCENES="${SCENES:-bicycle,flowers,stump,treehill,bicycle_i7k,flowers_i7k,stump_i7k,treehill_i7k}"
VARIANT_SET="${VARIANT_SET:-m9}"
FIDELITY="${FIDELITY:-0}"
LEVEL="${LEVEL:-12}"
ARCHIVE_URL="${ARCHIVE_URL:-https://www.modelscope.cn/api/v1/datasets/Jackie137/3dgs-Output/repo?Revision=master&FilePath=output-3dgs.tar.gz}"
ARCHIVE_BYTES="${ARCHIVE_BYTES:-9587304864}"

log() { echo "[$(date +%H:%M:%S)] $*"; }

stage_setup() {
  log "=== setup: deps ==="
  "$PY" -m pip install --quiet plyfile pillow packaging "gsplat>=1.5,<2" zstandard
  "$PY" - <<'PY'
import torch, gsplat
print("torch", torch.__version__, "cuda", torch.version.cuda,
      "available", torch.cuda.is_available(), "gsplat", getattr(gsplat, "__version__", "?"))
assert torch.cuda.is_available(), "no CUDA"
PY
  if [ ! -d "$ARCH/output/bicycle" ]; then
    mkdir -p "$DATA"
    log "=== downloading $ARCHIVE_BYTES B archive ==="
    curl -L --retry 3 -C - -o "$DATA/output-3dgs.tar.gz" "$ARCHIVE_URL"
    log "archive bytes $(stat -c %s "$DATA/output-3dgs.tar.gz") (want $ARCHIVE_BYTES)"
    log "=== unpacking ==="
    tar -xzf "$DATA/output-3dgs.tar.gz" -C "$DATA"
    if [ -d "$DATA/output-3dgs" ] && [ ! -d "$DATA/out3dgs" ]; then
      mv "$DATA/output-3dgs" "$ARCH"
    elif [ -d "$DATA/output" ] && [ ! -e "$DATA/out3dgs" ]; then
      # this archive's top level is a bare ``output/`` (the A4/M7 nodes were built the
      # same way); the contract below is ``$ARCH/output/<scene>``, so point ARCH at DATA
      ln -s "$DATA" "$DATA/out3dgs"
      log "archive root is output/ -> linked $DATA/out3dgs -> $DATA"
    fi
  fi
  log "=== verifying the data contract ==="
  "$PY" - "$ARCH" $SCENES <<'PY'
import json, os, sys
arch, scenes = sys.argv[1], [s for s in sys.argv[2].split(",") if s]
for sc in scenes:
    d = os.path.join(arch, "output", sc)
    cams = json.load(open(os.path.join(d, "cameras.json")))
    gt = os.listdir(os.path.join(d, "test", "ours_40000", "gt"))
    ply = os.path.join(d, "point_cloud", "iteration_40000", "point_cloud.ply")
    print(f"{sc:12s} cams={len(cams):4d} gt={len(gt):3d} ply={os.path.getsize(ply)/2**30:.2f}GiB OK")
PY
}

stage_dump() {
  log "=== dump: $VARIANT_SET grid on $SCENES ==="
  cd "$ROOT"
  if [ "$FIDELITY" = "1" ]; then FID="--fidelity --lpips-net alex"; else FID=""; fi
  # One process per asset: a silent gsplat crash in one scene must not erase the rest,
  # and the manifest merges rows across runs.
  for sc in ${SCENES//,/ }; do
    log "--- $sc ---"
    "$PY" -u experiments/qfp_rd.py \
      --archive "$ARCH" --out "$OUT/dump" --scenes "$sc" \
      --variant-set "$VARIANT_SET" \
      --factor 4 --cal-frac 0.5 --alpha 0.1 --n-fisher-views 4 \
      --gt-convention archive --downsample 1 --budget-mb 900 --device cuda $FID
  done
  log "=== dump done: $(ls -1 "$OUT/dump"/*.npz 2>/dev/null | wc -l) npz ==="
}

stage_bytes() {
  log "=== measured bytes (shipped format: morton + zstd -$LEVEL) ==="
  cd "$ROOT"
  "$PY" -u experiments/m4_bytes.py \
    --archive "$ARCH" --scenes "$SCENES" --skip-flat --level "$LEVEL" \
    --specs "$("$PY" -c 'import qfp_rd as Q; print(Q.M9_VARIANTS)')" \
    --out "$OUT/m9_bytes.json"
}

stage_analyse() {
  log "=== analysis on the measured axis ==="
  cd "$ROOT"
  "$PY" -u experiments/m1_analyse.py \
    --dump "$OUT/dump" --out "$OUT/m9_rd.json" \
    --bytes-json "$OUT/m9_bytes.json" \
    --rates 2,3,5,7,9,12,16,24 --n-splits 400 --protocol m3 --rate-need 3
  "$PY" -u experiments/m9_report.py --json "$OUT/m9_rd.json" --out "$OUT/m9_report.md"
  log "=== WROTE $OUT/m9_rd.json and $OUT/m9_report.md ==="
}

case "${1:-all}" in
  setup)   stage_setup ;;
  dump)    stage_dump ;;
  bytes)   stage_bytes ;;
  analyse) stage_analyse ;;
  all)     stage_setup; stage_dump; stage_bytes; stage_analyse ;;
  *) echo "unknown stage: $1" >&2; exit 2 ;;
esac
