import io
Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()

block = '''    # ---- M11: per-primitive mode selection -------------------------------------
    C.log("== mode selection (msc) ==")
    spec_m = parse_spec("msc12-4-a1_c8_o8")
    check("msc parsed", spec_m.sh_msc == {"b_dict": 12, "b_scalar": 4, "alpha": 1}
          and spec_m.means_cluster_bits == 8, str(spec_m.sh_msc))
    check("msc charges the 2-bit flag",
          abs(spec_m.bytes_per_prim(3, 4_000_000)
              - msc_bytes_per_prim(3, 12, 4, (0.0, 1.0, 0.0), 4_000_000)) < 1e-9)
    check("msc excludes vq/rvq/scalar sh",
          _raises(lambda: parse_spec("msc12-4-a1_vq12_c8_o8"))
          and _raises(lambda: parse_spec("msc12-4-a1_c8_o8_sh4")))
    st_m = SceneState(base=sp)
    deg_m = int(sp.sh_degree)
    cols_m = sh_cols(deg_m)
    flat_m = _sh_flat(sp)[:, :cols_m]
    mixes = {}
    for a in (1, 4):
        spx = parse_spec(f"msc12-4-a{a}_c8_o8")
        _, _, _, frac = msc_select(sp, spx, st_m, deg_m)
        mixes[a] = frac
        check(f"msc a{a} mix sums to one", abs(sum(frac) - 1.0) < 1e-6, f"{frac}")
        spq = apply_quant(sp, spx, st_m)
        check(f"msc a{a} records its realised mix",
              spx.msc_frac is not None and abs(sum(spx.msc_frac) - 1.0) < 1e-6,
              str(spx.msc_frac))
        check(f"msc a{a} charges the realised mix",
              abs(spx.bytes_per_prim(deg_m, int(sp.n))
                  - msc_bytes_per_prim(deg_m, 12, 4, spx.msc_frac, int(sp.n))) < 1e-9)
        rec = _sh_flat(spq)[:, :cols_m]
        err = float(((flat_m - rec) ** 2).sum(1).mean())
        check(f"msc a{a} beats zeroing everything", err < float((flat_m ** 2).sum(1).mean()),
              f"{err:.4e}")
    check("a dearer byte zeroes more primitives",
          mixes[4][0] >= mixes[1][0], f"{mixes[1]} vs {mixes[4]}")
    check("bands above the truncation are zeroed under msc",
          abs(float(_sh_flat(apply_quant(sp, parse_spec("d2_msc12-4-a1_c8_o8"),
                                         st_m))[:, 27:].abs().max())) == 0.0)

'''
s = s.replace('''    C.log("== end-to-end analysis smoke ==")''', block + '''    C.log("== end-to-end analysis smoke ==")''', 1)
io.open(Q, "w", encoding="utf-8", newline="\n").write(s)
print("ok", len(s))
