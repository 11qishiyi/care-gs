import io
p = r"D:\3dsg_1\research\code\scripts\certificate_audit.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''                      cal_idx=np.array(pool[0::2]), dep_idx=np.array(pool[1::2]))''',
'''                      cal_idx=np.array(pool[0::2]), dep_idx=np.array(pool[1::2]))
            cal = list(sc["cal_idx"])
            dep = list(sc["dep_idx"])''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed unbound cal/dep")
