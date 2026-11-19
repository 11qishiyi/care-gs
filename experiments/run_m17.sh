#!/usr/bin/env bash
# M17: the best number we can report at HAC's operating point (bicycle, <= 27.54 MB).
#
# M16 measured exactly one pruning setting -- keep 20 %, 1500 finetune steps -- and lost 4.97 dB
# to HAC at HAC's own size.  That confounded two things: how good our codec is per byte, and how
# good the pruned model is at that primitive count.  This round holds the codec fixed (the M16
# grid, unchanged) and moves the pruning setting to where a model would actually be shipped,
# with a finetune long enough to be a real comparison (8000 steps, not 1500).
#
# Configurations are fixed by the pre-registration in METHOD_PLAN.md (written 06:50, before any
# data):  K1 keep .50 lr 1.0 | K2 keep .35 lr 1.0 | K3 keep .50 lr 0.3.  All at 8000 steps.
#
#   bash experiments/run_m17.sh deps      # pip + LPIPS-VGG weights
#   bash experiments/run_m17.sh data      # bicycle COLMAP images_4 + mirror 30k PLY
#   bash experiments/run_m17.sh base      # base archive + clean calibration
#   bash experiments/run_m17.sh k1 k2 k3  # prune -> finetune -> archive -> clean PSNR
#   bash experiments/run_m17.sh compress  # dump + measured bytes for every finetuned model
#   bash experiments/run_m17.sh report    # rd json + C5 report
#   bash experiments/run_m17.sh all
set -euo pipefail

ROOT="${ROOT:-/workspace/code}"
DATA="${DATA:-/workspace/data}"
ARCH="${ARCH:-$DATA/m360std}"
COLMAP="${COLMAP:-$DATA/mip360_colmap}"
MODELS="${MODELS:-$DATA/models}"
OUT="${OUT:-/workspace/res/m17}"
PY="${PY:-python3}"
SCENE="${SCENE:-bicycle}"
STEPS="${STEPS:-8000}"
LEVEL="${LEVEL:-12}"
JOBS="${JOBS:-3}"
FACTOR="${FACTOR:-1}"     # archive cameras are already at images_4 resolution
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
#: The five specs the frontier needs.  vq12 is the shared-colour model (12-bit index into a SH
#: codebook), c8/c10 are the near-lossless shelf, m16_o8_sh2 is the cheapest 3-bit row.  No p*
#: rows: every model in this round is already pruned before compression.
SPECS="${SPECS:-vq12_c8_o8,c8_o8_sh3,c10_o8_sh3,m16_o8_sh2,msc12-6-a1_c8_o8}"
VARIANTS="${VARIANTS:-vq12_c8_o8,c8_o8_sh3,c10_o8_sh3,m16_o8_sh2,msc12-6-a1_c8_o8}"

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
  "$PY" - <<'PY'
import lpips
lpips.LPIPS(net="vgg", verbose=False)
print("lpips vgg ok")
PY
}

stage_data() {
  log "=== data: $SCENE COLMAP (images_4 + sparse/0) and mirror 30k PLY ==="
  cd "$ROOT"
  ROOT="$COLMAP" SCENES="$SCENE" JOBS=1 bash experiments/fetch_m360_colmap.sh
  MODELS="$MODELS" IMAGES="$DATA/mip360" bash experiments/fetch_hf_curl.sh "$SCENE" "iteration_30000" 8 \
    | tail -3
  bash experiments/link_images.sh || true
  ls -l "$MODELS/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply"
}

#: One entry of the archive holds one PLY behind one cameras.json, so every model gets its own
#: name.  The name is also the row label in the report: bicycle_k50_ft is "keep 50 %, finetuned".
_mk() { # _mk <name> <ply>
  PYTHONPATH="$PYTHONPATH" "$PY" experiments/make_m360_archive.py \
    --scene-dir "$COLMAP/$SCENE" --ply "$2" --archive "$ARCH" --name "$1" 2>&1 | tail -1
}

_probe() { # _probe <name>
  bash experiments/probe_render.sh "$1" "$FACTOR" 2>&1 | tail -2
}

stage_base() {
  log "=== base archive: $SCENE (mirror 30k) ==="
  cd "$ROOT"
  _mk "$SCENE" "$MODELS/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply"
  _probe "$SCENE"
}

