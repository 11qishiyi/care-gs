"""qfp_rd stage B: PQ codebooks, the quantiser, and the M12 grid."""
import io

Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()

s = s.replace('''def base_degree(sp) -> int:''',
'''def build_codebook_pq(sp, m: int, b: int, deg_out: int, seed: int = 0, iters: int = 15):
    """One codebook per interleaved sub-vector of the SH block."""
    import torch  # noqa: F401  (kept for symmetry with the other builders)
    cols = sh_cols(int(deg_out))
    if cols % m:
        raise ValueError(f"{cols} coefficients do not split into {m} groups")
    flat = _sh_flat(sp)[:, :cols].contiguous()
    books = []
    for g in range(m):
        sub = flat[:, g::m].contiguous()
        books.append(quantise_codebook(_kmeans(sub, 1 << b, seed=seed + g, iters=iters), 8))
    return books


def quantize_pq(sp, books, m: int, deg_out: int):
    """Replace each sub-vector by its nearest centre."""
    cols = sh_cols(int(deg_out))
    flat = _sh_flat(sp)
    out = flat.clone()
    for g, C in enumerate(books):
        sub = flat[:, g::m].contiguous()
        idx = _vq_assign(sub, C)
        out[:, g::m] = C.index_select(0, idx)
    if cols < int(out.shape[1]):
        out[:, cols:] = 0.0
    _set_sh_flat(sp, out)
    return sp


def base_degree(sp) -> int:''', 1)

s = s.replace('''    out = sp.clone()
    if spec.sh_msc is not None:''',
'''    out = sp.clone()
    if spec.sh_pq is not None:
        if state is None:
            raise RuntimeError("product quantisation needs the scene state (codebooks)")
        m_pq, b_pq = int(spec.sh_pq[0]), int(spec.sh_pq[1])
        deg_out = spec.out_degree(int(base_degree(sp)))
        quantize_pq(out, state.codebook_pq(m_pq, b_pq, deg_out), m_pq, deg_out)
    elif spec.sh_msc is not None:''', 1)

# SceneState cache
s = s.replace('''    def codebook(self, bits: int, deg_out: int):''',
'''    def codebook_pq(self, m: int, b: int, deg_out: int):
        key = ("pq", int(m), int(b), int(deg_out))
        if key not in self.cache:
            self.cache[key] = build_codebook_pq(self.base, int(m), int(b), int(deg_out))
        return self.cache[key]

    def codebook(self, bits: int, deg_out: int):''', 1)

# variants
s = s.replace('''#: M11 grid: per-primitive mode selection.''',
'''#: M12 grid: product quantisation.  M9-M11 pushed one 48-d codebook as far as it goes
#: (0.3-2.4 pp at 19x) and neither a second stage nor per-primitive scheduling moved it.
#: PQ changes the codebook's *shape*: interleaved sub-vectors, one small codebook each.
M12_VARIANTS = ",".join([
    "clean",
    # single-codebook anchors at the same bytes
    "vq12_c8_o8", "vq14_c8_o8", "vq16_c8_o8",
    # scalar anchors
    "c8_o8_sh2", "c8_o8_sh3",
    # prune anchors (the family every coverage claim is measured against)
    "p50", "p30", "p20",
    # PQ at 1.0-1.5 B: matched with vq12/14
    "pq2-4_c8_o8", "pq3-4_c8_o8", "pq2-6_c8_o8",
    # PQ at 2.0-3.0 B: matched with vq16
    "pq4-4_c8_o8", "pq3-6_c8_o8", "pq6-4_c8_o8", "pq8-3_c8_o8",
    # the expensive end, where a finer partition should pay
    "pq4-6_c8_o8", "pq4-8_c8_o8",
])


#: M11 grid: per-primitive mode selection.''', 1)

s = s.replace('''                                                  M9_VARIANTS, M10_VARIANTS,
                                                  M11_VARIANTS):''',
'''                                                  M9_VARIANTS, M10_VARIANTS,
                                                  M11_VARIANTS, M12_VARIANTS):''', 1)
s = s.replace('''                "m10": M10_VARIANTS, "m11": M11_VARIANTS}[preset]''',
'''                "m10": M10_VARIANTS, "m11": M11_VARIANTS,
                "m12": M12_VARIANTS}[preset]''', 1)
s = s.replace('''choices=["custom", "m1", "m2", "m3", "m7", "m8", "m9", "m10", "m11"],''',
'''choices=["custom", "m1", "m2", "m3", "m7", "m8", "m9", "m10", "m11", "m12"],''', 1)

io.open(Q, "w", encoding="utf-8", newline="\n").write(s)
print("stage B", len(s))
