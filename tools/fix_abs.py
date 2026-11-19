import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""第 2 条是本文的反面教材也是贡献：**conformal 预测的交换性假设在 3DGS 资产审计里很容易被无声破坏，
而破坏的后果是"证书看起来很好，实际上什么都没测到"。**""",
"""第 2 条是本文的反面教材也是贡献：**conformal 预测的交换性假设在 3DGS 资产审计里很容易被无声破坏，
而破坏的后果是"证书看起来很好，实际上什么都没测到"。**

此外我们在自己身上复现了一个更常见的陷阱：把训练视角混入标定集，
会让覆盖率悄悄偏低 8 个百分点而且看起来完全合理（§3.1b）。""")
io.open(p, "w", encoding="utf-8").write(s)
print("abstract updated")
