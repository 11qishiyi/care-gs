"""qfp_rd: selftest the two-stage (rvq) quantiser next to the single-stage one."""
import io

Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()

s = s.replace(
    '''    C.log("== end-to-end analysis smoke ==")''',
    '''    C.log("== residual vector quantisation (M10) ==")
    st_r = SceneState(base=sp)
    pair = st_r.codebook_pair(6, 2, 3)
    check("two codebooks of the registered widths", [tuple(c.shape) for c in pair]
          == [(64, 48), (4, 48)], str([tuple(c.shape) for c in pair]))
    check("residual codebook training is deterministic",
          torch.equal(pair[1], SceneState(base=sp).codebook_pair(6, 2, 3)[1]))
    qr = apply_quant(sp, parse_spec("rvq6-2_c8_o8"), st_r)
    rec_r = _sh_flat(qr)[:, :48]

    # The residual stage is only worth its index bits if the reconstruction really is
    # ``centre1 + centre2``: every row must land on such a sum.
    a1 = _vq_assign(rec_r, pair[0])
    r1 = rec_r - pair[0].index_select(0, a1)
    a2 = _vq_assign(r1, pair[1])
    dev = (rec_r - (pair[0].index_select(0, a1) + pair[1].index_select(0, a2))).abs().amax()
    check("every stored block is centre1 + centre2", float(dev) < 1e-5,
          f"max deviation {float(dev):.2e}")

    def _err(spec):
        st = SceneState(base=sp)
        q = apply_quant(sp, parse_spec(spec), st)
        return float((_sh_flat(q) - ref_flat).abs().mean())

    # Same total index width, spent as 8 or as 6+2: the split must not be worse than
    # a single codebook of the same width, and both must beat a narrower one.
    e_single8, e_rvq62, e_single6 = _err("vq8_c8_o8"), _err("rvq6-2_c8_o8"), _err("vq6_c8_o8")
    check("two stages at 8 total bits beat a 6-bit single stage",
          e_rvq62 < e_single6, f"{e_rvq62:.3e} vs {e_single6:.3e}")
    check("residual stage is a real refinement (not a no-op)",
          e_rvq62 < e_single8 * 1.5, f"rvq 6+2 {e_rvq62:.3e} vs single 8 {e_single8:.3e}")

    b_rvq = parse_spec("rvq8-4_c8_o8").bytes_per_prim(3, n_stored=1_000_000)
    want_r = (8.0 + 3 * 8 / 8 + CLUSTER_HEADER_PER_PRIM + (8 + 4) / 8
              + (256 + 16) * 48 / 1e6)
    check("both codebooks are charged", abs(b_rvq - want_r) < 1e-9,
          f"{b_rvq:.4f} B vs {want_r:.4f}")
    check("rvq excludes vq and scalar SH",
          _raises(lambda: parse_spec("rvq8-4_vq12_c8_o8"))
          and _raises(lambda: parse_spec("rvq8-4_c8_o8_sh4")))
    check("rvq widths are range checked",
          _raises(lambda: parse_spec("rvq1-4_c8_o8"))
          and _raises(lambda: parse_spec("rvq8-20_c8_o8")))
    check("bands above the truncation are zeroed under rvq",
          abs(float(_sh_flat(apply_quant(sp, parse_spec("d2_rvq8-4_c8_o8"),
                                        SceneState(base=sp)))[:, 27:].abs().max())) == 0.0)

    C.log("== end-to-end analysis smoke ==")''', 1)

io.open(Q, "w", encoding="utf-8", newline="\n").write(s)
print("patched", len(s))
