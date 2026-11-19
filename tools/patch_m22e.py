p = "experiments/m22_basis.py"
s = open(p, encoding="utf-8").read()
orig = s
s = s.replace("""    s2 = np.asarray(comp, dtype=np.float64) ** 2
    for _ in range(bits_total - lo * r):
        gain = s2 * (4.0 ** -b) * 3.0
        gain[b >= hi] = -1.0
        b[int(np.argmax(gain))] += 1""",
"""    s2 = np.asarray(comp, dtype=np.float64) ** 2
    for _ in range(bits_total - lo * r):
        if bool((b >= hi).all()):
            break                     # every component is at the cap: the budget cannot be spent
        gain = s2 * (4.0 ** -b) * 3.0
        gain[b >= hi] = -1.0
        b[int(np.argmax(gain))] += 1""")
assert s != orig
open(p, "w", encoding="utf-8").write(s)

p = "experiments/tests/test_m22_basis.py"
s = open(p, encoding="utf-8").read()
orig = s
s = s.replace('''def test_the_allocator_spends_bits_where_the_variance_is():''',
'''def test_the_allocator_stops_at_the_cap():
    """A budget larger than ``rank * cap`` must not hand one component 44 bits (it did, and the
    cast to uint16 then produced NaNs and a 331 % relative error)."""
    comp = np.array([1e3, 1.0, 1.0], dtype=np.float32)
    b = B.allocate(comp, 300, hi=12)
    assert int(b.max()) <= 12, b
    assert int(b.sum()) <= 36, b


def test_the_allocator_spends_bits_where_the_variance_is():''')
s = s.replace('''    test_the_allocator_spends_bits_where_the_variance_is()''',
'''    test_the_allocator_stops_at_the_cap()
    test_the_allocator_spends_bits_where_the_variance_is()''')
assert s != orig
open(p, "w", encoding="utf-8").write(s)
print("patched cap")
