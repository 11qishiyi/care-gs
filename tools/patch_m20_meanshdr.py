"""Gridded *positions* need their own min/step too.

M19 taught the header to carry the min/step of the grid-coded scales, quaternions and opacities,
but positions were only ever gridded in the older variants (``m16_o8_sh4`` and friends, where
``means_cluster_bits is None``).  Those rows encode ``geo_means`` and the decoder had no way back:
`KeyError: 'means'`.  Same defect class as N28's second item, one attribute further up the file.

Order matters: the header is a flat float32 run, so encoder and decoder iterate the same tuple.
"""
import io

mb = "experiments/m4_bytes.py"
s = io.open(mb, encoding="utf-8").read()
old = '''    out = []
    for attr in ("scales", "quats", "opacities"):
        bits = int(spec.geo.get(attr, FP32_BITS))
        if bits >= FP32_BITS:
            continue'''
new = '''    out = []
    for attr in ("means", "scales", "quats", "opacities"):
        if attr == "means" and getattr(spec, "means_cluster_bits", None) is not None:
            continue                      # cluster coding carries its own per-block origin/step
        bits = int(spec.geo.get(attr, FP32_BITS))
        if bits >= FP32_BITS:
            continue'''
assert old in s
s = s.replace(old, new, 1)
io.open(mb, "w", encoding="utf-8", newline="\n").write(s)

mc = "experiments/m19_codec.py"
t = io.open(mc, encoding="utf-8").read()
old2 = '''    out = {}
    off = 0
    for attr in ("scales", "quats", "opacities"):
        bits = int(spec.geo.get(attr, M.FP32_BITS))
        if bits >= M.FP32_BITS:
            continue'''
new2 = '''    out = {}
    off = 0
    for attr in ("means", "scales", "quats", "opacities"):
        if attr == "means" and getattr(spec, "means_cluster_bits", None) is not None:
            continue
        bits = int(spec.geo.get(attr, M.FP32_BITS))
        if bits >= M.FP32_BITS:
            continue'''
assert old2 in t
t = t.replace(old2, new2, 1)
io.open(mc, "w", encoding="utf-8", newline="\n").write(t)
print("means header wired in both directions")
