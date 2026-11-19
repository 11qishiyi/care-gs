import io
p = r"D:\3dsg_1\research\code\scripts\variance_object_test.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''            C = out["C"]
            if EXPOSURE:''','''            C = torch.from_numpy(out["C"]).to(args.device)
            if EXPOSURE:''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed")
