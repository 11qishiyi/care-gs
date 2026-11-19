p = "experiments/m23_pred.py"
s = open(p, encoding="utf-8").read()
orig = s

#: positions are 10 bits packed, i.e. 1.25 B/level: any byte-aligned delta is 2 B and the byte
#: alignment tax measured larger than the correlation it exposes.  Scales and opacity are 8-bit, so a
#: modular uint8 delta keeps the same width and only moves the entropy.
s = s.replace('''TARGETS = {
    "cluster_off": ("cluster_off", "means", 3, "cluster_off_d"),
    "geo_scales": ("geo_scales", "scales", 3, "geo_scales_d"),
    "geo_opacities": ("geo_opacities", "opacities", 1, "geo_opacities_d"),
}''',
'''TARGETS = {
    "geo_scales": ("geo_scales", "scales", 3, "geo_scales_d"),
    "geo_opacities": ("geo_opacities", "opacities", 1, "geo_opacities_d"),
}

#: streams measured and rejected: ``cluster_off`` is 10 bits packed (1.25 B/level), so a byte-aligned
#: int16 delta costs 2 B/level before zstd and measured +2.2 MB on the file (M23).  Kept here so the
#: next round does not re-try it.
REJECTED = {"cluster_off": "10-bit packed is 1.25 B/level; int16 deltas are 2 B and lost 2.2 MB"}''')

s = s.replace('''def narrow(d: np.ndarray) -> tuple:
    """The narrowest integer width that holds ``d``: int8 where it fits, else int16.

    An 8-bit level stream stored as int16 deltas would have to beat its own 1 B/level packing by
    50 % before the transform paid for itself; int8 only needs to beat it at all.
    """
    lo, hi = int(d.min()), int(d.max())
    if -128 <= lo and hi <= 127:
        return d.astype(np.int8), "i1"
    assert -32768 <= lo and hi <= 32767, f"delta does not fit int16: {lo}..{hi}"
    return d.astype("<i2"), "i2"''',
'''def narrow(d: np.ndarray, bits: int) -> tuple:
    """Store an 8-bit level stream's deltas as *modular* uint8: same width, lower entropy.

    An autocorrelation of 0.9 between neighbouring levels is worth nothing if exposing it costs 2 B
    instead of 1, which is what an int16 delta does (measured: scales went 18.40 MB -> 36.79 MB before
    zstd).  Modular arithmetic keeps the level width and lets zstd see small values near zero and near
    255 instead of a uniform spread.
    """
    if bits <= 8:
        return (d & 0xFF).astype(np.uint8), "u1"
    lo, hi = int(d.min()), int(d.max())
    if -128 <= lo and hi <= 127:
        return d.astype(np.int8), "i1"
    assert -32768 <= lo and hi <= 32767, f"delta does not fit int16: {lo}..{hi}"
    return d.astype("<i2"), "i2"''')

s = s.replace('''        d, dtype = narrow(to_delta(levels))''', '''        d, dtype = narrow(to_delta(levels), bits)''')

s = s.replace('''        dt = "<i1" if str(f.get("dtype", "i2")) == "i1" else "<i2"
        d = np.frombuffer(out[dname], dtype=dt).reshape(count, dim)
        levels = np.clip(from_delta(d, count), 0, (1 << bits) - 1).astype(np.int64)''',
'''        dt = {"u1": "u1", "i1": "<i1"}.get(str(f.get("dtype", "i2")), "<i2")
        d = np.frombuffer(out[dname], dtype=dt).astype(np.int64).reshape(count, dim)
        if dt == "u1":
            #: modular: the cumulative sum modulo 2**bits is the level sequence again
            levels = (np.cumsum(d, axis=0) & ((1 << bits) - 1)).astype(np.int64)
        else:
            levels = np.clip(from_delta(d, count), 0, (1 << bits) - 1).astype(np.int64)''')

assert s != orig
open(p, "w", encoding="utf-8").write(s)

p = "experiments/m23_run.py"
s = open(p, encoding="utf-8").read()
orig = s
s = s.replace('''VARIANTS = {
    "A_base": ("c10_o8_sh3", False),
    "B_delta": ("c10_o8_sh3", True),
    "C_st3": ("gp8-8-8_c10_sh3", False),
    "D_both": ("gp8-8-8_c10_sh3", True),
}''',
'''VARIANTS = {
    "A_base": ("c10_o8_sh3", False),
    "B_delta": ("c10_o8_sh3", True),
    "C_st3": ("gp8-8-8_c10_sh3", False),
    "D_both": ("gp8-8-8_c10_sh3", True),
}
#: what each variant isolates, for the report
PURPOSE = {
    "A_base": "the M22 point, reproduced",
    "B_delta": "A + modular deltas on scales/opacity (lossless)",
    "C_st3": "A + smallest-three quaternions (M15 measured this as free)",
    "D_both": "B + C",
}''')
assert s != orig
open(p, "w", encoding="utf-8").write(s)
print("patched modular deltas")
