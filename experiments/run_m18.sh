#!/usr/bin/env bash
# M18: does patience buy the fidelity term?  Same pruning and same codec as M17, 30 000 finetune
# steps instead of 8 000, at the two keep fractions that sit inside HAC's and PCGS's bicycle
# budgets (0.35 -> ~25.6 MB, 0.25 -> ~18.2 MB at the measured 11.90 B/primitive).
#
#   bash experiments/run_m18.sh deps data base
#   bash experiments/run_m18.sh k35 k25      # 30 k steps each, launched in parallel
#   bash experiments/run_m18.sh compress     # bytes + dumps (with `clean`) for the new entries
#   bash experiments/run_m18.sh report       # rd json + C6/C7 report
set -euo pipefail
ROOT=/workspace/code
DATA=/workspace/data
ARCH=$DATA/m360std
COLMAP=$DATA/mip360_colmap
MODELS=$DATA/models
OUT=/workspace/res/m18
SCENE=bicycle
STEPS=30000
LEVEL=12
SPECS="vq12_c8_o8,c8_o8_sh3,c10_o8_sh3,m16_o8_sh2,msc12-6-a1_c8_o8"
VARS="clean,vq12_c8_o8,c8_o8_sh3,c10_o8_sh3,m16_o8_sh2,msc12-6-a1_c8_o8"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT"

log() { echo "[$(date +%H:%M:%S)] $*"; }

_mk() { python3 "$ROOT/experiments/make_m360_archive.py" --scene-dir "$COLMAP/$SCENE" \
          --ply "$2" --archive "$ARCH" --name "$1" 2>&1 | tail -1; }
_probe() { bash "$ROOT/experiments/probe_render.sh" "$1" 1 2>&1 | tail -2; }

#: One configuration: prune -> 30 k finetune -> archive -> clean PSNR.  The tag carries the keep
#: fraction and the step count so a row can never be mistaken for an M17 row at 8 k steps.
_one() { # _one <tag> <keep>
  local tag="$1" keep="$2" out="$OUT/$1"
  mkdir -p "$out"; cd "$ROOT"
  log "--- $tag: prune keep=$keep ---"
  python3 experiments/prune_ply.py \
    --in "$MODELS/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply" \
    --out "$out/pruned.ply" --keep-frac "$keep" --score volume 2>&1 | tail -2
  _mk "${SCENE}_${tag}_pre" "$out/pruned.ply"
  _probe "${SCENE}_${tag}_pre"
  log "--- $tag: finetune $STEPS steps ---"
  PYTHONPATH="$ROOT/research/code" python3 research/code/scripts/train_gs.py \
    --data "$COLMAP/$SCENE" --out "$out/ft" --factor 4 --steps "$STEPS" --sh_degree 3 \
    --split interleaved --gt-convention archive --keep_all_views \
    --init_ply "$out/pruned.ply" --no_densify --no_scene_scale --lr_scale 0.3 \
    --grad_clip 1.0 --eval_every 5000 > "$out/ft.log" 2>&1
  grep -e final -e WROTE "$out/ft.log" | tail -2
  _mk "${SCENE}_${tag}_ft" "$out/ft/point_cloud.ply"
  _probe "${SCENE}_${tag}_ft"
  log "--- $tag done ---"
}

stage_compress() {
  cd "$ROOT"
  for sc in bicycle_k35s30_ft bicycle_k25s30_ft; do
    if [ ! -s "$OUT/bytes/bytes_$sc.json" ]; then
      log "bytes $sc"
      mkdir -p "$OUT/bytes"
      python3 -u experiments/m4_bytes.py --archive "$ARCH" --scenes "$sc" --level "$LEVEL" \
        --specs "$SPECS" --out "$OUT/bytes/bytes_$sc.json" > "$OUT/bytes/$sc.log" 2>&1 || \
        log "BYTES FAILED $sc"
    fi
    log "dump $sc"
    python3 -u experiments/qfp_rd.py --archive "$ARCH" --out "$OUT/dump" --scenes "$sc" \
      --variants "$VARS" --factor 1 --cal-frac 0.5 --alpha 0.1 --n-fisher-views 4 \
      --gt-convention archive --downsample 1 --budget-mb 900 --device cuda \
      --fidelity --lpips-net vgg > "$OUT/dump_$sc.log" 2>&1 || log "DUMP FAILED $sc"
  done
  python3 - "$OUT" <<'PY'
import glob, json, os, sys
out = sys.argv[1]
merged = {"scenes": [], "backend": None}
for f in sorted(glob.glob(os.path.join(out, "bytes", "bytes_*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    merged["scenes"].extend(d.get("scenes", []))
    merged["backend"] = d.get("backend") or merged["backend"]
dst = os.path.join(out, "m18_bytes.json")
json.dump(merged, open(dst, "w", encoding="utf-8"), indent=1)
print("WROTE", dst, len(merged["scenes"]), "assets")
PY
}

stage_report() {
  cd "$ROOT"
  python3 -u experiments/m1_analyse.py --dump "$OUT/dump" --out "$OUT/m18_rd.json" \
    --bytes-json "$OUT/m18_bytes.json" \
    --rates 1,2,3,5,7,9,12,16,24,40,60 --n-splits 400 --protocol m3 --rate-need 3
  python3 -u experiments/m17_report.py --rd "$OUT/m18_rd.json" --bytes "$OUT/m18_bytes.json" \
    --base-psnr 24.52 --title M18_pilot_30k_steps --out "$OUT/m18_report.md" --json "$OUT/m18_report.json"
  log "=== WROTE $OUT/m18_rd.json $OUT/m18_report.md ==="
}

case "${1:-all}" in
  deps) bash "$ROOT/experiments/run_m17.sh" deps ;;
  data) bash "$ROOT/experiments/run_m17.sh" data ;;
  base) bash "$ROOT/experiments/run_m17.sh" base ;;
  k35)  _one k35s30 0.35 ;;
  k25)  _one k25s30 0.25 ;;
  compress) stage_compress ;;
  report)   stage_report ;;
  *) echo "use deps|data|base|k35|k25|compress|report" >&2; exit 2 ;;
esac
