"""Mirror the side-information term into ``m1_analyse.bytes_per_prim``.

``m1_check_bytes`` compares the two implementations of the byte model on 881 cases, so
every term has to exist in both.  After M19 the format writes two one-off headers
(``geo_hdr`` 64 B, ``sh_hdr`` 8 B) that ``m4_bytes`` charges per primitive; the
published model has to carry the same share or the two drift by 72 B per file.
"""
import io

p = "experiments/m1_analyse.py"
s = io.open(p, encoding="utf-8").read()

old = """        b_geo += n * int(geo.get(a, 32)) / 8.0
    return float(b_geo + b_sh)"""
new = """        b_geo += n * int(geo.get(a, 32)) / 8.0
    # one-off per-file side information, charged per stored primitive (mirrors qfp_rd)
    scalar_ladder = (sh_pq is None and sh_msc is None and sh_rvq is None
                     and sh_vq_bits is None and sh_bits < FP32_BITS)
    b_side = GEO_HEADER_BYTES + (SH_HDR_BYTES if scalar_ladder else 0.0)
    b_side /= float(n_stored or VQ_NOMINAL_PRIMS)
    return float(b_geo + b_sh + b_side)"""
assert old in s
s = s.replace(old, new, 1)

anchor = "CLUSTER_HEADER_PER_PRIM = CLUSTER_HEADER_BYTES / float(CLUSTER_SIZE)\n"
if "GEO_HEADER_BYTES" not in s:
    assert anchor in s, "cluster constants not found"
    s = s.replace(anchor, anchor + "GEO_HEADER_BYTES = 64.0\nSH_HDR_BYTES = 8.0\n", 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched:", s.count("b_side"), "GEO_HEADER_BYTES:", "GEO_HEADER_BYTES = 64.0" in s)
