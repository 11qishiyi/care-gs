import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("### 3.3 划分方式的影响（本文最重要的方法论教训）", "### 3.4 划分方式的影响（本文最重要的方法论教训）")
io.open(p, "w", encoding="utf-8").write(s)
print("renumbered")
