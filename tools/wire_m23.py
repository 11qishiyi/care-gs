p = "experiments/m19_codec.py"
s = open(p, encoding="utf-8").read()
orig = s

# container order: the delta streams travel next to the streams they replace
s = s.replace('''         "sh_basis", "sh_basis_mean", "sh_basis_comp", "sh_coef_bits", "sh_coef_ref", "sh_coef_lvl", "sh_coef",''',
'''         "sh_basis", "sh_basis_mean", "sh_basis_comp", "sh_coef_bits", "sh_coef_ref", "sh_coef_lvl", "sh_coef",
         #: M23: geometry recoded as Morton-order deltas (lossless: the levels come back identical).
         "cluster_off_d", "geo_scales_d", "geo_opacities_d",''')

# decoder entry: restore the packed geometry streams before the ordinary path reads them
s = s.replace('''    import qfp_rd as Q

    spec = Q.parse_spec(meta["spec"])
    n = int(meta["n"])
    deg_out = int(meta["deg_out"])''',
'''    import qfp_rd as Q

    if meta.get("geo_delta"):
        #: M23 -- the file stored these streams as deltas; put the packed form back so there is
        #: still exactly one decoder for what follows.
        import m23_pred
        streams = m23_pred.restore(meta, streams)
    spec = Q.parse_spec(meta["spec"])
    n = int(meta["n"])
    deg_out = int(meta["deg_out"])''')

assert s != orig
open(p, "w", encoding="utf-8").write(s)
print("patched m19_codec")

p = "experiments/m22_basis.py"
s = open(p, encoding="utf-8").read()
orig = s
s = s.replace('''def encode_basis(splats, rank: int, bits_total: int = 64, level: int = 12, path: str = None,
                 layout: str = "bits", spec_name: str = "c10_o8_sh3",
                 return_recon: bool = False) -> dict:''',
'''def encode_basis(splats, rank: int, bits_total: int = 64, level: int = 12, path: str = None,
                 layout: str = "bits", spec_name: str = "c10_o8_sh3",
                 return_recon: bool = False, geo_delta: bool = False) -> dict:''')
s = s.replace('''    streams["geo_hdr"] = C.geo_header(geo, spec)
    info = C.write_container(path, streams, meta, level) if path else None''',
'''    streams["geo_hdr"] = C.geo_header(geo, spec)
    if geo_delta:
        #: M23: recode the geometry streams as Morton deltas.  The decoded levels are identical.
        import m23_pred
        meta, streams = m23_pred.apply(meta, streams)
    info = C.write_container(path, streams, meta, level) if path else None''')
s = s.replace('''def encode_all(ply: str, plans, out: str, level: int = 12, layouts=("bits",)) -> list:''',
'''def encode_all(ply: str, plans, out: str, level: int = 12, layouts=("bits",),
               spec_name: str = "c10_o8_sh3", geo_delta: bool = False, tag_prefix: str = "") -> list:''')
s = s.replace('''            tag = f"r{rank:02d}_b{bits:03d}_{layout}"''',
'''            tag = f"{tag_prefix}r{rank:02d}_b{bits:03d}_{layout}"''')
s = s.replace('''            rec = encode_basis(mod, rank=rank, bits_total=bits, level=level, path=p, layout=layout)''',
'''            rec = encode_basis(mod, rank=rank, bits_total=bits, level=level, path=p, layout=layout,
                               spec_name=spec_name, geo_delta=geo_delta)''')
s = s.replace('''    ap.add_argument("--layouts", default="bits")''',
'''    ap.add_argument("--layouts", default="bits")
    ap.add_argument("--spec", default="c10_o8_sh3")
    ap.add_argument("--geo-delta", action="store_true")
    ap.add_argument("--tag", default="")''')
s = s.replace('''        rows = encode_all(a.encode, plans, a.out,
                          layouts=tuple(x for x in a.layouts.split(",") if x.strip()))''',
'''        rows = encode_all(a.encode, plans, a.out, spec_name=a.spec, geo_delta=a.geo_delta,
                          tag_prefix=a.tag,
                          layouts=tuple(x for x in a.layouts.split(",") if x.strip()))''')
assert s != orig
open(p, "w", encoding="utf-8").write(s)
print("patched m22_basis")
