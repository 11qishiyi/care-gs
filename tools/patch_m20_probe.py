import io

p = "experiments/m20_probe.py"
s = io.open(p, encoding="utf-8").read()

# 1. codes_published_sh_parts already returns unsigned codes in 0..2**bits-1
s = s.replace("""            codes, scale = M.codes_published_sh_parts(rest, bits)
            qmax = (1 << (bits - 1)) - 1
            codes = (codes.astype(np.int64) + (qmax + 1)).astype(np.uint8)   # 0..2**bits-1""",
              """            codes, scale = M.codes_published_sh_parts(rest, bits)
            codes = codes.astype(np.uint8)          # already 0 .. 2**bits - 1""")

# 2. V4: pack the plane itself, not its bytes
s = s.replace("""            variants["V4 plane x coef frames"] = sum(
                _z(np.packbits((((codes[:, c] >> b) & 1).astype(np.uint8)).tobytes()).tobytes(),
                   args.level) for c in range(ncol) for b in range(bits))""",
              """            variants["V4 plane x coef frames"] = sum(
                _z(np.packbits(((codes[:, c] >> b) & 1).astype(np.uint8)).tobytes(),
                   args.level) for c in range(ncol) for b in range(bits))""")

# 3. bytes per primitive, not bits
s = s.replace('f"{base * 8 / n:6.2f} B/prim"', 'f"{base / n:6.2f} B/prim"')
s = s.replace('f"{v / 1e6:8.2f} MB {v * 8 / n:6.2f} B/prim "', 'f"{v / 1e6:8.2f} MB {v / n:6.2f} B/prim "')
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched:", s.count("base / n"), s.count("v / n"), "double-offset removed:", "qmax + 1" not in s.split("def main")[1])
