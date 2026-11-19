import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("> 修复只要 **2–4 个留出视角**，但重标定会把区间放宽 **26–83%**。",
              "> 修复只要 **2–4 个留出视角**，但重标定会把区间放宽 **26–71%**。")
io.open(p, "w", encoding="utf-8").write(d)
print("index width synced")
