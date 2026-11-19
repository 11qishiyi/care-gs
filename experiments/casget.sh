#!/usr/bin/env bash
# casget.sh URL DST --- download one file through the signed CAS URL behind the mirror.
#
# The mirror's own redirect (`302 -> cas-bridge.xethub.hf.co`) is what breaks from MatPool's network: a plain
# `curl -L` on the mirror URL 502s, while the CAS URL answers 200. So resolve the Location once and fetch it.
#
#   bash casget.sh <url> <dst>
#   exit 0 ok / 1 already present / 2 no location / 3 transfer failed / 4 empty file
set -uo pipefail
U="$1"; D="$2"
[ -s "$D" ] && exit 1
mkdir -p "$(dirname "$D")"
LOC=""
for i in 1 2 3 4 5 6; do
  LOC=$(curl -sSI --max-time 30 "$U" | awk 'tolower($1)=="location:"{v=$2} END{gsub(/\r/,"",v);print v}')
  [ -n "${LOC:-}" ] && break
  sleep $((i * 2))
done
[ -z "${LOC:-}" ] && exit 2
curl -sSL --retry 3 --max-time 300 -o "$D.part" "$LOC" || { rm -f "$D.part"; exit 3; }
[ -s "$D.part" ] || { rm -f "$D.part"; exit 4; }
mv "$D.part" "$D"
exit 0
