import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("> **11.4–20.6 个百分点**（4 个高密度场景、8–13 留出视角、视角级自助区间全部排除）；",
              "> **10.9–18.6 个百分点**（4 个已收敛场景，每场景 16–25 个留出视角，400 次随机划分的配对区间全部排除零）；")
d = d.replace("""> 四个剪到 200k 再微调的紧凑模型（280k–390k 基元）在四个场景上都掉 −17.7~−20.6pp，""",
              """> 四个剪到 200k 再微调的紧凑模型（0.29M–0.39M 基元）在四个场景上都掉 −10.3~−12.9pp，""")
io.open(p, "w", encoding="utf-8").write(d)
print("deliverables synced")
