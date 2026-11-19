import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("| 3.1b | 混入训练视角 → 覆盖率偏低 8pp 且看起来合理 | 可复现反例 |",
"""| 3.1a″ | **扩到 9 个场景**：5 个新场景 12/13 次测量为负，最强者 −17.8pp；幅度随模型质量缩小 | 9 场景 × 3 状态 |
| 3.1b | 混入训练视角 → 覆盖率偏低 8pp 且看起来合理 | 可复现反例 |""")
d = d.replace("""| 3.1a′ | **隔离实验推翻"收敛"解释**：剪到 200k 未微调（10 dB）仍掉 −5.5~−15.4pp | 4 场景 |""",
"""| 3.1a′ | **隔离实验**：剪到 200k 未微调（10 dB）仍掉 −5.5~−15.4pp | 4 场景 |""")
io.open(p, "w", encoding="utf-8").write(d)
print("index updated")
