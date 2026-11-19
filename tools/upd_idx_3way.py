import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("| 3.1a | **适用区间**：驱动因素是**优化状态**不是规模——4 个 280k–390k 的紧凑微调模型仍掉 −17.7~−20.6pp | 9 + 4 模型 |",
              "| 3.1a | **适用区间**：驱动因素是**优化状态**不是规模——三分严格划分下，4 个 0.29M–0.39M 紧凑模型仍掉 −10.3~−12.9pp，干净态覆盖率精确 0.900 | 9 + 4 模型 |")
io.open(p, "w", encoding="utf-8").write(d)
print("index updated")
