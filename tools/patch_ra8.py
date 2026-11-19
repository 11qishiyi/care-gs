import io
p = r"D:\3dsg_1\research\code\scripts\risk_alloc.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("    if args.clamp_scale > 0:", "    if args.clamp_frac > 0:")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed clamp arg name")
