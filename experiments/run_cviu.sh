#!/usr/bin/env bash
# CVIU round — one GPU pass that produces every artifact the revision adds.
#
#   bash experiments/run_cviu.sh data      # archive + bonsai + 7k twins (delegates to repro/run_all.sh)
#   bash experiments/run_cviu.sh dump      # 10 scene-checkpoints x 8 variants, + SSIM/LPIPS
#   bash experiments/run_cviu.sh audit     # CPU: audit + KS envelope (works on the node or locally)
#   bash experiments/run_cviu.sh all
#
# It mirrors repro/run_all.sh exactly --- same archive, same `--gt-convention archive`,
# same variant list --- and adds two things: `--fidelity` (SSIM/LPIPS per view) and the
# audit analysis. The dump is the only GPU stage.
set -eu
# pipefail is not portable to dash, and some MatPool wrappers run scripts under
# /bin/sh, so set it only when the shell supports it.
if (set -o pipefail) 2>/dev/null; then set -o pipefail; fi

ROOT=${ROOT:-$(cd "$(dirname "$0")/.." && pwd)}
DATA=${DATA:-/workspace/data}
ARCH=$DATA/out3dgs
REC=${REC:-/workspace/res/rev}
OUT=${OUT:-/workspace/res/cviu}
PY=${PY:-python3}
STAGE=${1:-all}
mkdir -p "$REC" "$OUT" /data/runs
# `calib` lives at the repo root while the scripts live in experiments/, so the
# package is only importable when the root is on the path.
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

SCENES="bicycle,flowers,stump,treehill,bicycle_i7k,flowers_i7k,stump_i7k,treehill_i7k,bonsai"
VARIANTS="clean,prune50,prune30,pup30,shdeg1,quant8,quant6,quant4"

say() { printf '\n=== %s ===\n' "$*"; }

case "$STAGE" in
  data)
    bash "$ROOT/repro/run_all.sh" data
    ;;
  dump)
    say "PUP / Fisher top-30% variants"
    $PY "$ROOT/experiments/make_pup_variant.py" --archive "$ARCH" --out-dir "$REC/pup" \
        --scenes "$SCENES" --device cuda --n-views 4
    say "render every held-out view, 10 scene-checkpoints x 8 variants, + SSIM/LPIPS"
    $PY "$ROOT/experiments/dump_artifacts.py" --archive "$ARCH" --out "$REC/dump" \
        --pup-dir "$REC/pup" --scenes "$SCENES" --variants "$VARIANTS" \
        --profile full --gt-convention archive --device cuda --budget-mb 900 \
        --fidelity --lpips-net alex
    ;;
  audit)
    say "audit + Kolmogorov envelope (CPU)"
    $PY "$ROOT/experiments/audit_bound.py" --npz "$REC/dump" --out "$OUT/audit_bound.json"
    say "fidelity table (CPU, reads dump_summary.json)"
    $PY "$ROOT/tools/cviu_audit_tables.py" --dump "$REC/dump" --audit "$OUT/audit_bound.json" \
        --out-dir "$OUT"
    ;;
  all)
    bash "$0" data && bash "$0" dump && bash "$0" audit
    ;;
  *)
    echo "unknown stage: $STAGE (data|dump|audit|all)"; exit 2 ;;
esac
echo "CVIU_STAGE_DONE $STAGE $(date -Is)"
# Back to the workstation: $REC/dump/*.npz (~40 MB/checkpoint, the audit's only input),
# $REC/dump/dump_summary.json (PSNR/SSIM/LPIPS per variant per view), $OUT/*.json.
