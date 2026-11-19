import io
p = r"D:\3dsg_1\research\code\scripts\variance_object_test.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("            for k in acc:\n                acc[k].append(out[k].ravel())",
              "            for k in (\"V_mm\", \"V_ind\", \"V_cpl\"):\n                acc[k].append(out[k].ravel())")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed")
