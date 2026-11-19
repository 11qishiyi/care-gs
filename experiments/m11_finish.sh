#!/usr/bin/env bash
# Wait for the four surviving byte measurements, merge, analyse, and score M11.
#
# The parent of the ``bytes`` stage was killed when its ``matcli node exec`` hit the
# 70-minute idle limit, so the children survive but nobody was left to merge.  This
# script picks up from there and is safe to re-run: it waits for all eight per-asset
# json files, merges them, runs the measured-axis analysis and the P1/P2/P3 report.
set -uo pipefail

ROOT="${ROOT:-/workspace/code}"
OUT="${OUT:-/workspace/res/m11}"
PY="${PY:-python3}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
cd "$ROOT" || exit 2

echo "[$(date +%H:%M:%S)] waiting for 8 per-asset byte files"
for i in $(seq 1 400); do
  n=$(ls "$OUT"/bytes/bytes_*.json 2>/dev/null | wc -l)
  if [ "$n" -ge 8 ]; then break; fi
  sleep 20
done
echo "[$(date +%H:%M:%S)] byte files: $(ls "$OUT"/bytes/bytes_*.json 2>/dev/null | wc -l)"

"$PY" - "$OUT" <<'PY'
import glob, json, os, sys
out = sys.argv[1]
merged = {"scenes": [], "backend": None}
for f in sorted(glob.glob(os.path.join(out, "bytes", "bytes_*.json"))):
    with open(f, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    merged["scenes"].extend(d.get("scenes", []))
    merged["backend"] = d.get("backend") or merged["backend"]
dst = os.path.join(out, "m11_bytes.json")
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(merged, fh, indent=1)
print("MERGED", dst, len(merged["scenes"]), "assets")
PY

echo "[$(date +%H:%M:%S)] analysis on the measured axis"
"$PY" -u experiments/m1_analyse.py \
  --dump "$OUT/dump" --out "$OUT/m11_rd.json" \
  --bytes-json "$OUT/m11_bytes.json" \
  --rates 1,2,3,5,7,9,12,16,24,32 --n-splits 400 --protocol m3 --rate-need 3 \
  > "$OUT/m11_analyse.log" 2>&1
echo "ANALYSE_EXIT=$?"

"$PY" -u experiments/m11_report.py --json "$OUT/m11_rd.json" --out "$OUT/m11_report.md" \
  > "$OUT/m11_report.log" 2>&1
echo "REPORT_EXIT=$?"
tail -25 "$OUT/m11_report.log"
echo "[$(date +%H:%M:%S)] M11_FINISH_DONE"
