import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("""| 3.1c | 结论在 α=0.05/0.10/0.20 一致，退化随 α 单调增大（−8.1 → −14.1 → −19.4） | 4 场景 × 3 α |""",
"""| 3.1c | 结论在 α=0.05/0.10/0.20 一致，退化随 α 单调增大（−8.1 → −14.1 → −19.4） | 4 场景 × 3 α |
| 3.1d | 结论与渲染分辨率无关（1/4 vs 1/2 分辨率差 ≤1.4pp） | 4 场景 |""")
io.open(p, "w", encoding="utf-8").write(d)
print("index updated")
