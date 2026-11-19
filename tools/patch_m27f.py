import io

p = "experiments/m27_anchor.py"
s = io.open(p, encoding="utf-8").read()

start = s.index("def voxel_size_for(")
end = s.index("def group(")
new = '''def voxel_size_for(means: np.ndarray, target_ppa: float = 8.0, iters: int = 10) -> float:
    """Voxel edge that puts ``target_ppa`` primitives in the average occupied voxel.

    A density estimate brackets the answer, then the bracket is *checked* by expanding it until it
    really contains the target -- the first version of this function trusted the estimate and
    returned a voxel ten times too coarse, which quietly turned a ``ppa = 8`` sweep into a
    ``ppa = 85`` one (every container 2.5x smaller and unusable, with no error anywhere).
    """
    mn = means.min(axis=0)
    span = np.maximum(means.max(axis=0) - mn, 1e-6)
    vol = float(np.prod(span))
    guess = (vol * max(target_ppa, 1.0) / max(1, len(means))) ** (1.0 / 3.0)

    def ppa_at(edge: float) -> float:
        ij = np.floor((means - mn) / edge).astype(np.int64)
        return len(means) / max(1, int(np.unique(_key(ij)).shape[0]))

    lo = hi = None
    edge = guess
    for _ in range(24):
        p = ppa_at(edge)
        if p > target_ppa:
            hi = edge
            edge *= 0.6
            if lo is not None:
                break
        else:
            lo = edge
            edge *= 1.6
            if hi is not None:
                break
    if lo is None:
        lo = edge * 0.6
    if hi is None:
        hi = edge * 1.6
    if hi < lo:
        lo, hi = hi, lo
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if ppa_at(mid) > target_ppa:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


'''
s = s[:start] + new + s[end:]
io.open(p, "w", encoding="utf-8").write(s)
print("patched voxel search")
