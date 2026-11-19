import io

p = "experiments/m19_codec.py"
s = io.open(p, encoding="utf-8").read()

old_sig = 'def verify_roundtrip(splats, spec_name: str, level: int = 12) -> dict:'
new_sig = ('def verify_roundtrip(splats, spec_name: str, level: int = 12,\n'
           '                     sh_layout: str = "bits") -> dict:')
assert old_sig in s
s = s.replace(old_sig, new_sig, 1)

old = ('    streams, _ = M._encode(spec, geo, sh, deg, None, order)\n'
       '    meta = {"spec": spec_name, "n": int(geo["means"].shape[0]), "sh_degree": deg,\n'
       '            "deg_out": int(spec.out_degree(deg)), "model_bytes_per_prim": 0.0}')
new = ('    streams, _ = M._encode(spec, geo, sh, deg, None, order, sh_layout=sh_layout)\n'
       '    streams["geo_hdr"] = geo_header(geo, spec)\n'
       '    meta = {"spec": spec_name, "n": int(geo["means"].shape[0]), "sh_degree": deg,\n'
       '            "sh_layout": sh_layout,\n'
       '            "deg_out": int(spec.out_degree(deg)), "model_bytes_per_prim": 0.0}')
assert old in s, "verify body"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("verify_roundtrip now takes sh_layout")
