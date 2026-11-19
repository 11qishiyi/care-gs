"""Fix up the mirrored model: define FP32_BITS / the header constants in m1_analyse,
then check the two implementations agree on all 881 cases.
"""
import io

p = "experiments/m1_analyse.py"
s = io.open(p, encoding="utf-8").read()

if "GEO_HEADER_BYTES = 64.0" not in s:
    anchor = "CLUSTER_HEADER_PER_PRIM = CLUSTER_HEADER_BYTES / float(CLUSTER_SIZE)\n"
    assert anchor in s
    s = s.replace(anchor, anchor
                  + "FP32_BITS = 32\nGEO_HEADER_BYTES = 64.0\nSH_HDR_BYTES = 8.0\n", 1)
s = s.replace("and sh_bits < FP32_BITS)", "and sh_bits < 32)")
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("FP32_BITS defined:", "FP32_BITS = 32" in s)
