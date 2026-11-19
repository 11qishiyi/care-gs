import io

p = "experiments/m19_codec.py"
s = io.open(p, encoding="utf-8").read()
old = '                 sh_layout: str = "bits") -> dict:'
new = '                 sh_layout: str = "bytes") -> dict:'
assert old in s
s = s.replace(old, new, 1)
# the docstring says bits is the default; keep it truthful
s = s.replace('``sh_layout`` chooses how the SH codes are laid out before zstd (``bits`` = packed',
              '``sh_layout`` chooses how the SH codes are laid out before zstd; ``bytes`` is the default\n    because it is 8 % smaller and a third faster to decode on bicycle and stump (M20), while\n    ``bits`` (packed')
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("default is bytes now:", new in s)
