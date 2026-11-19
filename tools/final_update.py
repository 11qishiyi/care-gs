import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("| 主要结果 | `research/results_v22/cert_v3.json`（合法留出视角；三类编辑 + 修复曲线 + 区间宽度） |",
              "| 主要结果 | `research/results_v22/cert_v3.json`（合法留出视角；三类编辑 + 修复曲线 + 区间宽度） |\n| α 鲁棒性 | `research/results_v28/cert_a0.05.json`、`cert_a0.2.json` |")
# also record in the deliverables index
p2 = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p2, encoding="utf-8").read()
d = d.replace("""| 3.5 | 选敏感度准则而非不透明度准则，损失减半 | 4 场景 × 3 准则 |""",
"""| 3.5 | 选敏感度准则而非不透明度准则，损失减半 | 4 场景 × 3 准则 |
| 3.1c | 结论在 α=0.05/0.10/0.20 一致，退化随 α 单调增大（−8.1 → −14.1 → −19.4） | 4 场景 × 3 α |
| 3.3 | 重标定保住覆盖率但区间放宽 26–83%，覆盖率不是敏感指标 | 4 场景 |""")
io.open(p, "w", encoding="utf-8").write(s)
io.open(p2, "w", encoding="utf-8").write(d)
print("paper + index updated")
