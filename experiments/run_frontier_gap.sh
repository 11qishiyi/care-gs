#!/usr/bin/env bash
# Densify the SH ladder at the low-rate end (M13 gap fill).
#
# The frontier's 2x row is a mix of prune and scalar because the ladder jumped 16 -> 12 -> 8 bits,
# so for several assets the only affordable point at 2x was p90. Adding 24/20/14/10-bit SH turns the
# staircase into a real curve and costs four extra renders per asset.
set -euo pipefail

ROOT=${ROOT:-/workspace/code}
DATA=${DATA:-/workspace/data}
ARCH=${ARCH:-$DATA/out3dgs}
OUT=${OUT:-/workspace/res/frontier_gap}
PY=${PY:-python3}
SCENES=${SCENES:-bicycle,flowers,stump,treehill,bicycle_i7k,flowers_i7k,stump_i7k,treehill_i7k}
LADDER=${LADDER:-sh24_g16,sh20_g16,sh14_g16,sh10_g16}
VARIANTS=${VARIANTS:-clean,sh24_g16,sh20_g16,sh14_g16,sh10_g16}
JOBS=${JOBS:-3}

export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT/dump"

stage=${1:-all}

dump() {
  echo "=== dump ($SCENES) ==="
  IFS=',' read -ra SS <<< "$SCENES"
  for s in "${SS[@]}"; do
    "$PY" -u "$ROOT/experiments/qfp_rd.py" \
      --archive "$ARCH" --scenes "$s" --out "$OUT/dump" \
      --variant-set custom --variants "$VARIANTS" \
      --factor 4 --gt-convention archive --downsample 1 --device cuda --no-compress
  done
}

bytes() {
  echo "=== bytes ($SCENES) ==="
  IFS=',' read -ra SS <<< "$SCENES"
  i=0
  for s in "${SS[@]}"; do
    "$PY" -u "$ROOT/experiments/m4_bytes.py" \
      --archive "$ARCH" --scenes "$s" --specs "$LADDER" --level 12 --skip-flat \
      --out "$OUT/bytes_${s}.json" > "$OUT/bytes_${s}.log" 2>&1 &
    i=$((i + 1))
    if [ "$i" -ge "$JOBS" ]; then wait -n; fi
  done
  wait
  "$PY" - "$OUT" <<'PY'
import glob, json, os, sys
out = sys.argv[1]
scenes, crit, meta = [], {}, None
for p in sorted(glob.glob(os.path.join(out, "bytes_*.json"))):
    d = json.load(open(p))
    scenes += d.get("scenes", [])
    meta = meta or d.get("meta", {})
    crit.update(d.get("criteria", {}) or {})
dst = os.path.join(out, "gap_bytes.json")
json.dump({"meta": meta or {}, "criteria": crit, "scenes": scenes}, open(dst, "w"), indent=1)
print(f"WROTE {dst} scenes={len(scenes)}")
PY
}

analyse() {
  echo "=== analyse ==="
  "$PY" -u "$ROOT/experiments/m1_analyse.py" \
    --dump "$OUT/dump" --out "$OUT/m13_gap.json" \
    --bytes-json "$OUT/gap_bytes.json" \
    --rates 1,2,3,5,7 --n-splits 400 --protocol m3 --rate-need 2
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
