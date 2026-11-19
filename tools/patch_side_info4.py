"""Charge the *actual* per-file side information in both byte-model implementations.

``geo_hdr`` is 8 B per coded component of the grid-coded attributes (scales 3, quats 4
-- or 0 for smallest-three, which carries its own selector stream -- opacities 1), and
``sh_hdr`` is 8 B for the scalar SH ladder only.  Clean is therefore 0 B, a 3-bit SH
row is 72 B, a vector-quantised row is 64 B.  Measured against the encoder, then
mirrored into ``m1_analyse``.
"""
import io

FORMULA_Q = """    # one-off per-file side information, charged per stored primitive: 8 B per coded
    # component of every grid-coded geometry attribute, plus the SH ladder's two scales
    b_side = 0.0
    for _a, _c in (("scales", 3), ("quats", 4), ("opacities", 1)):
        if int(geo.get(_a, FP32_BITS)) >= FP32_BITS:
            continue
        if _a == "quats" and quat_st3 is not None:
            continue                      # smallest-three carries a selector stream instead
        b_side += 8.0 * _c
    _ladder = (sh_pq is None and sh_msc is None and sh_rvq is None
               and sh_vq_bits is None and sh_bits < FP32_BITS)
    if _ladder:
        b_side += SH_HDR_BYTES
    b_side /= float(n_stored or VQ_NOMINAL_PRIMS)
"""

OLD_Q = """    # one-off per-file side information, charged per stored primitive
    scalar_ladder = (sh_pq is None and sh_msc is None and sh_rvq is None
                     and sh_vq_bits is None and sh_bits < FP32_BITS)
    b_side = GEO_HEADER_BYTES + (SH_HDR_BYTES if scalar_ladder else 0.0)
    b_side /= float(n_stored or VQ_NOMINAL_PRIMS)
"""

OLD_A = """    # one-off per-file side information, charged per stored primitive (mirrors qfp_rd)
    scalar_ladder = (sh_pq is None and sh_msc is None and sh_rvq is None
                     and sh_vq_bits is None and sh_bits < 32)
    b_side = GEO_HEADER_BYTES + (SH_HDR_BYTES if scalar_ladder else 0.0)
    b_side /= float(n_stored or VQ_NOMINAL_PRIMS)
"""

for path, old in (("experiments/qfp_rd.py", OLD_Q), ("experiments/m1_analyse.py", OLD_A)):
    s = io.open(path, encoding="utf-8").read()
    assert old in s, path
    s = s.replace(old, FORMULA_Q, 1)
    s = s.replace("GEO_HEADER_BYTES = 64.0\n", "#: 8 B per coded component of a grid-coded attribute\n")
    io.open(path, "w", encoding="utf-8", newline="\n").write(s)
    print(path, "patched")
