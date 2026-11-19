import io
p = r"D:\3dsg_1\research\code\scripts\certifying_pruner.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''        print("    opacity ref: " + "  ".join(
            f"{f}:{row[f'opacity_cov_at_{fixed}']:.3f}" for fixed in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7)),
            flush=True)''',
'''        print("    opacity ref: " + "  ".join(
            f"{fx}:{row['opacity_cov_at_%s' % fx]:.3f}" for fx in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7)),
            flush=True)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed f-string")
