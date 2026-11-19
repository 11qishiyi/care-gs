import io

p = "experiments/m27_anchor.py"
s = io.open(p, encoding="utf-8").read()

old_start = s.index("def voxel_size_for(")
old_end = s.index("# ----------------------------------------------------------------------------- encoding")
new_block = '''def _key(ij: np.ndarray, side: int = 2048) -> np.ndarray:
    """One int64 per voxel so grouping is a 1-D sort instead of an ``axis=0`` unique.

    ``np.unique(..., axis=0)`` sorts rows and costs minutes on six million primitives; a linear key
    does the same job in seconds.  2048 levels per axis covers any voxel grid a 24-bit position
    quantiser can represent.
    """
    return (ij[:, 0] * side + ij[:, 1]) * side + ij[:, 2]


def voxel_size_for(means: np.ndarray, target_ppa: float = 8.0, iters: int = 12) -> float:
    """Voxel edge that puts ``target_ppa`` primitives in the average occupied voxel."""
    mn = means.min(axis=0)
    span = np.maximum(means.max(axis=0) - mn, 1e-6)
    #: a density estimate beats a blind bisection: n_anchors ~ volume / edge^3
    vol = float(np.prod(span))
    guess = (vol * max(target_ppa, 1.0) / max(1, len(means))) ** (1.0 / 3.0)
    lo, hi = guess / 2.5, guess * 2.5
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        ij = np.floor((means - mn) / mid).astype(np.int64)
        n_anchor = int(np.unique(_key(ij)).shape[0])
        ppa = len(means) / max(1, n_anchor)
        if ppa > target_ppa:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def group(means: np.ndarray, voxel: float):
    """Primitives sorted by voxel, plus the occupied voxel indices and per-voxel counts.

    Anchors sit at the *centre* of their voxel rather than at the mean of their members: the centre
    is a grid point the decoder can rebuild from the index alone (no stored float), and it bounds the
    member offset to ``+-voxel/2`` instead of ``+-voxel``, which halves the position error at the
    same 3-bit offset.
    """
    mn = means.min(axis=0)
    ij = np.floor((means - mn) / voxel).astype(np.int64)
    key = _key(ij)
    uniq_key, inv = np.unique(key, return_inverse=True)
    inv = inv.reshape(-1)
    order = np.argsort(inv, kind="stable")
    inv = inv[order]
    counts = np.bincount(inv, minlength=int(uniq_key.shape[0])).astype(np.int64)
    starts = np.concatenate([[0], np.cumsum(counts)[:-1]])
    #: recover the three indices of each occupied voxel from its key (same order as ``uniq_key``)
    side = 2048
    i = uniq_key // (side * side)
    rest = uniq_key % (side * side)
    j = rest // side
    l = rest % side
    vox = np.stack([i, j, l], axis=1).astype(np.int64)
    return order, starts, counts, vox, mn.astype(np.float32)


'''
s = s[:old_start] + new_block + s[old_end:]
io.open(p, "w", encoding="utf-8").write(s)
print("rewrote grouping")
