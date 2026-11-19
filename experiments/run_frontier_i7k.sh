#!/usr/bin/env bash
# Fill the 2x-4x band for the four iteration_7000 twins.
#
# The frontier's low-rate points came from repricing the M1 render table, which only covers the
# four base scenes. So at the paper's own 3.33x budget the twins fell back to prune (p90), which
# undersells the very comparison we want to make. This renders the SH ladder on the twins and
# measures its bytes, so all eight assets have the same low-rate options.
set -euo pipefail

ROOT=${ROOT:-/workspace/code}
DATA=${DATA:-/workspace/data}
ARCH=${ARCH:-$DATA/out3dgs}
OUT=${OUT:-/workspace/res/frontier_i7k}
PY=${PY:-python3}
SCENES=${SCENES:-bicycle_i7k,flowers_i7k,stump_i7k,treehill_i7k}
VARIANTS=${VARIANTS:-clean,sh16_g16,sh12_g16,sh8_g16,p90}
SPECS=${SPECS:-sh16_g16,sh12_g16,sh8_g16}

export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT/dump"

stage=${1:-all}

dump() {
  echo "=== dump (${SCENES}) ==="
  IFS=',' read -ra SS <<< "$SCENES"
  for s in "${SS[@]}"; do
    echo "--- $s"
    "$PY" -u "$ROOT/experiments/qfp_rd.py" \
      --archive "$ARCH" --scenes "$s" --out "$OUT/dump" \
      --variant-set custom --variants "$VARIANTS" \
      --factor 4 --gt-convention archive --downsample 1 --device cuda --no-compress
  done
}

bytes() {
  echo "=== bytes (${SCENES}) ==="
  IFS=',' read -ra SS <<< "$SCENES"
  for s in "${SS[@]}"; do
    "$PY" -u "$ROOT/experiments/m4_bytes.py" \
      --archive "$ARCH" --scenes "$s" --specs "$SPECS" --level 12 --skip-flat \
      --out "$OUT/bytes_${s}.json"
  done
}

analyse() {
  echo "=== analyse ==="
  "$PY" - "$OUT" <<'PY'
import glob, json, os, sys
out = sys.argv[1]
scenes, crit, meta = [], {}, None
for p in sorted(glob.glob(os.path.join(out, "bytes_*.json"))):
    d = json.load(open(p))
    scenes += d.get("scenes", [])
    meta = meta or d.get("meta", {})
    crit.update(d.get("criteria", {}) or {})
dst = os.path.join(out, "i7k_bytes.json")
json.dump({"meta": meta or {}, "criteria": crit, "scenes": scenes}, open(dst, "w"), indent=1)
print(f"WROTE {dst} scenes={len(scenes)}")
PY
  "$PY" -u "$ROOT/experiments/m1_analyse.py" \
    --dump "$OUT/dump" --out "$OUT/m13_i7k.json" \
    --bytes-json "$OUT/i7k_bytes.json" \
    --rates 1,2,3,5,7,9,12,16 --n-splits 400 --protocol m3 --rate-need 2
  ls -l "$OUT"/*.json
}

case "$stage" in
  dump) dump ;;
  bytes) bytes ;;
  analyse) analyse ;;
  all) dump; bytes; analyse ;;
  *) echo "unknown stage $stage" >&2; exit 2 ;;
esac
echo "=== done: $stage ==="
