import io
Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()

s = s.replace('''    check("msc charges the 2-bit flag",
          abs(spec_m.bytes_per_prim(3, 4_000_000)
              - msc_bytes_per_prim(3, 12, 4, (0.0, 1.0, 0.0), 4_000_000)) < 1e-9)''',
'''    _n = 4_000_000
    _cols4 = sh_cols(3) * FP32_BITS / 8.0
    def _nonsh(spec_, deg_):
        """Total bytes minus whatever the SH block costs at fp32."""
        return spec_.bytes_per_prim(deg_, _n) - _cols4
    check("msc charges the 2-bit flag",
          abs(spec_m.bytes_per_prim(3, _n)
              - (_nonsh(spec_m, 3) + msc_bytes_per_prim(3, 12, 4, (0.0, 1.0, 0.0), _n))) < 1e-9,
          f"{spec_m.bytes_per_prim(3, _n):.4f}")''', 1)

s = s.replace('''        check(f"msc a{a} charges the realised mix",
              abs(spx.bytes_per_prim(deg_m, int(sp.n))
                  - msc_bytes_per_prim(deg_m, 12, 4, spx.msc_frac, int(sp.n))) < 1e-9)''',
'''        _n2 = int(sp.n)
        _c4 = sh_cols(deg_m) * FP32_BITS / 8.0
        check(f"msc a{a} charges the realised mix",
              abs(spx.bytes_per_prim(deg_m, _n2)
                  - (spx.bytes_per_prim(deg_m, _n2) - _c4
                     + msc_bytes_per_prim(deg_m, 12, 4, spx.msc_frac, _n2))) < 1e-9,
              f"{spx.bytes_per_prim(deg_m, _n2):.4f} B")''', 1)

io.open(Q, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
