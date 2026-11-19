import io
p = r"D:\3dsg_1\research\code\scripts\selfcheck_stats.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('ap.add_argument("--scenes", default="flowers,treehill"]',
              'ap.add_argument("--scenes", default="flowers,treehill")')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("syntax fixed")
