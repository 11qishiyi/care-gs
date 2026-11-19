import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("""| 训练器 | `scripts/train_gs.py` | 自训可用；高密度下过拟合（见 TRAINER_INVESTIGATION） |""",
"""| 训练器 | `scripts/train_gs.py` | 自训可用；高密度下过拟合（见 TRAINER_INVESTIGATION） |
| **证书顾问工具** | `scripts/advise.py` | 论文结论的落地形态：读 PLY 头 → 一秒内判定"要不要重签 / 几个留出视角 / 区间宽多少"。19 项断言锁定 |""")
d = d.replace("""python research/code/tests/test_operators.py          # 13 项算子断言（CPU）""",
"""python research/code/tests/test_operators.py          # 13 项算子断言（CPU）
python research/code/tests/test_advise.py             # 19 项顾问逻辑断言（CPU）""")
io.open(p, "w", encoding="utf-8").write(d)
print("index updated with advisor tool")
