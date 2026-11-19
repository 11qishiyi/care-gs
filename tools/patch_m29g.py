import io

p = "experiments/m29_entropy.py"
s = io.open(p, encoding="utf-8").read()

if "H_prev" in s:
    print("already has H_prev")
    raise SystemExit(0)

old = '''def bucket_bytes('''
new = '''def order1_entropy(codes: np.ndarray, bits: int) -> float:
    """``H(code_t | code_{t-1})`` per component, i.e. what a Markov coder could reach."""
    k = 1 << int(bits)
    flat = codes.reshape(-1).astype(np.int64)
    if flat.size < 2:
        return 0.0
    prev, cur = flat[:-1], flat[1:]
    #: a 2**bits x 2**bits table is 64 k entries at 8 bits and 1 M at 10 bits -- both fine
    tab = np.bincount(prev * k + cur, minlength=k * k).reshape(k, k).astype(np.float64)
    tot = tab.sum(axis=1, keepdims=True)
    p = np.divide(tab, np.maximum(tot, 1.0), out=np.zeros_like(tab), where=tot > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        h = -np.where(p > 0, p * np.log2(np.maximum(p, 1e-300)), 0.0)
    w = tot[:, 0] / max(1.0, tot.sum())
    return float((h.sum(axis=1) * w).sum())


def bucket_bytes('''
assert old in s
s = s.replace(old, new, 1)

old = '''        row = {"stream": name, "dims": dims, "bits": bits, "raw": raw, "zstd": packed,
               "H0": round(h0, 3), "fixed_bits": bits, "n": int(codes.shape[0])}'''
new = '''        row = {"stream": name, "dims": dims, "bits": bits, "raw": raw, "zstd": packed,
               "H0": round(h0, 3), "fixed_bits": bits, "n": int(codes.shape[0]),
               "H1": round(order1_entropy(codes, bits), 3),
               "bits_via_zstd": round(8.0 * packed / max(1, codes.size), 3)}'''
assert old in s
s = s.replace(old, new, 1)

old = '''    print(f"\\n{'stream':>16}{'dims':>5}{'bits':>5}{'zstd MB':>9}{'B/prim':>8}{'H0':>7}"
          f"{'H(pos)':>8}{'pos MB':>8}{'H(scl)':>8}{'scl MB':>8}")'''
new = '''    print(f"\\n{'stream':>16}{'dims':>5}{'bits':>5}{'zstd MB':>9}{'B/prim':>8}{'b/code':>8}"
          f"{'H0':>7}{'H1':>7}{'H(pos)':>8}{'pos MB':>8}{'H(scl)':>8}{'scl MB':>8}")'''
assert old in s
s = s.replace(old, new, 1)

old = '''        print(f"{r['stream']:>16}{r['dims']:>5}{r['bits']:>5}{now/1e6:>9.3f}"
              f"{now/r['n']:>8.3f}{r['H0']:>7.2f}"'''
new = '''        print(f"{r['stream']:>16}{r['dims']:>5}{r['bits']:>5}{now/1e6:>9.3f}"
              f"{now/r['n']:>8.3f}{r['bits_via_zstd']:>8.2f}{r['H0']:>7.2f}{r['H1']:>7.2f}"'''
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("order-1 column added")
