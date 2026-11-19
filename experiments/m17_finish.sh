#!/usr/bin/env bash
# Finish the M17 pilot: measure bytes for the pruned/finetuned entries one at a time, merge,
# analyse, and render the C5 report.
#
# Why not the `compress` stage in run_m17.sh: that one launched three m4_bytes jobs and used
# `wait -n`, and the 6.1 M-primitive base entry was killed outright (no message, no json).  Under
# `set -e` a failed `wait -n` aborted the stage and took the two healthy jobs with it.  Here every
# job runs alone, a failure is recorded and the loop continues, and the base entry is skipped --
# its rows were measured in M16 and re-measuring 1.4 GB of zstd-12 buys nothing.
set -uo pipefail
cd /workspace/code
OUT=/workspace/res/m17
ARCH=/workspace/data/m360std
LEVEL=12
SPECS="vq12_c8_o8,c8_o8_sh3,c10_o8_sh3,m16_o8_sh2,msc12-6-a1_c8_o8"
export PYTHONPATH=/workspace/code/research/code:/workspace/code:/workspace/code/experiments

mkdir -p "$OUT/bytes"
for sc in bicycle_k50l3_ft bicycle_k35l3_ft bicycle_k50l3_pre bicycle_k35l3_pre; do
  f="$OUT/bytes/bytes_$sc.json"
  if [ -s "$f" ]; then echo "[$(date +%H:%M:%S)] $sc: cached"; continue; fi
  echo "[$(date +%H:%M:%S)] $sc: measuring"
  python3 -u experiments/m4_bytes.py --archive "$ARCH" --scenes "$sc" --level "$LEVEL" \
    --specs "$SPECS" --out "$f" > "$OUT/bytes/$sc.log" 2>&1
  echo "[$(date +%H:%M:%S)] $sc: exit $? ($(tail -1 "$OUT/bytes/$sc.log"))"
done

python3 - "$OUT" <<'PY'
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

python3 -u experiments/m1_analyse.py --dump "$OUT/dump" --out "$OUT/m17_rd.json" \
  --bytes-json "$OUT/m17_bytes.json" \
  --rates 1,2,3,5,7,9,12,16,24,40,60 --n-splits 400 --protocol m3 --rate-need 3
python3 -u experiments/m17_report.py --rd "$OUT/m17_rd.json" --bytes "$OUT/m17_bytes.json" \
  --out "$OUT/m17_report.md" --json "$OUT/m17_report.json"
echo "M17_FINISH_DONE"
