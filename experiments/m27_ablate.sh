#!/usr/bin/env bash
# M27 ablation: which attribute can be shared by a voxel and which has to stay per primitive.
#   bash experiments/m27_ablate.sh            # encode the four ablation variants at ppa 8
set -euo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m27/enc
PLY=/workspace/data/models/output/bicycle/point_cloud/iteration_30000/point_cloud.ply
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT"

# variant name -> attributes kept per primitive
run() {
  local name="$1" keep="$2"
  echo "[$(date +%H:%M:%S)] encode $name (per-primitive: ${keep:-none})"
  python3 -u "$ROOT/experiments/m27_anchor.py" --ply "$PLY" --out "$OUT/v_$name.gs1" \
    --ppa 8 --rank 16 --bits 48 --offset-bits 3 --dc-bits 6 --per-primitive "$keep" \
    > "/workspace/res/m27/v_$name.log" 2>&1
}

run all      ""
run opac     "opac"
run quat     "quat"
run opacquat "opac,quat"
run opacquat_scale "opac,quat,scale"
bash "$ROOT/experiments/m27_sizes.sh" "$OUT" | tail -8
