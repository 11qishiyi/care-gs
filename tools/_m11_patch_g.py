import io
Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()

s = s.replace('''    check("msc charges the 2-bit flag",
          abs(spec_m.bytes_per_prim(3, _n)
              - (_nonsh(spec_m, 3) + msc_bytes_per_prim(3, 12, 4, (0.0, 1.0, 0.0), _n))) < 1e-9,
          f"{spec_m.bytes_per_prim(3, _n):.4f}")''',
'''    _peak = parse_spec("c8_o8_sh32").bytes_per_prim(3, _n)
    check("msc charges the 2-bit flag",
          abs((spec_m.bytes_per_prim(3, _n) - (_peak - _cols4))
              - msc_bytes_per_prim(3, 12, 4, (0.0, 1.0, 0.0), _n)) < 1e-9,
          f"{spec_m.bytes_per_prim(3, _n):.4f}")''', 1)

s = s.replace('''        _n2 = int(sp.n)
        _c4 = sh_cols(deg_m) * FP32_BITS / 8.0
        check(f"msc a{a} charges the realised mix",
              abs(spx.bytes_per_prim(deg_m, _n2)
                  - (spx.bytes_per_prim(deg_m, _n2) - _c4
                     + msc_bytes_per_prim(deg_m, 12, 4, spx.msc_frac, _n2))) < 1e-9,
              f"{spx.bytes_per_prim(deg_m, _n2):.4f} B")''',
'''        _n2 = int(sp.n)
        _c2 = sh_cols(deg_m) * FP32_BITS / 8.0
        _peak2 = parse_spec("c8_o8_sh32").bytes_per_prim(deg_m, _n2)
        check(f"msc a{a} charges the realised mix",
              abs((spx.bytes_per_prim(deg_m, _n2) - (_peak2 - _c2))
                  - msc_bytes_per_prim(deg_m, 12, 4, spx.msc_frac, _n2)) < 1e-9,
              f"{spx.bytes_per_prim(deg_m, _n2):.4f} B")''', 1)

io.open(Q, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
