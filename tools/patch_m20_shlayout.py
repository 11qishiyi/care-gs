import io

p = "experiments/m4_bytes.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("_sh_stream(codes, sh_bits, layout)", "_sh_stream(codes, sh_bits, sh_layout)")
s = s.replace('per_prim += (cols * sh_bits / 8.0 if layout == "bits" else cols * 1.0)',
              'per_prim += (cols * sh_bits / 8.0 if sh_layout == "bits" else cols * 1.0)')
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("layout refs:", s.count("sh_layout"))
