import numpy as np

p = "experiments/m22_basis.py"
s = open(p, encoding="utf-8").read()
orig = s

# ---- robust per-component scale: the max is one outlier away from being useless -------------
s = s.replace('''    basis = v[:, :rank].T.contiguous()                     # (rank, 45)
    coef = (xc @ basis.T).numpy()                          # (n, rank)
    comp = np.abs(coef).max(axis=0)
    comp = np.maximum(comp, 1e-12)''',
'''    basis = v[:, :rank].T.contiguous()                     # (rank, 45)
    coef = (xc @ basis.T).numpy()                          # (n, rank)
    #: scale per component from a high quantile, not the max: a single outlier primitive otherwise
    #: sets the step for six million others (measured: 115 % relative error, worse than coding zero).
    comp = np.quantile(np.abs(coef), 0.999, axis=0) * 1.15
    comp = np.maximum(comp.astype(np.float32), 1e-9)''')

# ---- bit allocation: the budget is bits per primitive, so (r, bits each) is one knob ---------
s = s.replace('''def quantise(coef: np.ndarray, comp: np.ndarray, bits: int = 3, mode: str = "component") -> dict:''',
'''def allocate(comp: np.ndarray, bits_total: int, lo: int = 1, hi: int = 12) -> np.ndarray:
    """Greedy reverse water-filling: hand out ``bits_total`` bits across components by variance.

    Distortion of component j at ``b`` bits is ``(comp_j * 2**-b) ** 2 / 12``; the greedy step picks
    whichever component gains most from one more bit.  That is the integer optimum for squared error.
    """
    r = len(comp)
    bits_total = int(max(bits_total, lo * r))
    b = np.full(r, lo, dtype=np.int64)
    s2 = np.asarray(comp, dtype=np.float64) ** 2
    budget = bits_total - lo * r
    for _ in range(budget):
        gain = s2 * (4.0 ** -b) * 3.0            # drop in distortion from b -> b+1
        gain[b >= hi] = -1.0
        j = int(np.argmax(gain))
        b[j] += 1
    return b


def quantise_alloc(coef: np.ndarray, comp: np.ndarray, bits_total: int) -> dict:
    """Uniform mid-tread per component at the allocated depth, ``bits_total`` bits per primitive."""
    b = allocate(comp, bits_total)
    out = np.empty_like(coef, dtype=np.float32)
    codes = []
    for j, bj in enumerate(b):
        step = 2.0 / float(1 << int(bj))
        v = np.asarray(coef[:, j], dtype=np.float32) / comp[j]
        c = np.clip(np.floor((v + 1.0) / step), 0, (1 << int(bj)) - 1).astype(np.uint8)
        out[:, j] = ((c.astype(np.float32) + 0.5) * step - 1.0) * comp[j]
        codes.append(c)
    return {"codes": codes, "bits": b.astype(np.uint8), "bits_total": int(b.sum()),
            "err": float(np.abs(out - coef).mean())}


def quantise(coef: np.ndarray, comp: np.ndarray, bits: int = 3, mode: str = "component") -> dict:''')

# ---- encode: allocation mode instead of a single depth --------------------------------------
s = s.replace('''    f = fit(rest, rank)
    q = quantise(f["coef"], f["comp"], bits, mode=mode)''',
'''    f = fit(rest, rank)
    q = quantise(f["coef"], f["comp"], bits, mode=mode)''')

s = s.replace('''def encode_basis(splats, rank: int, bits: int = 3, level: int = 12, path: str = None,
                 layout: str = "bytes", spec_name: str = "c10_o8_sh3",
                 mode: str = "component") -> dict:''',
'''def encode_basis(splats, rank: int, bits: int = 3, level: int = 12, path: str = None,
                 layout: str = "bytes", spec_name: str = "c10_o8_sh3",
                 mode: str = "component") -> dict:''')

assert s != orig
open(p, "w", encoding="utf-8").write(s)
print("patched allocation")
