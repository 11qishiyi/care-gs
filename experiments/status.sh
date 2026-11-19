#!/usr/bin/env bash
# Node status probe: cheap, quote-free, safe to run through cmd.exe.
set -u
echo "== now: $(date -Is)"
for f in /workspace/res/m3_analyse.log /workspace/res/m3_dump.log /workspace/res/m4_dump.log; do
  if [ -f "$f" ]; then echo "-- $f"; tail -n "${TAILN:-6}" "$f"; fi
done
echo "== json"
ls -l /workspace/res/m3/*.json /workspace/res/m4/*.json 2>/dev/null
echo "== procs"
ps -eo pid,etime,pcpu,cmd | grep -E 'm1_analyse|qfp_rd|m4_bytes' | grep -v grep | head -n 5
