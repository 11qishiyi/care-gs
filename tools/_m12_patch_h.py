import io
Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()
old = '''    def codebook(self, vq_bits: int, deg_out: int):
        """SH dictionary for this asset, trained once and reused by every variant."""'''
new = '''    def codebook_pq(self, m: int, b: int, deg_out: int):
        """Product-quantisation codebooks for this asset, trained once and reused."""
        key = ("pq", int(m), int(b), int(deg_out))
        if key not in self.cache:
            self.cache[key] = build_codebook_pq(self.base, int(m), int(b), int(deg_out))
        return self.cache[key]

    def codebook(self, vq_bits: int, deg_out: int):
        """SH dictionary for this asset, trained once and reused by every variant."""'''
assert old in s
io.open(Q, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("ok")
