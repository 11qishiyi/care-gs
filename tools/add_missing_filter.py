import io
p = r"D:\3dsg_1\research\code\calib\colmap_io.py"
s = io.open(p, encoding="utf-8").read()
old = '''    idx = np.arange(len(paths))
    if filter_views:
        q = per_view_quality(sparse)'''
new = '''    idx = np.arange(len(paths))
    # mirrors sometimes ship only a subset of the images; drop cameras whose file is missing
    missing = np.array([not os.path.isfile(p) for p in paths])
    if missing.any():
        print(f"[scene] dropping {int(missing.sum())} views whose image file is absent",
              flush=True)
        keep = ~missing
        idx = idx[keep]
        camtoworlds = [camtoworlds[i] for i in idx]
        Ks = [Ks[i] for i in idx]
        paths = [paths[i] for i in idx]
    if filter_views:
        q = per_view_quality(sparse)
        q = {k: v[idx] for k, v in q.items()}'''
assert old in s
s = s.replace(old, new)
# after the quality filter, 'keep' indexes the already-filtered idx
s = s.replace('''        keep = (q["n2d"] >= min_n2d) & (q["med_err"] <= max_med_err)
        idx = idx[keep]''',
'''        keep = (q["n2d"] >= min_n2d) & (q["med_err"] <= max_med_err)
        idx = idx[keep]''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("missing-image filter added")
