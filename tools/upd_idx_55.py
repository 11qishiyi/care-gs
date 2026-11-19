import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("| 3.3 | 重标定保住覆盖率但区间放宽 26–83% | 4 场景 |",
              "| 3.3 | 重标定保住覆盖率但区间放宽 26–71%（400 划分下的 q） | 4 场景 |")
io.open(p, "w", encoding="utf-8").write(d)
print("index synced")
