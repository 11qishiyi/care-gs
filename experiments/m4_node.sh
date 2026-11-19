#!/usr/bin/env bash
# Node-side wrapper: install zstandard, then self-test the M4 byte measurement.
# Kept as a file so nothing has to survive three layers of quoting.
set -u
cd /workspace/code || exit 2
python -m pip install --quiet zstandard
echo "--- zstandard installed: $(python -c 'import zstandard; print(zstandard.__version__)' 2>&1)"
python -u experiments/m4_bytes.py --selftest
echo "--- analyser self-test (E1/E2/E3 included)"
python -u experiments/m1_analyse.py --selftest 2>&1 | tail -n 6
echo "--- m1_check_bytes"
python -u experiments/m1_check_bytes.py 2>&1 | tail -n 2
echo M4_SELFTEST_DONE
