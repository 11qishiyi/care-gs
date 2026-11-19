import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('listed = len(re.findall(r"^\\| 3\\.", idx, flags=re.M))',
              'listed = len(re.findall(r"^\\| (?:3\\.|附录)", idx, flags=re.M))')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("index-row regex covers appendices")
