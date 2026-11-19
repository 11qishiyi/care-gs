"""Side information is a per-*file* quantity: charge it only when the caller says how
many primitives the file holds.

Without ``n_stored`` the model returns the payload rate (what every published RD number
in this series quotes, and what the quantiser arithmetic selftests pin).  With
``n_stored`` it returns the exact file rate, headers included, which is what the M19
container needs.
"""
import io

for path in ("experiments/qfp_rd.py", "experiments/m1_analyse.py"):
    s = io.open(path, encoding="utf-8").read()
    old = "    b_side /= float(n_stored or VQ_NOMINAL_PRIMS)\n"
    assert old in s, path
    new = ("    # per-file, not per-primitive: without a primitive count the model quotes\n"
           "    # the payload rate; with one it quotes the file rate, headers included.\n"
           "    b_side = 0.0 if n_stored is None else b_side / float(n_stored)\n")
    s = s.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8", newline="\n").write(s)
    print(path, "patched")

t = "experiments/tests/test_m15_pack.py"
s = io.open(t, encoding="utf-8").read()
s = s.replace("""    # the payload is 27.96875 B; a shipped file additionally carries 72 B of one-off
    # side information (geo_hdr 64 + sh_hdr 8), i.e. 72/n per primitive
    n = 4_000_000
    assert abs(spec.bytes_per_prim(3, n_stored=n) - (27.96875 + 72.0 / n)) < 1e-12
    assert abs(spec.rate_vs_fp32(3, n_stored=n) - 236.0 / (27.96875 + 72.0 / n)) < 1e-9""",
              """    # the payload is 27.96875 B; a shipped file additionally carries 40 B of one-off
    # side information (geo_hdr 32 for scales+opacities, sh_hdr 8), i.e. 40/n per primitive
    n = 4_000_000
    assert abs(spec.bytes_per_prim(3, n_stored=n) - (27.96875 + 40.0 / n)) < 1e-12
    assert abs(spec.rate_vs_fp32(3, n_stored=n) - 236.0 / (27.96875 + 40.0 / n)) < 1e-9""")
io.open(t, "w", encoding="utf-8", newline="\n").write(s)
print("test updated:", "40.0 / n" in s)
