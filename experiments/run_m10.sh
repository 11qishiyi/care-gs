#!/usr/bin/env bash
# M10: does a two-stage (residual) dictionary clear the 12x near-lossless gate?
#
#   bash experiments/run_m10.sh setup     # deps + 9.5 GB archive -> /workspace/data/out3dgs
#   bash experiments/run_m10.sh dump      # 8 assets x 16 variants (two-stage + anchors)
#   bash experiments/run_m10.sh bytes     # measured bytes (morton + zstd -12), per asset
#   bash experiments/run_m10.sh analyse   # L1/L2/L3 on the measured axis
#   bash experiments/run_m10.sh all
#
# FIDELITY=0 by default: L1/L2/L3 need coverage and PSNR (both from the render), not
# SSIM/LPIPS, and the LPIPS backbone download is what stalled the M7 node.
set -euo pipefail

ROOT="${ROOT:-/workspace/code}"
DATA="${DATA:-/workspace/data}"
ARCH="${ARCH:-$DATA/out3dgs}"
OUT="${OUT:-/workspace/res/m10}"
PY="${PY:-python3}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
SCENES="${SCENES:-bicycle,flowers,stump,treehill,bicycle_i7k,flowers_i7k,stump_i7k,treehill_i7k}"
VARIANT_SET="${VARIANT_SET:-m10}"
FIDELITY="${FIDELITY:-0}"
LEVEL="${LEVEL:-12}"
JOBS="${JOBS:-3}"
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
      ln -s "$DATA" "$DATA/out3dgs"
      log "archive root is output/ -> linked $DATA/out3dgs -> $DATA"
    fi
  fi
  log "=== the i7k twins are not in the archive ==="
  "$PY" experiments/prep_aliases.py --archive "$ARCH" || true
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
  log "=== measured bytes, $JOBS assets in parallel ==="
  cd "$ROOT"
  local specs
  specs="$("$PY" -c 'import qfp_rd as Q; print(Q.M10_VARIANTS)')"
  mkdir -p "$OUT/bytes"
  local running=0
  for sc in ${SCENES//,/ }; do
    "$PY" -u experiments/m4_bytes.py \
      --archive "$ARCH" --scenes "$sc" --skip-flat --level "$LEVEL" \
      --specs "$specs" --out "$OUT/bytes/bytes_$sc.json" > "$OUT/bytes/$sc.log" 2>&1 &
    running=$((running + 1))
    if [ "$running" -ge "$JOBS" ]; then wait -n; running=$((running - 1)); fi
  done
  wait
  "$PY" - "$OUT" <<'PY'
import glob, json, os, sys
out = sys.argv[1]
merged = {"scenes": [], "backend": None}
for f in sorted(glob.glob(os.path.join(out, "bytes", "bytes_*.json"))):
    with open(f, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    merged["scenes"].extend(d.get("scenes", []))
    merged["backend"] = d.get("backend") or merged["backend"]
dst = os.path.join(out, "m10_bytes.json")
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(merged, fh, indent=1)
print("WROTE", dst, len(merged["scenes"]), "assets")
PY
}

stage_analyse() {
  log "=== analysis on the measured axis ==="
  cd "$ROOT"
  "$PY" -u experiments/m1_analyse.py \
    --dump "$OUT/dump" --out "$OUT/m10_rd.json" \
    --bytes-json "$OUT/m10_bytes.json" \
    --rates 1,2,3,5,7,9,12,16,24,32 --n-splits 400 --protocol m3 --rate-need 3
  "$PY" -u experiments/m10_report.py --json "$OUT/m10_rd.json" --out "$OUT/m10_report.md"
  log "=== WROTE $OUT/m10_rd.json and $OUT/m10_report.md ==="
}

case "${1:-all}" in
  setup)   stage_setup ;;
  dump)    stage_dump ;;
  bytes)   stage_bytes ;;
  analyse) stage_analyse ;;
  all)     stage_setup; stage_dump; stage_bytes; stage_analyse ;;
  *) echo "unknown stage: $1" >&2; exit 2 ;;
esac
