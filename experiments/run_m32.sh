#!/usr/bin/env bash
# M32: the colour block's residual -- rank or bits?  Iso-byte rank sweep on three scenes.
#
#   bash experiments/run_m32.sh setup|encode|render|all <scene>
#
# Colour cost per primitive is 1 + rank*bits/8 bytes, so every `*_b48` plan costs 7 B/primitive and the
# sweep holds the bytes fixed while trading subspace against precision.  `r16_b64` is the rate control.
set -uo pipefail
ROOT=/workspace/code
export PYTHONPATH="$ROOT/research/code:$ROOT:$ROOT/experiments"
PY=python3
STAGE="${1:?setup|encode|render|all}"
SCENE="${2:-bicycle}"
OUT=/workspace/res/m32
COLMAP=/workspace/data/mip360_colmap
SPEC=gp6-6-6_c8_sh3
PLANS="${PLANS:-16:48,24:48,32:48,8:48,16:64}"
mkdir -p "$OUT"

case "$STAGE" in
  setup)
    SCENES="$SCENE" bash "$ROOT/experiments/m20_setup.sh" 2>&1 | tail -2
    SCENE="$SCENE" bash "$ROOT/experiments/run_m17.sh" data 2>&1 | tail -1
    SCENE="$SCENE" bash "$ROOT/experiments/run_m17.sh" base 2>&1 | tail -2
    ;;
  encode)
    ply=/workspace/data/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply
    #: "16:48,24:48" -> "gp6-6-6_c8_sh3:16:48,gp6-6-6_c8_sh3:24:48"
    SPECPLANS="$SPEC:$(echo "$PLANS" | sed "s/,/,$SPEC:/g")"
    echo "plans: $SPECPLANS"
    t0=$(date +%s)
    $PY -u experiments/m24_alpha.py --ply "$ply" --plans "$SPECPLANS" \
      --out "$OUT/$SCENE" --no-ply --no-legacy > "$OUT/encode_$SCENE.log" 2>&1
    t1=$(date +%s)
    echo "$SCENE encode_wall $((t1-t0)) s" | tee "$OUT/enc_$SCENE.txt"
    ls -l "$OUT/$SCENE"/*.gs1 | awk '{print $5, $9}'
    ;;
  render)
    for f in "$OUT/$SCENE"/*_auto.gs1; do
      tag=$(basename "$f" .gs1)
      ply="$OUT/$SCENE/$tag.ply"
      [ -s "$ply" ] || $PY -u experiments/m19_codec.py --to-ply "$f" --out "$ply" >> "$OUT/decode_$SCENE.log" 2>&1
      $PY experiments/make_m360_archive.py --scene-dir "$COLMAP/$SCENE" --ply "$ply" \
        --archive /workspace/data/m360std --name "m32_${SCENE}_${tag}" 2>&1 | tail -1
      bash "$ROOT/experiments/probe_render.sh" "m32_${SCENE}_${tag}" 1 2>&1 | grep PSNR | tail -1 \
        | tee -a "$OUT/render_$SCENE.log"
      rm -f "$ply"
    done
    ;;
  coef)
    ply=/workspace/data/models/output/$SCENE/point_cloud/iteration_30000/point_cloud.ply
    t0=$(date +%s)
    $PY -u "$ROOT/tools/m32_coef_error.py" --ply "$ply" --plans "$PLANS" \
      --json "$OUT/coef_$SCENE.json" 2>&1 | tee "$OUT/coef_$SCENE.log" | tail -6
    t1=$(date +%s)
    echo "$SCENE coef_wall $((t1-t0)) s" | tee "$OUT/coef_time_$SCENE.txt"
    ;;
  all) bash "$0" setup "$SCENE"; bash "$0" encode "$SCENE"; bash "$0" coef "$SCENE"; bash "$0" render "$SCENE" ;;
  *) echo "use setup|encode|coef|render|all <scene>" >&2; exit 2 ;;
esac
