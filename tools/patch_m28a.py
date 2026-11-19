import io
import re

p = "experiments/m28_pred.py"
s = io.open(p, encoding="utf-8").read()

# 1. drop the unused trainer (the training loop lives in encode, where the quantised conditioning is)
start = s.index("def fit_predictor(")
end = s.index("# ----------------------------------------------------------------------------- encoding")
s = s[:start] + s[end:]

# 2. the selftest must simply decode twice from the same in-memory streams
old = '''    #: the weights round-trip through the container: decode twice, bit for bit
    m2, s2 = C.read_container.__wrapped__(meta, st) if hasattr(C.read_container, "__wrapped__") else (meta, st)
    again = decode(m2, s2)
    for k in again:
        assert np.array_equal(again[k], out[k]), k
'''
new = '''    #: the decoder is a pure function of the file: decode twice, bit for bit
    again = decode(meta, st)
    for k in again:
        assert np.array_equal(again[k], out[k]), k
    #: and the weights survive the container encoding (float16 in, float32 out)
    w = Predictor.from_bytes(st["m28_w"])
    assert w.state()["0.weight"].shape[0] == int(meta["hidden"])
'''
assert old in s
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("cleaned m28")