_finetune_one() { # _finetune_one <tag> <keep> <lr_scale>
  local tag="$1" keep="$2" lr="$3"
  local out="$OUT/$tag"
  mkdir -p "$out"
  cd "$ROOT"

  log "--- $tag: prune keep=$keep ---"
  "$PY" experiments/prune_ply.py --in "$MODELS/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply" \
    --out "$out/pruned.ply" --keep-frac "$keep" --score volume 2>&1 | tail -2
  _mk "${SCENE}_${tag}_pre" "$out/pruned.ply"
  _probe "${SCENE}_${tag}_pre"

  log "--- $tag: finetune $STEPS steps, lr_scale=$lr ---"
  PYTHONPATH="$ROOT/research/code" "$PY" research/code/scripts/train_gs.py \
    --data "$COLMAP/$SCENE" --out "$out/ft" --factor 4 --steps "$STEPS" --sh_degree 3 \
    --split interleaved --gt-convention archive --keep_all_views \
    --init_ply "$out/pruned.ply" --no_densify --no_scene_scale --lr_scale "$lr" \
    --grad_clip "${GRAD_CLIP:-1.0}" \
    --eval_every 1000 > "$out/ft.log" 2>&1
  grep -e final -e WROTE "$out/ft.log" | tail -2

  _mk "${SCENE}_${tag}_ft" "$out/ft/point_cloud.ply"
  _probe "${SCENE}_${tag}_ft"
  log "--- $tag done ---"
}

stage_k1() { _finetune_one k50 0.50 1.0; }
stage_k2() { _finetune_one k35 0.35 1.0; }
stage_k3() { _finetune_one k50l3 0.50 0.3; }
#: K1 and K2 (lr_scale 1.0) both diverged to NaN on the first attempt -- the finite guard caught
#: it at step ~3400 with psnr 1.33, and neither wrote a PLY.  That is a failed run, not a result,
#: so the second keep fraction is measured at the lr_scale that stayed stable (0.3), and the
#: report says which configurations were lost to divergence rather than quietly dropping them.
stage_k2b() { _finetune_one k35l3 0.35 0.3; }

stage_compress() {
  log "=== dump + measured bytes for every model in the archive ==="
  cd "$ROOT"
  mkdir -p "$OUT/bytes"
  local entries
  entries=$(ls "$ARCH/output" | grep -E "^${SCENE}" | sort)
  log "entries: $(echo $entries | tr '\n' ' ')"
  mkdir -p "$OUT/dump"
  for sc in $entries; do
    log "--- dump $sc ---"
    "$PY" -u experiments/qfp_rd.py \
      --archive "$ARCH" --out "$OUT/dump" --scenes "$sc" \
      --variants "$VARIANTS" \
      --factor "$FACTOR" --cal-frac 0.5 --alpha 0.1 --n-fisher-views 4 \
      --gt-convention archive --downsample 1 --budget-mb 900 --device cuda \
      --fidelity --lpips-net vgg 2>&1 | tail -3
  done
  local running=0
  for sc in $entries; do
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
dst = os.path.join(out, "m17_bytes.json")
json.dump(merged, open(dst, "w", encoding="utf-8"), indent=1)
print("WROTE", dst, len(merged["scenes"]), "assets")
PY
}

stage_report() {
  log "=== analysis ==="
  cd "$ROOT"
  "$PY" -u experiments/m1_analyse.py \
    --dump "$OUT/dump" --out "$OUT/m17_rd.json" \
    --bytes-json "$OUT/m17_bytes.json" \
    --rates 1,2,3,5,7,9,12,16,24,40,60 --n-splits 400 --protocol m3 --rate-need 3
  "$PY" -u experiments/m17_report.py --rd "$OUT/m17_rd.json" --bytes "$OUT/m17_bytes.json" \
    --out "$OUT/m17_report.md"
  log "=== WROTE $OUT/m17_rd.json $OUT/m17_report.md ==="
}

case "${1:-all}" in
  deps)     stage_deps ;;
  data)     stage_data ;;
  base)     stage_base ;;
  k1)       stage_k1 ;;
  k2)       stage_k2 ;;
  k3)       stage_k3 ;;
  k2b)      stage_k2b ;;
  compress) stage_compress ;;
  report)   stage_report ;;
  all)      stage_deps; stage_data; stage_base; stage_k1; stage_k2; stage_k3; stage_compress; stage_report ;;
  *) echo "unknown stage: $1" >&2; exit 2 ;;
esac
