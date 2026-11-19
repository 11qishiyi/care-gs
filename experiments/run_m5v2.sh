#!/usr/bin/env bash
# M5 v2: re-measure the shipped byte cost per (asset, spec) with the CORRECTED codec
# (band truncation slice fixed, SH block-scale stream charged).  One process per scene
# so a crash on one asset cannot lose the others; results are merged at the end.
set -u
cd /workspace/code || exit 2
ARCH=${ARCH:-/workspace/data/out3dgs}
OUT=${OUT:-/workspace/res/m5v2}
SCENES=${SCENES:-bicycle,flowers,stump,treehill,bicycle_i7k,flowers_i7k,stump_i7k,treehill_i7k}
SPECS=${SPECS:-clean,p90,p70,p50,p30,p20,p10,p05,m16_o8_sh8,m16_o8_sh6,m16_o8_sh4,m16_o8_sh3,m16_o8_sh2,m16_o6_sh3,m16_o6_sh2,m18_o6_sh3,d2_m16_o8_sh8,d1_m16_o8_sh8,d0_m16_o8_sh8,d2_m16_o8_sh4,d1_m16_o8_sh4}
LEVEL=${LEVEL:-12}
mkdir -p "$OUT"
fail=0
for sc in ${SCENES//,/ }; do
  if [ -s "$OUT/bytes_$sc.json" ]; then
    echo "SKIP $sc (already measured)"
    continue
  fi
  echo "=== $sc ==="
  python -u experiments/m4_bytes.py \
    --archive "$ARCH" --scenes "$sc" --specs "$SPECS" \
    --level "$LEVEL" --skip-flat \
    --out "$OUT/bytes_$sc.json" || { echo "FAILED $sc"; fail=$((fail+1)); }
done
python -u - "$OUT" <<'PY'
import glob, json, os, sys
out = sys.argv[1]
merged = {"level": None, "codecs": None, "shipped": None, "backend": None,
          "includes_scale_bytes": True, "specs": None, "scenes": []}
for path in sorted(glob.glob(os.path.join(out, "bytes_*.json"))):
    d = json.load(open(path))
    for k in ("level", "codecs", "shipped", "backend", "specs"):
        if merged.get(k) is None and d.get(k) is not None:
            merged[k] = d[k]
    merged["scenes"].extend(d.get("scenes", []))
json.dump(merged, open(os.path.join(out, "m5_bytes.json"), "w"))
print("MERGED", len(merged["scenes"]), "scene(s) ->", os.path.join(out, "m5_bytes.json"))
PY
echo "=== m5v2 bytes finished, failing scene(s): $fail ==="
