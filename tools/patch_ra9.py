import io
p = r"D:\3dsg_1\research\code\scripts\risk_alloc.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''    cal, dep = sc["cal_idx"], sc["dep_idx"]''',
'''    cal = np.asarray(sc["cal_idx"])[: args.max_cal]
    dep = np.asarray(sc["dep_idx"])[: args.max_dep]''')
s = s.replace('ap.add_argument("--thr_q", type=float, default=0.5)',
              'ap.add_argument("--thr_q", type=float, default=0.5)\n'
              '    ap.add_argument("--max_cal", type=int, default=12)\n'
              '    ap.add_argument("--max_dep", type=int, default=12)')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("capped view counts")
