#!/usr/bin/env bash
# M40 -- the deployment table: 4 MB vs 256 KB frames on three scenes, plus decode cost and damage.
#
#   bash experiments/run_m40.sh setup <scene>
#   bash experiments/run_m40.sh build <scene> <4194304|262144>
#   bash experiments/run_m40.sh cost  <scene> <bytes>
#   bash experiments/run_m40.sh damage <scene> <tag> <0.001|0.01>
#   bash experiments/run_m40.sh all <scene>
set -uo pipefail
ROOT=/workspace/code
OUT=/workspace/res/m40
ARCH=/workspace/data/m360std
COLMAP=/workspace/data/mip360_colmap
CACHE=/mnt/m35cache
SPEC="gp6-6-6_c8_sh3"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
mkdir -p "$OUT"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/m40.log"; }

case "${1:-all}" in
  setup)
    S="${2:?scene}"
    mkdir -p "$(dirname "/workspace/data/m20/$S.ply")"
    [ -s "$CACHE/$S.ply" ] || { log "no cached model for $S"; exit 1; }
    ln -sf "$CACHE/$S.ply" "/workspace/data/m20/$S.ply"
    [ -d "$COLMAP/$S/sparse/0" ] || SCENES="$S" bash "$ROOT/experiments/fetch_m360_colmap.sh" 2>&1 | tail -1
    [ -d "$ARCH/output/$S" ] || {
      mkdir -p "/workspace/data/models/output/$S/point_cloud/iteration_30000"
      ln -sf "$CACHE/$S.ply" "/workspace/data/models/output/$S/point_cloud/iteration_30000/point_cloud.ply"
      SCENES="$S" bash "$ROOT/experiments/run_m17.sh" base 2>&1 | tail -1
    }
    log "setup $S ok"
    ;;
  build)
    S="${2:?scene}"; F="${3:?frame}"
    tag=$([ "$F" = "262144" ] && echo f256k || echo f4m)
    t0=$(date +%s)
    "$PY" -u "$ROOT/experiments/m24_alpha.py" --ply "/workspace/data/m20/$S.ply" \
      --plans "$SPEC:16:48" --out "$OUT/$S/$tag" --no-ply --no-legacy --suffix "_m40$S$tag" \
      --min-frame "$F" > "$OUT/build_${S}_${tag}.log" 2>&1
    t1=$(date +%s)
    echo "enc_${S}_${tag} $((t1-t0)) s" >> "$OUT/m40_encode.txt"
    f=$(ls "$OUT/$S/$tag"/*.gs1 2>/dev/null | head -1)
    echo "$S $tag $f $(stat -c %s "$f")" >> "$OUT/m40_sizes.txt"
    tail -1 "$OUT/m40_sizes.txt"
    ;;
  cost)
    S="${2:?scene}"; F="${3:?file}"
    "$PY" -u "$ROOT/tools/m25_time.py" --glob "$F" >> "$OUT/m40_cost.txt" 2>&1
    tail -2 "$OUT/m40_cost.txt"
    ;;
  damage)
    S="${2:?scene}"; TAG="${3:?tag}"; B="${4:?burst}"
    # control first: every damage PSNR is read against the untouched container rendered on this node
    if [ ! -f "$OUT/$S/dmg_$TAG/control.json" ]; then
      "$PY" -u "$ROOT/tools/m33_damage.py" --gs1 "$(ls "$OUT/$S/$TAG"/*.gs1 | head -1)" \
        --out "$OUT/$S/dmg_$TAG" --archive "$ARCH" --scene-dir "$COLMAP/$S" \
        --tag "m40_${S}_${TAG}" --only control --render > "$OUT/control_${S}_${TAG}.log" 2>&1
      tail -1 "$OUT/control_${S}_${TAG}.log"
    fi
    "$PY" -u "$ROOT/tools/m33_damage.py" --gs1 "$(ls "$OUT/$S/$TAG"/*.gs1 | head -1)" \
      --out "$OUT/$S/dmg_$TAG" --archive "$ARCH" --scene-dir "$COLMAP/$S" \
      --tag "m40_${S}_${TAG}_$B" --only damage --burst "$B" --render \
      > "$OUT/damage_${S}_${TAG}_${B}.log" 2>&1
    tail -2 "$OUT/damage_${S}_${TAG}_${B}.log"
    ;;
  all)
    S="${2:?scene}"
    bash "$0" setup "$S"
    for F in 4194304 262144; do
      bash "$0" build "$S" "$F"
      tag=$([ "$F" = "262144" ] && echo f256k || echo f4m)
      bash "$0" cost "$S" "$OUT/$S/$tag/*.gs1"
      bash "$0" damage "$S" "$tag" 0.001
      bash "$0" damage "$S" "$tag" 0.01
    done
    cat "$OUT/m40_sizes.txt" "$OUT/m40_encode.txt"
    ;;
  *) echo "use setup|build|cost|damage|all [scene] [frame|tag] [burst]" >&2; exit 2 ;;
esac
