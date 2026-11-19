#!/usr/bin/env bash
# M20 probe/measure wrapper: the container needs `calib` importable, and `node exec`
# does not carry an exported PYTHONPATH through to a backgrounded job.
set -uo pipefail
export PYTHONPATH=/workspace/code/research/code:/workspace/code:/workspace/code/experiments
cd /workspace/code || exit 1
case "${1:-probe}" in
  probe)   shift; python experiments/m20_probe.py "$@" ;;
  measure) shift; python experiments/m20_measure.py "$@" ;;
  *) echo "usage: $0 probe|measure [args]" >&2; exit 2 ;;
esac
