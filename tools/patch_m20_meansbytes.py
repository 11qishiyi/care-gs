"""Charge the gridded-position header in both byte models, mirroring the encoder.

``m16_o8_sh4``-style variants grid-code the positions, so their ``geo_hdr`` is 88 B (24 B of
min/step for x,y,z plus 64 B for the rest) rather than 64 B.  The two models have to say the
same thing or ``m1_check_bytes`` drifts by 24 B per file.
"""
import io

OLD = """    b_side = 0.0
    for _a, _c in (("scales", 3), ("quats", 4), ("opacities", 1)):"""
NEW = """    b_side = 0.0
    _head = (("means", 3), ("scales", 3), ("quats", 4), ("opacities", 1))
    for _a, _c in _head:
        if _a == "means" and means_cbits is not None:
            continue                      # cluster coding carries its own per-block origin/step"""
for path in ("experiments/qfp_rd.py", "experiments/m1_analyse.py"):
    s = io.open(path, encoding="utf-8").read()
    assert OLD in s, path
    s = s.replace(OLD, NEW, 1)
    io.open(path, "w", encoding="utf-8", newline="\n").write(s)
    print(path, "patched")

t = io.open("experiments/m19_codec.py", encoding="utf-8").read()
print("codec DIMS has means:", '"means": 3' in t)
