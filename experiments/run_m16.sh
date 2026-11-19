#!/usr/bin/env bash
# M16: our curve on the published axes.  Protocol alignment (3DGS-30k trained here on the
# published recipe, images_4, 7 MipNeRF360 scenes, PSNR/SSIM/LPIPS-VGG) plus the spanning
# lattice from 2x to prune-plus-dictionary sizes, judged by C1 (protocol) and C2 (equal size).
#
#   bash experiments/run_m16.sh deps      # pip + LPIPS-VGG weights
#   bash experiments/run_m16.sh colmap    # images_4 + sparse/0 for the panel
#   bash experiments/run_m16.sh train     # 30k iterations per scene, official hyper-parameters
#   bash experiments/run_m16.sh archive    # archive contract from COLMAP + trained PLY
#   bash experiments/run_m16.sh calib      # clean render, C1 preview against published 3DGS
#   bash experiments/run_m16.sh dump       # M16 grid with SSIM/LPIPS
#   bash experiments/run_m16.sh bytes      # measured bytes (morton + zstd -12)
#   bash experiments/run_m16.sh analyse    # rd json + m16_compare (C1/C2)
#   bash experiments/run_m16.sh timing     # encode time + peak RSS per scene
#   bash experiments/run_m16.sh all
#
# Why we train the baseline instead of downloading it: the INRIA release (models.zip, 14.66 GB)
# reached this node at 25 KB/s, and the HuggingFace mirror that does serve INRIA-format PLYs
# carries only bicycle, bonsai and stump of the nine tabulated scenes.  Training 3DGS ourselves
# is what the compression papers do too -- they train, then compress -- and it is the only way
# to have a like-for-like base model on a panel wide enough to report a mean.
set -euo pipefail

ROOT="${ROOT:-/workspace/code}"
DATA="${DATA:-/workspace/data}"
ARCH="${ARCH:-$DATA/m360std}"                     # archive contract: output/<scene>/...
COLMAP="${COLMAP:-$DATA/mip360_colmap}"           # COLMAP scenes at images_4
SELFTRAIN="${SELFTRAIN:-$DATA/m360_selftrain}"    # trained PLYs
OUT="${OUT:-/workspace/res/m16}"
PY="${PY:-python3}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
#: Seven of the nine MipNeRF360 scenes the papers tabulate.  flowers and treehill are absent from
#: the COLMAP mirrors we can reach, so the round reports a seven-scene panel and says so instead
#: of interpolating; every scene is compared against its own published row.
SCENES="${SCENES:-bicycle,garden,stump,room,counter,kitchen,bonsai}"
VARIANT_SET="${VARIANT_SET:-m16}"
LEVEL="${LEVEL:-12}"
JOBS="${JOBS:-3}"
TRAIN_JOBS="${TRAIN_JOBS:-2}"
FACTOR="${FACTOR:-4}"
STEPS="${STEPS:-30000}"
#: The specs the comparison needs.  ``clean`` is deliberately absent: it *is* the PLY, so its
#: size is n*236 B by definition (cmp_points synthesises that row) and pricing it would cost a
#: 1.5 GB zstd-12 pass per asset for a number every table already reports.
SPECS="${SPECS:-sh16_g16,sh8_g16,m16_o8_sh4,msc12-6-a1_c8_o8,m16_o8_sh2,c10_o8_sh3,c8_o8_sh3,c8_o8_sh2,vq12_c8_o8,rvq10-4_c8_o8,p50_vq12_c8_o8,p30_vq12_c8_o8,p10_vq12_c8_o8}"

log() { echo "[$(date +%H:%M:%S)] $*"; }

stage_deps() {
  log "=== deps ==="
  "$PY" -m pip install --quiet plyfile pillow packaging zstandard scikit-image
  "$PY" -c 'import gsplat' 2>/dev/null || "$PY" -m pip install --quiet --no-deps "gsplat>=1.5,<2"
  "$PY" -m pip install --quiet rich jaxtyping ninja lpips
  "$PY" - <<'PY'
import torch, gsplat
print("torch", torch.__version__, "cuda", torch.version.cuda,
      "available", torch.cuda.is_available(), "gsplat", getattr(gsplat, "__version__", "?"))
assert torch.cuda.is_available(), "no CUDA"
PY
  # LPIPS-VGG weights: every paper reports vgg, so the download happens once here rather than
  # inside a render loop that a 600 s no-output timeout can kill.
  "$PY" - <<'PY'
import lpips
lpips.LPIPS(net="vgg", verbose=False)
print("lpips vgg ok")
PY
}

stage_colmap() {
  cd "$ROOT"
  SCENES="$SCENES" ROOT="$COLMAP" bash experiments/fetch_m360_colmap.sh
}

stage_train() {
  cd "$ROOT"
  COLMAP="$COLMAP" OUT="$SELFTRAIN" SCENES="$SCENES" STEPS="$STEPS" JOBS="$TRAIN_JOBS" \
    CODE="$ROOT" bash experiments/train_official.sh
}

