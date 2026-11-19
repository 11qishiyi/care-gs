import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""- **场景数 4**，全部来自同一归档，合法留出视角每场景仅 8–13 个；""",
"""- **场景数 4**，全部来自同一归档，合法留出视角每场景仅 8–13 个。
  我们已穷尽该归档：它共含 5 个场景（bicycle / flowers / stump / treehill / bungeenerf-amsterdam），
  但 **bungeenerf 只有检查点与相机、没有 GT 图像**，无法用于证书审计；
  外部补充来源（BungeeNeRF 原始数据集）只通过 Google Drive / 百度网盘分发，无法在算力节点上脚本化获取。""")
io.open(p, "w", encoding="utf-8").write(s)
print("paper: data-availability verified and recorded")
