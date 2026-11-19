import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("| 3.6 | 选敏感度准则而非不透明度准则，损失减半 | 4 场景 × 3 准则 |",
              "| 3.6 | 选敏感度准则：损失压掉 70–83%（flowers 仅 15%），且区间宽度几乎不变 | 4 场景 × 400 划分 |")
io.open(p, "w", encoding="utf-8").write(d)
print("index synced")
