import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("（−0.7~+3.2pp）", "（−0.8~+3.2pp）")
io.open(p, "w", encoding="utf-8").write(d)
print("index synced")
