import io

p = "experiments/tests/test_m19_codec.py"
s = io.open(p, encoding="utf-8").read()
old = '    spec = M.Q.parse_spec("c10_o8_sh3")'
new = '    import qfp_rd as Q2\n    spec = Q2.parse_spec("c10_o8_sh3")'
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
