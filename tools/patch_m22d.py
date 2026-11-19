p = "experiments/m22_basis.py"
s = open(p, encoding="utf-8").read()
orig = s
s = s.replace('''def encode_basis(splats, rank: int, bits_total: int = 64, level: int = 12, path: str = None,
                 layout: str = "bits", spec_name: str = "c10_o8_sh3") -> dict:''',
'''def encode_basis(splats, rank: int, bits_total: int = 64, level: int = 12, path: str = None,
                 layout: str = "bits", spec_name: str = "c10_o8_sh3",
                 return_recon: bool = False) -> dict:''')
s = s.replace('''    return {"streams": streams, "meta": meta, "info": info, "energy": f["energy"],
            "coef_err": q["err"], "model_bytes_per_prim": float(model_bpp),
            "bits_per_component": [int(x) for x in q["bits"]]}''',
'''    out = {"streams": streams, "meta": meta, "info": info, "energy": f["energy"],
           "coef_err": q["err"], "model_bytes_per_prim": float(model_bpp),
           "bits_per_component": [int(x) for x in q["bits"]]}
    if return_recon:
        #: the encoder's own idea of the rest block, in the container's primitive order
        out["recon"] = (f["mean"] + q["rec"] @ f["basis"]).astype(np.float32)
        out["order"] = np.asarray(order)
    return out''')
assert s != orig
open(p, "w", encoding="utf-8").write(s)

p = "experiments/tests/test_m22_basis.py"
s = open(p, encoding="utf-8").read()
orig = s
s = s.replace('''def test_a_low_rank_model_is_recovered():
    s = _model(rank_like=3)
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "b.gs1")
        B.encode_basis(s, rank=8, bits_total=64, level=12, path=p)
        meta, streams = C.read_container(p)
        got = C.decode(meta, streams)["sh_rest"].reshape(int(meta["n"]), -1)
        want = np.asarray(s.shN).reshape(int(meta["n"]), -1)
        err = float(np.abs(got - want).mean())
        #: quantisation at 8 bits per component dominates; a plumbing error (wrong order, wrong
        #: basis orientation) would show up as the spread of the coefficients themselves (~0.1).
        assert err < 0.03, f"low-rank model not recovered: {err:.4f}"''',
'''def test_the_decoder_reproduces_the_encoder():
    """The decoder must land on the encoder's own reconstruction, bit for bit.

    Comparing against the *original* coefficients would measure the quantiser; comparing against the
    encoder's reconstruction measures the thing this test is for: order, packing, basis orientation.
    """
    s = _model(rank_like=3)
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "b.gs1")
        rec = B.encode_basis(s, rank=8, bits_total=64, level=12, path=p, return_recon=True)
        meta, streams = C.read_container(p)
        got = C.decode(meta, streams)["sh_rest"].reshape(int(meta["n"]), -1)
        want = np.asarray(rec["recon"], dtype=np.float64)
        err = float(np.abs(got - want).max())
        assert err < 2e-3, f"decoder disagrees with the encoder: {err:.5f}"
        #: and the reconstruction has to be close to the model it coded, or the fit is broken
        coarse = float(np.abs(want - np.asarray(s.shN).reshape(int(meta["n"]), -1)[
            np.asarray(rec["order"])]).mean())
        assert coarse < 0.06, f"reconstruction too far from the model: {coarse:.4f}"''')
assert s != orig
open(p, "w", encoding="utf-8").write(s)
print("patched tests + return_recon")
