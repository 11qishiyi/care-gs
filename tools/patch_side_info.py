"""Add the per-file side information (geo_hdr 64 B, sh_hdr 8 B) to the published
byte model, so ``bytes_per_prim * n`` equals the real stream total exactly.

``m4_bytes`` charges those bytes per primitive (``len(header)/n``); the published
model in ``qfp_rd`` did not, which showed up as a 72 B gap once the headers started
being written.  The share is ~1e-5 B/prim at 6 M primitives, but equality is worth
having: the M19 container compares the two.
"""
import io

qp = "experiments/qfp_rd.py"
s = io.open(qp, encoding="utf-8").read()

anchor = "CLUSTER_HEADER_PER_PRIM = CLUSTER_HEADER_BYTES / float(CLUSTER_SIZE)\n"
assert anchor in s
add = (
    "#: per-file side information: the min/step pair of every mesh-coded geometry\n"
    "#: attribute (float32) and, for the scalar SH ladder, the two block scales.\n"
    "GEO_HEADER_BYTES = 64.0\n"
    "SH_HDR_BYTES = 8.0\n"
)
assert "GEO_HEADER_BYTES" not in s
s = s.replace(anchor, anchor + add, 1)

old = "    return float(b_geo + b_sh)"
assert old in s
new = (
    "    # one-off per-file side information, charged per stored primitive\n"
    "    scalar_ladder = (sh_pq is None and sh_msc is None and sh_rvq is None\n"
    "                     and sh_vq_bits is None and sh_bits < FP32_BITS)\n"
    "    b_side = GEO_HEADER_BYTES + (SH_HDR_BYTES if scalar_ladder else 0.0)\n"
    "    b_side /= float(n_stored or VQ_NOMINAL_PRIMS)\n"
    "    return float(b_geo + b_sh + b_side)"
)
s = s.replace(old, new, 1)
io.open(qp, "w", encoding="utf-8", newline="\n").write(s)
print("qfp_rd patched:", s.count("b_side"), "refs to b_side")
