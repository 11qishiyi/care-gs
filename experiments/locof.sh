#!/usr/bin/env bash
# locof.sh URL --- print the signed CAS URL behind a mirror URL.
#
# The mirror answers 502 to MatPool's egress on the *redirect* itself, while the CAS URL it points at serves 200/206.
# Every download on the node therefore starts here. Retries with backoff because the mirror rate-limits the HEAD.
set -uo pipefail
U="$1"
for i in 1 2 3 4 5 6; do
  LOC=$(curl -sSI --max-time 30 "$U" | awk 'tolower($1)=="location:"{v=$2} END{gsub(/\r/,"",v);print v}')
  if [ -n "${LOC:-}" ]; then printf '%s\n' "$LOC"; exit 0; fi
  sleep $((i * 2))
done
exit 1
