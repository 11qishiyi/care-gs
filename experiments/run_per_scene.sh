#!/usr/bin/env bash
# Per-scene region_coverage in parallel (the serial run is ~15 min/scene).
# Each scene gets its own one-npz directory so region_coverage's --max-scenes
# filter is unnecessary; outputs land in /workspace/res/rev/region_<scene>.json.
set -u
NPZDIR=${1:-/workspace/res/rev/dump}
OUTDIR=${2:-/workspace/res/rev}
PAR=${3:-4}
cd /workspace/code || exit 1
mkdir -p "$OUTDIR/per"
for f in "$NPZDIR"/*.npz; do
  s=$(basename "$f" .npz)
  mkdir -p "$OUTDIR/per/$s"
  ln -sf "$f" "$OUTDIR/per/$s/$s.npz"
done
ls "$OUTDIR/per" | tr '\n' ' '; echo
printf '%s\n' "$OUTDIR"/per/*/ | xargs -P "$PAR" -I{} bash -c '
  d="{}"; s=$(basename "$d")
  out="'"$OUTDIR"'/region_${s}.json"
  [ -s "$out" ] && { echo "SKIP $s"; exit 0; }
  echo "START $s"
  python experiments/region_coverage.py --npz "$d" --out "$out" \
      --granularities pixel,block --blocks 64 \
      --variants clean,prune50,prune30,pup30,shdeg1,quant8,quant6,quant4 \
      > "/data/runs/rc_${s}.log" 2>&1
  echo "DONE $s rc=$?"
'
echo ALLDONE
