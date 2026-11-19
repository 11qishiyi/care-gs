#!/usr/bin/env bash
# Print one line per encoded anchor container: plan, bytes, bytes/primitive, ppa, anchors, voxel.
set -euo pipefail
DIR="${1:-/workspace/res/m27/enc}"
python3 - "$DIR" <<'PY'
import glob, json, os, sys
d = sys.argv[1]
print(f"{'plan':<18}{'bytes':>12}{'B/prim':>9}{'ppa':>7}{'anchors':>10}{'voxel':>9}")
for p in sorted(glob.glob(os.path.join(d, "*.json"))):
    r = json.load(open(p))
    print(f"{os.path.basename(p)[:-5]:<18}{r['bytes']:>12,}{r['b_per_prim']:>9.3f}"
          f"{r['ppa']:>7.2f}{r['n_anchor']:>10,}{r['voxel']:>9.4f}")
PY
