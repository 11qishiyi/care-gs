#!/usr/bin/env bash
# Wait for the M15 byte measurements, merge, analyse, and score.
#
# The parent of the ``bytes`` stage can be killed when its ``matcli node exec`` hits the
# 70-minute idle limit; the children survive but nobody is left to merge.  This script
# picks up from there and is safe to re-run: it waits for all eight per-asset json files,
# merges them, runs the measured-axis analysis and the R1/R2/R3 report.
set -uo pipefail

ROOT="${ROOT:-/workspace/code}"
OUT="${OUT:-/workspace/res/m15}"
PY="${PY:-python3}"
WANT="${WANT:-8}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
cd "$ROOT" || exit 2

echo "[$(date +%H:%M:%S)] waiting for $WANT per-asset byte files"
for i in $(seq 1 400); do
  n=$(ls "$OUT"/bytes/bytes_*.json 2>/dev/null | wc -l)
  if [ "$n" -ge "$WANT" ]; then break; fi
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
dst = os.path.join(out, "m15_bytes.json")
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(merged, fh, indent=1)
print("MERGED", dst, len(merged["scenes"]), "assets")
PY

echo "[$(date +%H:%M:%S)] analysis on the measured axis"
"$PY" -u experiments/m1_analyse.py \
  --dump "$OUT/dump" --out "$OUT/m15_rd.json" \
  --bytes-json "$OUT/m15_bytes.json" \
  --rates 1,2,3,5,7,9,10,11,12,16,24 --n-splits 400 --protocol m3 --rate-need 3 \
  > "$OUT/m15_analyse.log" 2>&1
echo "ANALYSE_EXIT=$?"

"$PY" -u experiments/m15_report.py --json "$OUT/m15_rd.json" --out "$OUT/m15_report.md" \
  > "$OUT/m15_report.log" 2>&1
echo "REPORT_EXIT=$?"
tail -30 "$OUT/m15_report.log"
echo "[$(date +%H:%M:%S)] M15_FINISH_DONE"
