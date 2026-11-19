#!/usr/bin/env bash
# M21: a file worth truncating.  Two artefacts out of one codec -- the best-rate file and a
# rate-scalable file whose prefixes are complete models at lower colour precision -- and the
# measured ladder (bytes -> PSNR) of the scalable one.
#
#   bash experiments/run_m21.sh deps data base
#   bash experiments/run_m21.sh encode    # <scene>_<spec>.gs1 and <scene>_<spec>_p.gs1
#   bash experiments/run_m21.sh ladder    # truncate at every layer boundary, decode, export PLY
#   bash experiments/run_m21.sh render    # archive entry + held-out PSNR for every ladder step
#   bash experiments/run_m21.sh timing    # decode time / peak RSS, 2 scenes x 2 specs
#   bash experiments/run_m21.sh all
set -euo pipefail

ROOT="${ROOT:-/workspace/code}"
DATA="${DATA:-/workspace/data}"
ARCH="${ARCH:-$DATA/m360std}"
COLMAP="${COLMAP:-$DATA/mip360_colmap}"
OUT="${OUT:-/workspace/res/m21}"
PY="${PY:-python3}"
LEVEL="${LEVEL:-12}"
FACTOR="${FACTOR:-1}"
SCENES="${SCENES:-bicycle,stump}"
#: c10 is the near-lossless shelf row, c8 the cheaper one; both are 3-bit ladders, so both can be
#: made rate-scalable.  vq is not: a codebook index is not a bit-plane.
SPECS="${SPECS:-c10_o8_sh3,c8_o8_sh3}"
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
mkdir -p "$OUT"

log() { echo "[$(date +%H:%M:%S)] $*"; }

stage_encode() {
  cd "$ROOT"
  log "=== best-rate files ==="
  "$PY" -u experiments/m19_codec.py --archive "$ARCH" --scenes "$SCENES" --specs "$SPECS" \
    --out "$OUT/models" --level "$LEVEL" --deck 2>&1 | tee "$OUT/encode.log" | tail -20
  log "=== rate-scalable files ==="
  "$PY" -u experiments/m19_codec.py --archive "$ARCH" --scenes "$SCENES" --specs "$SPECS" \
    --out "$OUT/models" --level "$LEVEL" --progressive --deck 2>&1 \
    | tee "$OUT/encode_p.log" | tail -20
  log "=== files ==="
  ls -l "$OUT/models" | tail -20
}

stage_ladder() {
  cd "$ROOT"
  for scene in ${SCENES//,/ }; do
    for spec in ${SPECS//,/ }; do
      f="$OUT/models/${scene}_${spec}_p.gs1"
      [ -s "$f" ] || { log "$scene $spec: no scalable file"; continue; }
      log "--- ladder ${scene} ${spec} ---"
      "$PY" -u experiments/m21_ladder.py --file "$f" --out "$OUT/cut" \
        --ply-dir "$OUT/ply" --json "$OUT/ladder_${scene}_${spec}.json" 2>&1 | tee -a "$OUT/ladder.log"
    done
  done
}

stage_render() {
  cd "$ROOT"
  for ply in "$OUT"/ply/*.ply; do
    [ -s "$ply" ] || continue
    name="$(basename "$ply" .ply)"
    log "--- render $name ---"
    #: make_m360_archive hard-links the PLY (M19 cost an afternoon); drop the entry first.
    rm -rf "${ARCH:?}/output/${name}"
    "$PY" experiments/make_m360_archive.py --scene-dir "$COLMAP/$(echo "$name" | cut -d_ -f1)" \
      --ply "$ply" --archive "$ARCH" --name "$name" 2>&1 | tail -1
    bash experiments/probe_render.sh "$name" "$FACTOR" 2>&1 | tail -2 | tee -a "$OUT/render.log"
  done
}

stage_timing() {
  cd "$ROOT"
  log "=== decode timing / peak RSS ==="
  for scene in ${SCENES//,/ }; do
    for spec in ${SPECS//,/ }; do
      for suf in "" "_p"; do
        f="$OUT/models/${scene}_${spec}${suf}.gs1"
        [ -s "$f" ] || continue
        /usr/bin/time -f "$(basename "$f" .gs1)  wall %e s  peak RSS %M KB" \
          "$PY" experiments/m19_codec.py --to-ply "$f" --out "$OUT/tmp.ply" 2>&1 | tail -2
      done
    done
  done
}

case "${1:-all}" in
  deps)   bash "$ROOT/experiments/run_m17.sh" deps ;;
  data)   for s in ${SCENES//,/ }; do SCENE="$s" bash "$ROOT/experiments/run_m17.sh" data; done ;;
  base)   for s in ${SCENES//,/ }; do SCENE="$s" bash "$ROOT/experiments/run_m17.sh" base; done ;;
  encode) stage_encode ;;
  ladder) stage_ladder ;;
  render) stage_render ;;
  timing) stage_timing ;;
  all)    stage_encode; stage_ladder; stage_render; stage_timing ;;
  *) echo "use deps|data|base|encode|ladder|render|timing|all" >&2; exit 2 ;;
esac
