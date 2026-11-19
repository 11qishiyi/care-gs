import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("### 3.4 划分方式的影响（本文最重要的方法论教训）", "### 3.5 划分方式的影响（本文最重要的方法论教训）")
s = s.replace("### 3.5 如果非要剪枝：选对准则能把损失减半", "### 3.6 如果非要剪枝：选对准则能把损失减半")
s = s.replace("### 3.6 无标签自检（交错划分下）", "### 3.7 无标签自检（交错划分下）")
s = s.replace("""2. **标定/部署划分方式决定一切**""", """2. **重标定保住了覆盖率，却把区间放宽 26–83%**：证书仍有效但精度差近一倍。
   覆盖率不是剪枝代价的敏感指标，**区间宽度才是**。实践含义：证书应在剪枝之后签发。
3. **标定/部署划分方式决定一切**""")
s = s.replace("""第 2 条是本文的反面教材也是贡献""", """第 3 条是本文的反面教材也是贡献""")
s = s.replace("| 主要结果 | `research/results_v22/cert_v3.json`（合法留出视角；三类编辑 + 修复曲线） |",
              "| 主要结果 | `research/results_v22/cert_v3.json`（合法留出视角；三类编辑 + 修复曲线 + 区间宽度） |\n| 按证书剪枝实验 | `research/results_v27/cert_pruner.json` |")
io.open(p, "w", encoding="utf-8").write(s)
print("renumbered + abstract updated")
