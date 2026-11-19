import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("| 3.2 | 几何编辑致命、外观/精度编辑无害 | 3 类编辑 × 4 场景 |",
              "| 3.2 | 几何 11–19pp ＞ 外观 0.2–2pp ＞ 精度 0pp，三层梯度 | 3 类编辑 × 4 场景 × 400 划分 |")
d = d.replace("| 3.1 | 剪枝 30% 使覆盖率 −11.4~−20.6pp | 4 场景，视角级 95% CI 全部排除 |",
              "| 3.1 | 剪枝 30% 使覆盖率 −10.9~−18.6pp | 4 场景 × 400 次随机划分，干净态覆盖率精确 0.90 |")
io.open(p, "w", encoding="utf-8").write(d)
print("index synced")
