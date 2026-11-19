#!/usr/bin/env bash
# M27 follow-up: the offset depth is a *choice*, and 3 bits (an 8-level grid inside the voxel) is
# 1.3 cm at ppa 8 -- coarser than the shelf's position quantum by an order of magnitude.  Before the
# anchor representation is judged, spend the bytes where they were saved.
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m27/enc
PLY=/workspace/data/models/output/bicycle/point_cloud/iteration_30000/point_cloud.ply
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"

run() {
  local name="$1" keep="$2" ob="$3"
  echo "[$(date +%H:%M:%S)] encode $name (per-primitive: ${keep:-none}, offset bits $ob)"
  python3 -u "$ROOT/experiments/m27_anchor.py" --ply "$PLY" --out "$OUT/o_$name.gs1" \
    --ppa 8 --rank 16 --bits 48 --offset-bits "$ob" --dc-bits 6 --per-primitive "$keep" \
    > "/workspace/res/m27/o_$name.log" 2>&1
  grep -h -e bytes -e b_per_prim "/workspace/res/m27/o_$name.log" | tr -d '\n'; echo " <- $name"
}

run all_o5   ""             5
run all_o6   ""             6
run ppq_o5   "opac,quat,scale" 5
