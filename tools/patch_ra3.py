import io
p = r"D:\3dsg_1\research\code\scripts\risk_alloc.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('ap.add_argument("--out3dgs", required=True)', 'ap.add_argument("--out3dgs", default="")')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("out3dgs now optional")
