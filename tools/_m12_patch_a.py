"""qfp_rd: product quantisation of the SH block (M12).

M9-M11 showed that one 48-dimensional codebook stalls at 0.3-2.4 pp around 19x, and that
neither a second stage nor per-primitive scheduling moves it.  The remaining lever is the
codebook's *shape*: split the block into ``m`` sub-vectors and give each its own codebook,
which is the standard remedy when the marginal structure is strong and the joint structure
is not.  Interleaved groups (``j % m``) spread the DC band and the two channels across the
sub-vectors instead of cutting the block into contiguous runs.
"""
import io

Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()

# ---- byte model ------------------------------------------------------------
s = s.replace('''def rvq_codebook_bytes(b1: int, b2: int, cols: int) -> int:''',
'''def pq_codebook_bytes(m: int, b: int, cols: int) -> int:
    """One codebook per sub-vector, 8-bit centres: ``2**b`` centres over ``cols`` dims."""
    if cols % m:
        raise ValueError(f"{cols} coefficients do not split into {m} groups")
    return int((1 << b) * cols)


def pq_bytes_per_prim(m: int, b: int, n_stored: int, cols: int) -> float:
    """``m`` codes of ``b`` bits each, plus the amortised codebooks."""
    return float(m * b) / 8.0 + pq_codebook_bytes(m, b, cols) / float(
        n_stored or VQ_NOMINAL_PRIMS)


def rvq_codebook_bytes(b1: int, b2: int, cols: int) -> int:''', 1)

s = s.replace('''    sh_rvq_bits: tuple = None
    #: per-primitive mode selection''',
'''    sh_rvq_bits: tuple = None
    #: product quantisation ``(groups, bits)`` of the SH block
    sh_pq: tuple = None
    #: per-primitive mode selection''', 1)

s = s.replace('''        is_quant = (self.sh_bits < FP32_BITS or self.sh_vq_bits is not None
                    or self.sh_rvq_bits is not None or self.sh_msc is not None''',
'''        is_quant = (self.sh_bits < FP32_BITS or self.sh_vq_bits is not None
                    or self.sh_rvq_bits is not None or self.sh_msc is not None
                    or self.sh_pq is not None''', 1)

s = s.replace('''    if sh_msc is not None:
        b_sh = msc_bytes_per_prim(sh_degree, int(sh_msc["b_dict"]),''',
'''    if sh_pq is not None:
        m_pq, b_pq = int(sh_pq[0]), int(sh_pq[1])
        b_sh = pq_bytes_per_prim(m_pq, b_pq, n_stored, cols)
    elif sh_msc is not None:
        b_sh = msc_bytes_per_prim(sh_degree, int(sh_msc["b_dict"]),''', 1)

s = s.replace('''                              sh_rvq=self.sh_rvq_bits,''',
'''                              sh_rvq=self.sh_rvq_bits, sh_pq=self.sh_pq,''', 1)

s = s.replace('''        if self.sh_msc is not None:
            cols = sh_cols(self.out_degree(sh_degree))''',
'''        if self.sh_pq is not None:
            cols = sh_cols(self.out_degree(sh_degree))
            return pq_codebook_bytes(int(self.sh_pq[0]), int(self.sh_pq[1]), cols)
        if self.sh_msc is not None:
            cols = sh_cols(self.out_degree(sh_degree))''', 1)

# ---- parser ----------------------------------------------------------------
s = s.replace('''            or (_rest.startswith("msc") and "-" in _rest)):''',
'''            or (_rest.startswith("msc") and "-" in _rest)
            or (_rest.startswith("pq") and "-" in _rest)):''', 1)

s = s.replace('''        vq_bits = None
        rvq = None
        msc = None''',
'''        vq_bits = None
        rvq = None
        msc = None
        pq = None''', 1)

s = s.replace('''            elif tok.startswith("msc") and "-" in tok:''',
'''            elif tok.startswith("pq") and "-" in tok:
                p, _, q = tok[2:].partition("-")
                m_pq, b_pq = int(p), int(q)
                if m_pq not in (2, 3, 4, 6, 8) or not 2 <= b_pq <= 8:
                    raise ValueError(f"pq widths out of range in {name}")
                if 48 % m_pq:
                    raise ValueError(f"pq groups must divide 48 in {name}")
                pq = (m_pq, b_pq)
                seen.add("sh")
            elif tok.startswith("msc") and "-" in tok:''', 1)

s = s.replace('''        if msc is not None and (vq_bits is not None or rvq is not None
                                or sh_bits < FP32_BITS):
            raise ValueError(f"msc excludes vq/rvq/sh in {name}")''',
'''        if msc is not None and (vq_bits is not None or rvq is not None
                                or sh_bits < FP32_BITS):
            raise ValueError(f"msc excludes vq/rvq/sh in {name}")
        if pq is not None and (vq_bits is not None or rvq is not None
                               or msc is not None or sh_bits < FP32_BITS):
            raise ValueError(f"pq excludes vq/rvq/msc/sh in {name}")''', 1)

s = s.replace('''                  sh_vq_bits=vq_bits, sh_rvq_bits=rvq, sh_msc=msc)''',
'''                  sh_vq_bits=vq_bits, sh_rvq_bits=rvq, sh_msc=msc, sh_pq=pq)''', 1)

io.open(Q, "w", encoding="utf-8", newline="\n").write(s)
print("stage A", len(s))
