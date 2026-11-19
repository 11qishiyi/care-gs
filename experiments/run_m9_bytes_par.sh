#!/usr/bin/env bash
# Measure M9 bytes for every asset, 3 at a time, then merge into one json.
#   bash experiments/run_m9_bytes_par.sh
set -uo pipefail

ROOT="${ROOT:-/workspace/code}"
ARCH="${ARCH:-/workspace/data/out3dgs}"
OUT="${OUT:-/workspace/res/m9}"
PY="${PY:-python3}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
SCENES="${SCENES:-bicycle,flowers,stump,treehill,bicycle_i7k,flowers_i7k,stump_i7k,treehill_i7k}"
LEVEL="${LEVEL:-12}"
JOBS="${JOBS:-3}"
SPECS="$("$PY" -c 'import qfp_rd as Q; print(Q.M9_VARIANTS)')"

log() { echo "[$(date +%H:%M:%S)] $*"; }
mkdir -p "$OUT/bytes"

for sc in ${SCENES//,/ }; do
  log "start $sc"
  "$PY" -u "$ROOT/experiments/m4_bytes.py" \
    --archive "$ARCH" --scenes "$sc" --skip-flat --level "$LEVEL" \
    --specs "$SPECS" --out "$OUT/bytes/$sc.json" \
    > "$OUT/bytes/$sc.log" 2>&1 &
  while [ "$(jobs -r | wc -l)" -ge "$JOBS" ]; do sleep 5; done
done
wait
log "all assets measured"

"$PY" - "$OUT" <<'PY'
import json, os, sys
out = sys.argv[1]
d = os.path.join(out, "bytes")
scenes, criteria = [], {}
for f in sorted(os.listdir(d)):
    if not f.endswith(".json"):
        continue
    doc = json.load(open(os.path.join(d, f)))
    scenes += doc.get("scenes", [])
    criteria.update(doc.get("criteria", {}))
doc = dict(specs=json.load(open(os.path.join(d, sorted(os.listdir(d))[0]))).get("specs", []),
           level=12, scenes=scenes, criteria=criteria)
json.dump(doc, open(os.path.join(out, "m9_bytes.json"), "w"), indent=1)
print(f"MERGED {len(scenes)} scene(s) -> {os.path.join(out, 'm9_bytes.json')}")
PY
