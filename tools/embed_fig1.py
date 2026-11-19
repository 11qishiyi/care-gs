import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("### 3.2 几何编辑致命，外观/精度编辑无害\n我们测了三类编辑",
              "### 3.2 几何编辑致命，外观/精度编辑无害\n\n![编辑类型对证书的影响](figures/fig1_edit_families.png)\n\n我们测了三类编辑")
io.open(p, "w", encoding="utf-8").write(s)
print("fig1 embedded")
