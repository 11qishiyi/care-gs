import io

p = "experiments/m27_anchor.py"
s = io.open(p, encoding="utf-8").read()

anchor = "# ----------------------------------------------------------------------------- encoding\n"
helpers = '''def _quant(v: np.ndarray, bits: int):
    v = np.asarray(v, dtype=np.float32)
    mn = v.min(axis=0)
    step = (v.max(axis=0) - mn) / max(1, (1 << bits) - 1)
    step = np.where(step > 0, step, np.float32(1.0)).astype(np.float32)
    codes = np.clip(np.round((v - mn) / step), 0, (1 << bits) - 1).astype(np.int64)
    return codes, mn.astype(np.float32), step


def _deg_from_cols(cols: int) -> int:
    k = cols // 3
    return int(round((k + 1) ** 0.5 - 1))


''' + anchor
assert anchor in s
s = s.replace(anchor, helpers, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("restored helpers")
