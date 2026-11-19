#!/usr/bin/env bash
# M16 measurement on the two scenes where we hold an authoritative 3DGS-30k checkpoint
# (bicycle 24.52 dB, stump 26.15 dB against published 25.11 / 26.66).  Archives were built by
# make_m360_archive.py from the mirror PLYs, so the cameras are already at images_4 and every
# stage must run with FACTOR=1.
set -euo pipefail
cd /workspace/code
export ARCH=/workspace/data/m360std
export SCENES=bicycle_mirror,stump_mirror
export FACTOR=1
export JOBS=2
mkdir -p /workspace/res/m16
bash experiments/run_m16.sh dump > /workspace/res/m16/run_dump.log 2>&1
bash experiments/run_m16.sh bytes > /workspace/res/m16/run_bytes.log 2>&1
bash experiments/run_m16.sh analyse > /workspace/res/m16/run_analyse.log 2>&1
echo M16_MEASURE_DONE