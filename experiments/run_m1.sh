#!/usr/bin/env bash
# M1 round --- QFP: quantise first, prune second (precision is cheap, primitives are not).
#
#   bash experiments/run_m1.sh setup    # deps + 9.59 GB archive + LPIPS backbone + layout check
#   bash experiments/run_m1.sh smoke    # 1 scene, 4 views, one variant per family (~4 min)
#   bash experiments/run_m1.sh dump     # 4 scenes x 35 variants, with SSIM/LPIPS (GPU)
#   bash experiments/run_m1.sh analyse  # CPU: 400 splits, matched-byte curves, D1/D2/D3
#   bash experiments/run_m1.sh all      # setup -> smoke -> dump -> analyse
#
# Spec and preregistered criteria: experiments/METHOD_PLAN.md, section "M1 规格".
#   D1  at matched bytes the QFP curve sits at least 3.0 pp above the prune curve
#   D2  fidelity (PSNR/SSIM/LPIPS) of QFP is not worse than prune at the same bytes
#   D3  a near-lossless shelf exists (>=2 rates with <=1.0 pp and <=0.3 dB absolute loss)
# Nothing here may be re-tuned after the numbers exist.
set -eu
if (set -o pipefail) 2>/dev/null; then set -o pipefail; fi

ROOT=${ROOT:-$(cd "$(dirname "$0")/.." && pwd)}
DATA=${DATA:-/workspace/data}
ARCH=${ARCH:-$DATA/out3dgs}
OUT=${OUT:-/workspace/res/m1}
# Which variant grid to realise: ``m1`` (the QFP grid) or ``m2`` (the attribute
# ladder).  Both write the same npz/manifest contract, so one analyser reads both.
VARIANT_SET=${VARIANT_SET:-m1}
PY=${PY:-python3}
STAGE=${1:-all}
mkdir -p "$OUT"
export PYTHONPATH="$ROOT/research/code:$ROOT${PYTHONPATH:+:$PYTHONPATH}"

SCENES=${SCENES:-bicycle,flowers,stump,treehill}
# one representative per family: clean / iso / geo-only / sh-only / qfp / prune / joint
SMOKE_VARIANTS="clean,iso_quats8,geo16,sh4_g16,q4_g12,p50,p50_q4_g12"

ARCHIVE_URL="https://www.modelscope.cn/api/v1/datasets/Jackie137/3dgs-Output/repo?Revision=master&FilePath=output-3dgs.tar.gz"
ARCHIVE_BYTES=9587304864

say() { printf '\n=== %s ===\n' "$*"; }

case "$STAGE" in
  setup)
    say "deps"
    $PY -m pip install --quiet plyfile pillow packaging scikit-image lpips zstandard
    if ! $PY -c "import gsplat, torch" 2>/dev/null; then
      # 1.6.0 exists only in research/code/gsplat, not on PyPI: pin the newest released 1.x.
      $PY -m pip install --quiet "gsplat>=1.5,<2"
    fi
    $PY - <<'PY'
import torch, gsplat
print("torch", torch.__version__, "cuda", torch.version.cuda,
      "available", torch.cuda.is_available(), "gsplat", gsplat.__version__)
assert torch.cuda.is_available(), "no CUDA device"
PY

    say "lpips backbone (D2 needs it; --fidelity degrades to None rather than hanging)"
    if [ "${FIDELITY:-1}" = "0" ]; then
      # M7 runs without perceptual metrics: this host pulls the backbone at ~10 kB/s.
      echo "FIDELITY=0 -> skipping the LPIPS backbone"
    else
    $PY - <<'PY'
import os, torch
d = os.path.join(os.environ.get("TORCH_HOME", os.path.expanduser("~/.cache/torch")),
                 "hub", "checkpoints")
os.makedirs(d, exist_ok=True)
for fn, url in (("alexnet-owt-7be5be79.pth",
                 "https://download.pytorch.org/models/alexnet-owt-7be5be79.pth"),):
    p = os.path.join(d, fn)
    if os.path.exists(p) and os.path.getsize(p) > 1_000_000:
        print("cached", fn, os.path.getsize(p)); continue
    sd = torch.hub.load_state_dict_from_url(url, model_dir=d, progress=False)
    print("fetched", fn, "tensors", len(sd))
PY
    fi

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
    say "smoke: bicycle / 4 views / 7 variants spanning every family"
    $PY "$ROOT/experiments/qfp_rd.py" --archive "$ARCH" \
        --out "$OUT/smoke" --scenes bicycle --max-views 4 \
        --variants "$SMOKE_VARIANTS" --device cuda --no-compress
    say "CPU reader on the smoke dump (must not crash, rates need not pass yet)"
    $PY "$ROOT/experiments/m1_analyse.py" --dump "$OUT/smoke" \
        --out "$OUT/smoke/m1_rd.json" --rates 2,3,5 --n-splits 40
    ;;
  dump)
    say "4 scene-checkpoints, variant set $VARIANT_SET, with SSIM/LPIPS"
    # ``FIDELITY=0`` skips SSIM/LPIPS.  M7 sets it: this host pulled the AlexNet
    # backbone at ~10 kB/s (3 MB in 5 min), which would stall the round for hours,
    # and none of the M7 criteria read a perceptual metric.
    _FID_ARGS="--fidelity --lpips-net alex"
    if [ "${FIDELITY:-1}" = "0" ]; then _FID_ARGS=""; fi
    # One process per scene: gsplat can die hard (segfault, no traceback) on a
    # single scene, and that must not cost the other three their results.  The
    # manifest is merged on load, so a rerun only rewrites the scene it names.
    IFS=',' read -ra _SC <<< "$SCENES"
    _fail=0
    for s in "${_SC[@]}"; do
        say "scene $s"
        # shellcheck disable=SC2086
        $PY "$ROOT/experiments/qfp_rd.py" --archive "$ARCH" \
            --out "$OUT/dump" --scenes "$s" --device cuda \
            --variant-set "$VARIANT_SET" \
            --factor 4 --gt-convention archive --downsample 1 --budget-mb 900 \
            $_FID_ARGS || _fail=$((_fail+1))
        if [ -f "$OUT/dump/$s.npz" ]; then
            echo "$s" >> "$OUT/dump/.done_scenes"
        fi
    done
    say "dump finished with $_fail failing scene(s)"
    ;;
  analyse)
    say "matched-byte rate--distortion + preregistered verdicts (CPU)"
    $PY "$ROOT/experiments/m1_analyse.py" --dump "$OUT/dump" \
        --out "$OUT/m1_rd.json" --rates 2,3,5,7,9,12,16,24 --n-splits 400
    ;;
  all)
    bash "$0" setup && bash "$0" smoke && bash "$0" dump && bash "$0" analyse
    ;;
  *)
    echo "unknown stage: $STAGE (setup|smoke|dump|analyse|all)"; exit 2 ;;
esac
echo "M1_STAGE_DONE $STAGE $(date -Is)"
