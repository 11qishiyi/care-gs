import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("| **3.3** | **核心卖点**：证书低估实际损失 **2–12 倍**",
              "| 3.3 | **核心卖点**：证书低估实际损失 **2–12 倍**")
io.open(p, "w", encoding="utf-8").write(d)
print("3.3 row normalised")
