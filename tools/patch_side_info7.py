import io

p = "experiments/qfp_rd.py"
s = io.open(p, encoding="utf-8").read()
bad = ("    want = 8.0 + 3 * 8 / 8 + CLUSTER_HEADER_PER_PRIM + 12 / 8 + 4096 * 48 / 1e6\n"
       "            + 64.0 / 1e6            # grid headers, 8 B per coded component\n")
good = ("    want = (8.0 + 3 * 8 / 8 + CLUSTER_HEADER_PER_PRIM + 12 / 8 + 4096 * 48 / 1e6\n"
        "            + 64.0 / 1e6)           # grid headers, 8 B per coded component\n")
assert bad in s
s = s.replace(bad, good, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("fixed")
