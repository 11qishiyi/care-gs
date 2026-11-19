#!/usr/bin/env bash
# A4 round --- rate--distortion of the coverage certificate at matched bytes.
#
#   bash experiments/run_a4.sh setup    # deps + 9.59 GB archive + layout check (idempotent)
#   bash experiments/run_a4.sh smoke    # 1 scene, 4 views, 7 variants: catches API breakage in ~3 min
#   bash experiments/run_a4.sh dump     # 4 scenes x 32 variants (the only GPU stage)
#   bash experiments/run_a4.sh analyse  # CPU: 400 splits, matched-byte table, preregistered verdicts
#   bash experiments/run_a4.sh all      # setup -> smoke -> dump -> analyse
#
# Spec and preregistered criteria: experiments/METHOD_PLAN.md, section "A4 规格".
#   C1  at matched bytes, the best non-prune family beats the Fisher-prune family
#   C2  inside the allocator's action space, tail weights beat visibility weights
# Neither is allowed to be re-tuned after the numbers exist.
set -eu
# pipefail is not portable to dash, and some MatPool wrappers run scripts under
# /bin/sh, so set it only when the shell supports it.
if (set -o pipefail) 2>/dev/null; then set -o pipefail; fi

ROOT=${ROOT:-$(cd "$(dirname "$0")/.." && pwd)}
DATA=${DATA:-/workspace/data}
ARCH=${ARCH:-$DATA/out3dgs}
OUT=${OUT:-/workspace/res/a4}
PY=${PY:-python3}
STAGE=${1:-all}
mkdir -p "$OUT"
# `calib` lives at research/code, so the root has to be importable; the scripts
# themselves add it too, but the node's PYTHONPATH keeps stray imports happy.
export PYTHONPATH="$ROOT/research/code:$ROOT${PYTHONPATH:+:$PYTHONPATH}"

SCENES=${SCENES:-bicycle,flowers,stump,treehill}
SMOKE_VARIANTS="clean,q8,q4,p50,p70_q6,am3.0,at3.0"

ARCHIVE_URL="https://www.modelscope.cn/api/v1/datasets/Jackie137/3dgs-Output/repo?Revision=master&FilePath=output-3dgs.tar.gz"
ARCHIVE_BYTES=9587304864

say() { printf '\n=== %s ===\n' "$*"; }

case "$STAGE" in
  setup)
    # Idempotent. Re-running costs nothing once the archive and the deps are in place.
    say "deps"
    $PY -m pip install --quiet plyfile pillow packaging
    if ! $PY -c "import gsplat, torch" 2>/dev/null; then
      # calib.gsrender needs gsplat's unpacked rasterization/projection API. The
      # version vendored under research/code/gsplat (1.6.0) is not on PyPI, so pin
      # the newest released 1.x; `a4_envcheck.py --probe-gpu` proves the API shape.
      $PY -m pip install --quiet "gsplat>=1.5,<2"
    fi
    $PY - <<'PY'
import torch, gsplat
print("torch", torch.__version__, "cuda", torch.version.cuda,
      "available", torch.cuda.is_available(), "gsplat", gsplat.__version__)
assert torch.cuda.is_available(), "no CUDA device"
PY

    say "archive (9.59 GB, skipped when already complete)"
    mkdir -p "$DATA"
    if [ ! -s "$DATA/output-3dgs.tar.gz" ] || \
       [ "$(stat -c%s "$DATA/output-3dgs.tar.gz")" != "$ARCHIVE_BYTES" ]; then
      curl -L --retry 3 -C - -o "$DATA/output-3dgs.tar.gz" "$ARCHIVE_URL"
    fi
    echo "archive bytes $(stat -c%s "$DATA/output-3dgs.tar.gz") (want $ARCHIVE_BYTES)"

    say "extract -> $ARCH/output/<scene>"
    if [ ! -d "$ARCH/output" ]; then
      mkdir -p "$ARCH"
      tar -xzf "$DATA/output-3dgs.tar.gz" -C "$ARCH"
      # some builds of the tarball carry an extra output-3dgs/ shell
      if [ -d "$ARCH/output-3dgs/output" ]; then
        mv "$ARCH/output-3dgs/output" "$ARCH/output" && rmdir "$ARCH/output-3dgs"
      fi
    fi

    say "layout contract (cameras.json + ply + gt count == i%8==0 count)"
    $PY - "$ARCH" "$SCENES" <<'PY'
import json, os, sys
arch, scenes = sys.argv[1], sys.argv[2].split(",")
bad = 0
for sc in scenes:
    base = os.path.join(arch, "output", sc)
    camsp = os.path.join(base, "cameras.json")
    ply = os.path.join(base, "point_cloud", "iteration_40000", "point_cloud.ply")
    gtd = os.path.join(base, "test", "ours_40000", "gt")
    if not (os.path.isfile(camsp) and os.path.isfile(ply)):
        print(f"{sc:9s} MISSING cameras.json / point_cloud.ply"); bad += 1; continue
    cams = json.load(open(camsp)); cams.sort(key=lambda c: c["img_name"])
    n_test = len([i for i in range(len(cams)) if i % 8 == 0])
    gt = sorted(os.listdir(gtd)) if os.path.isdir(gtd) else []
    flag = "OK" if len(gt) == n_test else f"** gt={len(gt)} != test={n_test} **"
    bad += flag != "OK"
    print(f"{sc:9s} cams={len(cams):4d} test={n_test:3d} gt={len(gt):3d} "
          f"ply={os.path.getsize(ply)/2**30:.2f}GiB {flag}")
sys.exit(1 if bad else 0)
PY
    ;;
  smoke)
    say "smoke: bicycle / 4 views / all four families, no dumps kept"
    $PY "$ROOT/experiments/rate_distortion.py" --archive "$ARCH" \
        --out "$OUT/smoke" --scenes bicycle --max-views 4 \
        --variants "$SMOKE_VARIANTS" --device cuda --no-compress
    say "CPU reader on the smoke dump (must not crash)"
    $PY "$ROOT/experiments/rd_analyse.py" --npz "$OUT/smoke" \
        --out "$OUT/smoke/rd.json" --rates 2.5,3.0 --n-splits 40
    ;;
  dump)
    say "A4: 4 scene-checkpoints x 32 variants (prune / quant / joint / allocator)"
    $PY "$ROOT/experiments/rate_distortion.py" --archive "$ARCH" \
        --out "$OUT/dump" --scenes "$SCENES" --device cuda \
        --factor 4 --gt-convention archive --downsample 1 --budget-mb 900
    ;;
  analyse)
    say "matched-byte rate--distortion + preregistered verdicts (CPU)"
    $PY "$ROOT/experiments/rd_analyse.py" --npz "$OUT/dump" \
        --out "$OUT/rd.json" --rates 2.0,2.5,3.0,3.5,4.0 --n-splits 400
    ;;
  all)
    bash "$0" setup && bash "$0" smoke && bash "$0" dump && bash "$0" analyse
    ;;
  *)
    echo "unknown stage: $STAGE (setup|smoke|dump|analyse|all)"; exit 2 ;;
esac
echo "A4_STAGE_DONE $STAGE $(date -Is)"
# Back to the workstation: $OUT/dump/*.npz (the analysis' only input, ~40 MB/scene),
# $OUT/dump/rd_manifest.json (byte accounting per variant), $OUT/rd.json (verdicts).
