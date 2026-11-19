#!/usr/bin/env bash
# Measure the bytes of the low-rate end of the SH ladder (16/12/8-bit SH at full geometry).
#
# Why: the M5 grid starts at 4.18x because it only carries 8-bit-and-below SH. The paper's own
# operating point -- "keep 30%" -- is 3.33x, which therefore has no quantisation-only entry at
# all, so the frontier table showed prune alone in the 2-3x region. The renders for SH 16/12/8
# already exist (m1_rd), so the only missing piece is a *measured* byte count for those four
# specs. That is what this script collects; no rendering happens here.
set -euo pipefail

ROOT=${ROOT:-/workspace/code}
DATA=${DATA:-/workspace/data}
ARCH=${ARCH:-$DATA/out3dgs}
OUT=${OUT:-/workspace/res/frontier}
PY=${PY:-python3}
SCENES=${SCENES:-bicycle,flowers,stump,treehill}
SPECS=${SPECS:-sh16_g16,sh12_g16,sh8_g16,m16_o8_sh8,m16_o8_sh6}
LEVEL=${LEVEL:-12}
JOBS=${JOBS:-4}

export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT"

stage=${1:-all}

ARCHIVE_URL=${ARCHIVE_URL:-"https://www.modelscope.cn/api/v1/datasets/Jackie137/3dgs-Output/repo?Revision=master&FilePath=output-3dgs.tar.gz"}
ARCHIVE_BYTES=${ARCHIVE_BYTES:-9587304864}

data() {
  echo "=== data ==="
  mkdir -p "$DATA"
  local tgz="$DATA/output-3dgs.tar.gz"
  if [ ! -f "$tgz" ] || [ "$(stat -c %s "$tgz")" != "$ARCHIVE_BYTES" ]; then
    curl -L --retry 3 -C - -o "$tgz" "$ARCHIVE_URL"
  fi
  echo "archive bytes $(stat -c %s "$tgz") (want $ARCHIVE_BYTES)"
  if [ ! -d "$DATA/output" ]; then
    tar -xzf "$tgz" -C "$DATA"
    if [ -d "$DATA/output-3dgs/output" ]; then mv "$DATA/output-3dgs/output" "$DATA/output"; fi
  fi
  if [ -d "$DATA/output/bicycle" ] && [ ! -e "$ARCH/output" ]; then
    mkdir -p "$ARCH"
    ln -sfn "$DATA/output" "$ARCH/output"
  fi
  for s in bicycle flowers stump treehill; do
    echo "$s cams=$(ls "$ARCH/output/$s/cameras.json" 2>/dev/null | wc -l) \
gt=$(ls "$ARCH/output/$s/test/ours_40000/gt" 2>/dev/null | wc -l) \
ply=$(du -h "$ARCH/output/$s/point_cloud/iteration_40000/point_cloud.ply" 2>/dev/null | cut -f1)"
  done
}

setup() {
  echo "=== setup ==="
  "$PY" -m pip install --quiet --no-input plyfile pillow packaging zstandard
  "$PY" - <<'PY'
import torch, importlib.util
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
print("gsplat", importlib.util.find_spec("gsplat") is not None)
PY
  if [ ! -d "$ARCH/output/bicycle" ]; then
    if [ -d "$DATA/output/bicycle" ]; then
      ln -sfn "$DATA" "$ARCH"
    else
      echo "archive missing under $ARCH/output -- download it first" >&2
      exit 1
    fi
  fi
  n=$("$PY" -c "import glob;print(len(glob.glob('$ARCH/output/*/point_cloud/iteration_40000/point_cloud.ply')))")
  echo "assets with ply: $n"
  "$PY" "$ROOT/experiments/prep_aliases.py" --archive "$ARCH" || true
}

bytes() {
  echo "=== bytes (per asset, $JOBS parallel) ==="
  IFS=',' read -ra SS <<< "$SCENES"
  i=0
  for s in "${SS[@]}"; do
    "$PY" -u "$ROOT/experiments/m4_bytes.py" \
      --archive "$ARCH" --scenes "$s" --specs "$SPECS" --level "$LEVEL" --skip-flat \
      --out "$OUT/bytes_${s}.json" > "$OUT/bytes_${s}.log" 2>&1 &
    i=$((i + 1))
    if [ "$i" -ge "$JOBS" ]; then wait -n; fi
  done
  wait
  echo "=== merge ==="
  "$PY" - "$OUT" <<'PY'
import glob, json, os, sys
out = sys.argv[1]
rows, meta, crit = [], None, {}
for p in sorted(glob.glob(os.path.join(out, "bytes_*.json"))):
    d = json.load(open(p))
    rows += d.get("rows", [])
    if meta is None:
        meta = d.get("meta", {})
        crit = d.get("criteria", {})
    else:
        for r in d.get("rows", []):
            pass
doc = {"meta": meta or {}, "criteria": crit, "rows": rows}
dst = os.path.join(out, "frontier_bytes.json")
json.dump(doc, open(dst, "w"), indent=1)
print(f"WROTE {dst} rows={len(rows)}")
PY
}

case "$stage" in
  data) data ;;
  setup) setup ;;
  bytes) bytes ;;
  all) data; setup; bytes ;;
  *) echo "unknown stage $stage" >&2; exit 2 ;;
esac
echo "=== done: $stage ==="
