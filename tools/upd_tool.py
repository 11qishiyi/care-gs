import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""5. **做成工具**：给定资产 + 编辑记录，20 秒内判定是否需要重签、需要几个留出视角。""",
"""5. ~~做成工具~~ **已完成**：`research/code/scripts/advise.py` 把本文的规则编码成一个 CLI，
   读 PLY 头取基元数（无需 GPU、无需渲染），一秒内回答"这个编辑要不要重签、要几个留出视角、区间会宽多少"。
   决策逻辑由 `tests/test_advise.py` 的 19 项断言锁定（编辑家族分类、密度阈值、
   损伤范围、未知编辑保守处理）。""")
io.open(p, "w", encoding="utf-8").write(s)
print("paper §7: tool marked done")
