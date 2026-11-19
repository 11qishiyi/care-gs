import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""**修复很便宜**（2–4 个留出视角即可重签），**且剪枝准则的选择能把损失减半**
   （敏感度准则 −4.9~−10.0pp，不透明度准则 −11.6~−19.8pp）。""",
"""**修复很便宜**（2–4 个留出视角即可重签），**且剪枝准则的选择能把损失压掉 70–83%**
   （敏感度准则 2.0–9.3pp，不透明度准则 10.9–18.6pp；flowers 上两者差别较小）。""")
io.open(p, "w", encoding="utf-8").write(s)
print("abstract synced")
