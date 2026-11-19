#!/usr/bin/env bash
# Measure the finetuned 20 % bicycle model on the published axes: dump two variants, measure their
# bytes, and fold the rows into the M16 curve so the pruned point sits next to HAC/PCGS.
set -euo pipefail
cd /workspace/code
SCENES=bicycle_mirror_ft
bash experiments/run_m16.sh dump   > /workspace/res/m16/ft_dump.log   2>&1 || true
echo FT_DUMP_DONE