#!/usr/bin/env bash
# Node-side probes for the M16 round.  Every command here is invoked as one exec with no
# quoting in the argument, because matcli splits the --command string on whitespace and the
# node shell then re-parses quotes: anything with double quotes inside fails as
# "unknown option".  Keeping the probes in a file avoids the whole class of problem.
#
#   bash experiments/node_probe.sh progress
#   bash experiments/node_probe.sh scenes
#   bash experiments/node_probe.sh setup_tail
#   bash experiments/node_probe.sh disk
set -u
case "${1:-progress}" in
  progress)
    for f in /workspace/data/models_official/output/*/point_cloud/iteration_30000/point_cloud.ply.part; do
      [ -f "$f" ] || continue
      printf '%s %s\n' "$(stat -c %s "$f")" "$f"
    done
    du -sb /workspace/data/models_official
    ;;
  scenes)
    ls /workspace/data/m360std/output 2>/dev/null || echo no_archive
    du -sh /workspace/data/models_official 2>/dev/null
    du -sh /workspace/data/mip360_full 2>/dev/null
    ;;
  setup_tail)
    tail -n "${2:-15}" /workspace/res/m16/setup.log
    ;;
  disk)
    df -h / | tail -1
    ;;
  *)
    echo "unknown probe: $1" >&2
    exit 2
    ;;
esac