stage_archive() {
  log "=== archive contract from COLMAP + trained PLY ==="
  cd "$ROOT"
  for sc in ${SCENES//,/ }; do
    ply="$SELFTRAIN/$sc/point_cloud.ply"
    if [ ! -f "$ply" ]; then log "  $sc: no PLY, skipped"; continue; fi
    "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$sc" --ply "$ply" \
      --archive "$ARCH" --name "$sc" --factor "$FACTOR" --holdout 8
  done
  log "=== archive ready: $(ls "$ARCH/output" | tr '\n' ' ') ==="
}

_dump_one() {
  local sc="$1" out="$2"
  "$PY" -u experiments/qfp_rd.py \
    --archive "$ARCH" --out "$out/dump" --scenes "$sc" \
    --variant-set "$VARIANT_SET" \
    --factor "$FACTOR" --cal-frac 0.5 --alpha 0.1 --n-fisher-views 4 \
    --gt-convention archive --downsample 1 --budget-mb 900 --device cuda \
    --fidelity --lpips-net vgg
}

stage_calib() {
  log "=== calib: clean + one compressed row, factor $FACTOR ==="
  cd "$ROOT"
  local cal="${CAL_SCENES:-bicycle,garden,stump}"
  for sc in ${cal//,/ }; do
    "$PY" -u experiments/qfp_rd.py \
      --archive "$ARCH" --out "$OUT/calib_dump" --scenes "$sc" \
      --variants "clean,c10_o8_sh3" --factor "$FACTOR" --cal-frac 0.5 --alpha 0.1 \
      --n-fisher-views 4 --gt-convention archive --downsample 1 \
      --budget-mb 900 --device cuda --fidelity --lpips-net vgg
  done
  # The dump summary carries per-variant PSNR/SSIM/LPIPS, which is all C1 reads: the rate axis is
  # irrelevant for a protocol check and the byte pass would cost a gigabyte-scale zstd run.
  "$PY" - "$OUT/calib_dump/dump" "$ROOT/experiments/published_3dgs.json" <<'PY'
import json, os, sys
dump, pubfile = sys.argv[1], sys.argv[2]
pub = json.load(open(pubfile, encoding="utf-8"))["methods"]["3dgs"]
summ = os.path.join(dump, "dump_summary.json")
rows = json.load(open(summ, encoding="utf-8"))
if isinstance(rows, dict):
    rows = rows.get("scenes", [])
print("| scene | ours | published | delta dB | SSIM ours/ref | LPIPS ours/ref |")
bad = 0
for r in rows:
    sc = r["scene"]
    v = (r.get("variants") or {}).get("clean")
    if not v or sc not in pub:
        continue
    d = v["psnr"] - pub[sc]["psnr"]
    bad += 0 if abs(d) <= 0.35 else 1
    print(f"| {sc} | {v['psnr']:.2f} | {pub[sc]['psnr']:.2f} | {d:+.2f} | "
          f"{(v.get('ssim') or 0):.3f}/{pub[sc]['ssim']:.3f} | "
          f"{(v.get('lpips') or 0):.4f}/{pub[sc]['lpips']:.3f} |")
print(f"\nC1 preview on {len(rows)} scene(s): {len(rows) - bad} within 0.35 dB")
PY
  log "=== calib done ==="
}

stage_dump() {
  log "=== dump: $VARIANT_SET grid on ${SCENES} ==="
  cd "$ROOT"
  for sc in ${SCENES//,/ }; do
    log "--- $sc ---"
    _dump_one "$sc" "$OUT"
  done
  log "=== dump done: $(ls -1 "$OUT/dump"/*.npz 2>/dev/null | wc -l) npz ==="
}

stage_bytes() {
  log "=== measured bytes, $JOBS assets in parallel ==="
  cd "$ROOT"
  mkdir -p "$OUT/bytes"
  local running=0
  for sc in ${SCENES//,/ }; do
    "$PY" -u experiments/m4_bytes.py \
      --archive "$ARCH" --scenes "$sc" --level "$LEVEL" \
      --specs "$SPECS" --out "$OUT/bytes/bytes_$sc.json" > "$OUT/bytes/$sc.log" 2>&1 &
    running=$((running + 1))
    if [ "$running" -ge "$JOBS" ]; then wait -n; running=$((running - 1)); fi
  done
  wait
  "$PY" - "$OUT" <<'PY'
import glob, json, os, sys
out = sys.argv[1]
merged = {"scenes": [], "backend": None}
for f in sorted(glob.glob(os.path.join(out, "bytes", "bytes_*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    merged["scenes"].extend(d.get("scenes", []))
    merged["backend"] = d.get("backend") or merged["backend"]
dst = os.path.join(out, "m16_bytes.json")
json.dump(merged, open(dst, "w", encoding="utf-8"), indent=1)
print("WROTE", dst, len(merged["scenes"]), "assets")
PY
}

stage_analyse() {
  log "=== analysis on the measured axis ==="
  cd "$ROOT"
  "$PY" -u experiments/m1_analyse.py \
    --dump "$OUT/dump" --out "$OUT/m16_rd.json" \
    --bytes-json "$OUT/m16_bytes.json" \
    --rates 1,2,3,5,7,9,12,16,24,40,60 --n-splits 400 --protocol m3 --rate-need 3
  "$PY" -u experiments/m16_compare.py --rd "$OUT/m16_rd.json" --bytes "$OUT/m16_bytes.json" \
    --out "$OUT/m16_compare.md" --json "$OUT/m16_compare.json"
  log "=== WROTE $OUT/m16_rd.json $OUT/m16_compare.md ==="
}

stage_timing() {
  log "=== encode time and peak RSS, one scene per spec ==="
  cd "$ROOT"
  "$PY" -u experiments/m16_timing.py --archive "$ARCH" --scenes "$SCENES" \
    --specs "c10_o8_sh3,vq12_c8_o8,p30_vq12_c8_o8" --out "$OUT/m16_timing.json"
}

case "${1:-all}" in
  deps)    stage_deps ;;
  colmap)  stage_colmap ;;
  train)   stage_train ;;
  archive) stage_archive ;;
  calib)   stage_calib ;;
  dump)    stage_dump ;;
  bytes)   stage_bytes ;;
  analyse) stage_analyse ;;
  timing)  stage_timing ;;
  all)     stage_deps; stage_colmap; stage_train; stage_archive; stage_calib; stage_dump; stage_bytes; stage_analyse; stage_timing ;;
  *) echo "unknown stage: $1" >&2; exit 2 ;;
esac
