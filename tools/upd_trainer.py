import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("""| **`figures/`** | 四张图，全部由 `make_figures.py` 从原始 JSON 生成 |""",
"""| **`figures/`** | 四张图，全部由 `make_figures.py` 从原始 JSON 生成 |
| **`research/TRAINER_INVESTIGATION.md`** | 训练器的两个问题：一个已修（尺度往返 ×100），一个未解（高密度过拟合），附排除清单与接手建议 |""")
d = d.replace("""| 一个真实的下游任务 | 把"可用区域"从图像块换成真实决策（导航/抓取），任务感知分配可能重获价值 |""",
"""| 一个真实的下游任务 | 把"可用区域"从图像块换成真实决策（导航/抓取），任务感知分配可能重获价值 |
| **一个能训出 ≳2M 基元且留出 ≥18 dB 的训练器** | 把论文 §3.1a 的 5 个反例变成 9 个阳性，删掉那条混淆声明——这是当前**唯一**能实质提升论文强度的动作 |""")
io.open(p, "w", encoding="utf-8").write(d)
print("index updated with trainer investigation")
