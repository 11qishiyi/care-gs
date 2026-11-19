#!/usr/bin/env bash
# M21 setup on a fresh node: dependencies, the two scenes' COLMAP + reference PLYs, and the clean
# calibration that every ladder step is compared against.  Runs under nohup because `node exec`
# gives up after ~120 s of silence.
#
#   nohup bash experiments/m21_setup.sh > /workspace/res/m21/setup.log 2>&1 &
set -x
ROOT=/workspace/code
export ROOT DATA=/workspace/data ARCH=/workspace/data/m360std COLMAP=/workspace/data/mip360_colmap
export MODELS=/workspace/data/models
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p /workspace/res/m21

bash "$ROOT/experiments/run_m17.sh" deps
for s in bicycle stump; do
  SCENE="$s" bash "$ROOT/experiments/run_m17.sh" data || exit 1
  SCENE="$s" bash "$ROOT/experiments/run_m17.sh" base || exit 1
done
echo "SETUP_DONE"
