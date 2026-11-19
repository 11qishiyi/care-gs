import io
p = r"D:\3dsg_1\research\code\scripts\certificate_audit.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace(".amax(axis=(2, 4))", ".max(axis=(2, 4))")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("numpy amax -> max")
