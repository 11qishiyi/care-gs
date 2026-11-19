import io
p = r"D:\3dsg_1\APPENDIX_negative_results.md"
s = io.open(p, encoding="utf-8").read()
anchor = "## 贯穿全程的三次自我否决"
new = """## N9. 把结论外推到轻量模型（失败，但产生了论文的适用区间）

**假设**：证书退化效应应该在更多场景上复现，只要场景数够。

**检验**：从 Mip-NeRF 360 官方公开桶下载 5 个新场景（garden / room / counter / kitchen / bonsai），
自训 3DGS，用完全相同的协议重测。

**结果**：**五个场景全部无效应**（−0.7 ~ +3.2pp），而四个发布检查点是 −11.4 ~ −20.6pp。
两者的差别不在场景，而在**模型密度**：自训模型 117k–241k 基元，发布检查点 3.1M–5.3M。

**判定**：原结论**过度泛化**。已改写为条件命题（论文 §3.1a）：
效应只在**高密度（≳3M 基元）、已收敛**的模型上出现。

**净收获**：这不是失败，是把一个会被反例打穿的普适结论，换成了一个带明确边界的真命题。
顺带更正了一个更早的错误判断——我曾说"数据源已穷尽"，实际上官方桶完全可达。

证据：`research/ROUND35_scope_condition.md`、`research/results_v35/`

---

## 贯穿全程的三次自我否决"""
s = s.replace(anchor, new)
io.open(p, "w", encoding="utf-8").write(s)
print("appendix: N9 added")
