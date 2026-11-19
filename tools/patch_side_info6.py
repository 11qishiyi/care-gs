"""The two remaining selftest expectations now include the 64 B of grid side
information that a vector-quantised file carries once ``n_stored`` is supplied.
"""
import io

p = "experiments/qfp_rd.py"
s = io.open(p, encoding="utf-8").read()

old1 = "8.0 + 3 * 8 / 8 + CLUSTER_HEADER_PER_PRIM + 12 / 8 + 4096 * 48 / 1e6"
new1 = ("8.0 + 3 * 8 / 8 + CLUSTER_HEADER_PER_PRIM + 12 / 8 + 4096 * 48 / 1e6\n"
        "            + 64.0 / 1e6            # grid headers, 8 B per coded component")
assert old1 in s
s = s.replace(old1, new1, 1)

old2 = "              + (256 + 16) * 48 / 1e6)"
new2 = "              + (256 + 16) * 48 / 1e6 + 64.0 / 1e6)"
assert old2 in s
s = s.replace(old2, new2, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("selftest expectations patched")
