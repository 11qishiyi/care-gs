import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
# the paper is now organised as 6 subsections + 3 appendices; count both
s = s.replace('n_sections = len(re.findall(r"^### 3\\.", paper, flags=re.M))',
              'n_sections = len(re.findall(r"^### [0-9]", paper, flags=re.M)) + '
              'len(re.findall(r"^## 附录", paper, flags=re.M))')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("section counting fixed for the new structure")
