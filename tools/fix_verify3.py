import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('paper = io.open(PAPER, encoding="utf-8").read()',
              'paper = io.open(PAPER, encoding="utf-8").read()\nSCENES_LIST = ["flowers", "treehill", "bicycle", "stump"]')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("SCENES_LIST defined")
