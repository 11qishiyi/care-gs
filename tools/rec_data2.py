import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("""1. **合法留出视角只有 8–13 个/场景**——归档只提供 4 个场景的 test GT。扩大样本必须有新的、带独立留出集的检查点来源。这是外部约束，不是方法问题。""",
"""1. **合法留出视角只有 8–13 个/场景**——归档只提供 4 个场景的 test GT。扩大样本必须有新的、带独立留出集的检查点来源。
   **已穷尽验证**：归档共 5 个场景，第 5 个（bungeenerf-amsterdam）只有检查点与 161 个相机、**没有 GT 图像**，
   无法用于证书审计；BungeeNeRF 原始数据集只通过 Google Drive / 百度网盘分发，无法在算力节点上脚本化获取。
   这是外部约束，不是方法问题。""")
io.open(p, "w", encoding="utf-8").write(d)
print("index updated with verified data constraint")
