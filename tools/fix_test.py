import io
p = r"D:\3dsg_1\research\code\tests\test_operators.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''    # fewer views -> wider interval
    means2 = rng.choice(per_view[:10], size=(2000, 10), replace=True).mean(axis=1)
    lo2, hi2 = np.percentile(means2, [2.5, 97.5])
    ok(hi2 - lo2 > hi - lo, "interval widens with fewer views")''',
'''    # fewer views -> wider interval (use continuous per-view coverage so a
    # degenerate all-ones subset cannot happen)
    per_view_c = np.clip(rng.beta(9.0, 1.2, size=400), 0.0, 1.0)
    rng2 = np.random.default_rng(3)
    m_all = rng2.choice(per_view_c, size=(2000, 400), replace=True).mean(axis=1)
    m_few = rng2.choice(per_view_c, size=(2000, 10), replace=True).mean(axis=1)
    w_all = np.diff(np.percentile(m_all, [2.5, 97.5]))[0]
    w_few = np.diff(np.percentile(m_few, [2.5, 97.5]))[0]
    ok(w_few > w_all, f"interval widens with fewer views ({w_few:.4f} > {w_all:.4f})")''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed bootstrap test")
