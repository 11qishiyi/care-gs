#!/usr/bin/env bash
# Node-side: report the zstd backend and self-test the M4 byte measurement.
# No quoting has to survive the matcli -> cmd.exe -> bash chain: the caller runs
# `bash experiments/m4_check.sh`, and everything else lives in this file.
set -u
cd /workspace/code || exit 2
python - <<'PY'
try:
    import zstandard
    print("zstandard", zstandard.__version__)
except Exception as exc:                      # noqa: BLE001 - report, do not raise
    print("zstandard MISSING:", type(exc).__name__, exc)
PY
echo "--- M4 self-test"
python -u experiments/m4_bytes.py --selftest
echo "--- analyser self-test (M1 + M3 criteria)"
python -u experiments/m1_analyse.py --selftest 2>&1 | tail -n 8
echo "--- byte ledger cross-check (qfp_rd vs m1_analyse)"
python -u experiments/m1_check_bytes.py 2>&1 | tail -n 2
echo M4_CHECK_DONE
