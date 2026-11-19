import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("""| 结果数据按轮次存放""", """| 结果数据按轮次存放""")
d = d.replace("""结果数据按轮次存放在 `research/results_v1..v24/`，主结果为 `results_v22/cert_v3.json`。""",
"""结果数据按轮次存放在 `research/results_v1..v28/`，主结果为 `results_v22/cert_v3.json`。

**论文数字校验**：`python research/code/scripts/verify_paper_numbers.py` 会把论文里每个数字与原始 JSON 逐一比对
（44 项检查，当前全部通过）。这个脚本在最后一轮抓出了一个真实抄写错误（stump 的值 0.885 → 0.778），
建议任何后续修改后都重跑。""")
io.open(p, "w", encoding="utf-8").write(d)
print("index updated with verification instructions")
