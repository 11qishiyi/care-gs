import io
Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()
anchor = '''def rvq_codebook_bytes(bits1: int, bits2: int, cols: int) -> float:'''
assert anchor in s
block = '''def pq_codebook_bytes(m: int, b: int, cols: int) -> int:
    """One codebook per sub-vector, 8-bit centres: ``2**b`` centres over ``cols`` dims."""
    if cols % m:
        raise ValueError(f"{cols} coefficients do not split into {m} groups")
    return int((1 << b) * cols)


def pq_bytes_per_prim(m: int, b: int, n_stored: int, cols: int) -> float:
    """``m`` codes of ``b`` bits each, plus the amortised codebooks."""
    return float(m * b) / 8.0 + pq_codebook_bytes(m, b, cols) / float(
        n_stored or VQ_NOMINAL_PRIMS)


'''
io.open(Q, "w", encoding="utf-8", newline="\n").write(s.replace(anchor, block + anchor, 1))
print("inserted")
