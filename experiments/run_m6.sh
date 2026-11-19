#!/usr/bin/env bash
# M6: how much redundancy is left in the shipped format?
#
#   bash experiments/run_m6.sh a          # coder comparison on two heavy assets (M6a)
#   bash experiments/run_m6.sh b          # optional: re-measure the whole grid with c3
#
# M6a writes /workspace/res/m6/m6_codec.json.  It is already in the row schema that
# `m1_analyse.py --bytes-json` consumes, but it only covers two assets and five specs,
# so it is used for H1/H2 (coder quality), not for the RD replay.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PY=${PY:-python3}
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
ARCH=${ARCH:-/workspace/data/out3dgs}
OUT=${OUT:-/workspace/res/m6}
STAGE=${1:-a}
LEVEL=${LEVEL:-12}

mkdir -p "$OUT"

if [ "$STAGE" = "a" ]; then
  SCENES=${SCENES:-stump,flowers}
  SPECS=${SPECS:-clean,p30,m16_o8_sh4,m16_o8_sh3,m16_o6_sh2}
  echo "== M6a: coder comparison, scenes=$SCENES specs=$SPECS level=$LEVEL"
  "$PY" -u "$ROOT/experiments/m6_codec.py" \
    --archive "$ARCH" --scenes "$SCENES" --specs "$SPECS" --level "$LEVEL" \
    --out "$OUT/m6_codec.json"
elif [ "$STAGE" = "b" ]; then
  # The full grid with the better coder, so the RD curves can be replayed on it.
  # 21 specs x 8 assets with c3 is slow (bit planes are ~2x the work of plain zstd),
  # so this is only run when M6a shows the coder matters.
  SCENES=${SCENES:-bicycle,flowers,stump,treehill,bicycle_i7k,flowers_i7k,stump_i7k,treehill_i7k}
  SPECS=${SPECS:-clean,p90,p70,p50,p30,p20,p10,p05,m16_o8_sh8,m16_o8_sh6,m16_o8_sh4,m16_o8_sh3,m16_o8_sh2,m16_o6_sh3,m16_o6_sh2,m18_o6_sh3,d2_m16_o8_sh8,d1_m16_o8_sh8,d0_m16_o8_sh8,d2_m16_o8_sh4,d1_m16_o8_sh4}
  for scene in $(echo "$SCENES" | tr ',' ' '); do
    echo "== M6b: $scene"
    "$PY" -u "$ROOT/experiments/m6_codec.py" \
      --archive "$ARCH" --scenes "$scene" --specs "$SPECS" --level "$LEVEL" \
      --out "$OUT/m6_all_${scene}.json"
  done
  "$PY" - <<'PY'
import glob, json, os
parts = sorted(glob.glob('/workspace/res/m6/m6_all_*.json'))
doc = {"level": 12, "shipped": "c3_delta_planes", "includes_scale_bytes": True, "scenes": []}
for p in parts:
    with open(p) as f:
        d = json.load(f)
    doc["scenes"].extend(d.get("scenes", []))
with open('/workspace/res/m6/m6_all.json', 'w') as f:
    json.dump(doc, f, indent=1)
print(f"MERGED {len(doc['scenes'])} scene(s) -> /workspace/res/m6/m6_all.json")
PY
else
  echo "usage: bash experiments/run_m6.sh {a|b}" >&2
  exit 2
fi

echo "=== m6 stage $STAGE finished with $? ==="
