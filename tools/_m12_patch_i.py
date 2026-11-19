"""Let run_m12.sh's bytes stage take an explicit SPECS list (measured subset only)."""
import io

P = r"D:\3dsg_1\experiments\run_m12.sh"
s = io.open(P, encoding="utf-8").read()
old = '''  specs="$("$PY" -c 'import qfp_rd as Q; print(Q.M12_VARIANTS)')"'''
new = '''  # Only the variants a criterion actually reads need measured bytes.  ``vq16``
  # (65536 centres over 5.26M points) and the fp32-SH prune anchors dominate the wall
  # clock -- ``clean`` alone is 1.24 GB through zstd-12 -- so SPECS exists to measure
  # just the PQ family and its matched single-codebook anchor.
  specs="${SPECS:-}"
  if [ -z "$specs" ]; then
    specs="$("$PY" -c 'import qfp_rd as Q; print(Q.M12_VARIANTS)')"
  fi'''
assert old in s
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("ok")
