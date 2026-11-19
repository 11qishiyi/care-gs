import io
p = r"D:\3dsg_1\research\code\calib\colmap_io.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''    if filter_views:
        q = per_view_quality(sparse)
        q = {k: v[idx] for k, v in q.items()}
        keep = (q["n2d"] >= min_n2d) & (q["med_err"] <= max_med_err)''',
'''    if filter_views:
        q_full = per_view_quality(sparse)
        sel = np.asarray(idx, dtype=int)
        q = {k: np.asarray(v)[sel] for k, v in q_full.items()}
        keep = (q["n2d"] >= min_n2d) & (q["med_err"] <= max_med_err)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("indexing fixed")
