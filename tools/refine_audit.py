import io
p = r"D:\3dsg_1\NOVELTY_AUDIT_2026-11.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""**定位建议**：把 AURA 写进 Related Work 的**第一句**，明确分工——
"AURA 解决的是*如何签发一个可信证书*；本文问的是*证书签发之后会发生什么，以及证书这个指标够不够*。"
不要试图在"谁的剪枝更好"这条赛道上和它比。""",
"""**一个必须注意的 nuance**：AURA 的证书覆盖的是一条**认证的 LoD 阶梯**，也就是说
"消费者在若干预设层级之间切换"这一情形它已经考虑了。因此我们不能把"消费者会继续剪枝"当成本文独有。
**本文真正多出来的情形是**：消费者用**自己的准则**（而非证书指定准则）剪枝、
或者做证书未覆盖的编辑（合并、SH 降阶、微调）——这时候证书与模型不再对应，而 AURA 的框架没有测量这种情况。

**定位建议**：把 AURA 写进 Related Work 的**第一句**，明确分工——
"AURA 解决的是*如何签发一个可信证书，并让它在预设的 LoD 阶梯内继续有效*；
本文问的是*证书被带到阶梯之外时会发生什么，以及证书这个指标本身够不够*。"
不要试图在"谁的剪枝更好"这条赛道上和它比。""")
s = s.replace("""**已查**：arXiv（多组关键词）、engrxiv、Zenodo、PyPI、ScienceDirect、CVF、Springer、本地 1066 条 3DGS 方法库（含 conformal / certificate / calibrated / audit 关键词）。""",
"""**已查**：arXiv（多组关键词）、engrxiv、Zenodo、PyPI、ScienceDirect、CVF、Springer、本地 1066 条 3DGS 方法库
（含 conformal / certificate / calibrated / audit 关键词）。AURA 全文 PDF 已取到（7.3 MB），
其摘要、指标定义与 LoD 阶梯描述已核对。""")
io.open(p, "w", encoding="utf-8").write(s)
print("audit report refined with the LoD-ladder nuance")
