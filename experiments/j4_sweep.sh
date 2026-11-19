#!/usr/bin/env bash
# J4 sweep only (archives already built at /root/m360std). Writes rc to /root/j4.done.
set -uo pipefail
cd /root/j4
export PYTHONPATH=/root/j4
rm -f /root/j4.done
python qfp_rd.py --archive /root/m360std --scenes bicycle,stump --variant-set j4 \
    --out /root/res/j4 --factor 1 --gt-convention archive --device cuda \
    --budget-mb 2000 --fidelity --lpips-net alex > /root/j4_sweep.log 2>&1
echo "$?" > /root/j4.done
