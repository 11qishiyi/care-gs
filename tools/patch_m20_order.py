"""The container dropped ``geo_means``: the encoder wrote it, ``ORDER`` did not list it.

Third instance of the M19 class (a stream exists but the format does not carry it), and this one
makes every grid-coded-position variant undecodable -- the whole M16 shelf.  The fix is one name in
``ORDER``; the real fix is a test that walks the encoder's streams instead of a fixed list.
"""
import io

p = "experiments/m19_codec.py"
s = io.open(p, encoding="utf-8").read()
old = 'ORDER = ("geo_hdr", "cluster_hdr", "cluster_off",'
new = 'ORDER = ("geo_hdr", "geo_means", "cluster_hdr", "cluster_off",'
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
line = [ln for ln in s.splitlines() if ln.startswith("ORDER")][0]
print(line)
