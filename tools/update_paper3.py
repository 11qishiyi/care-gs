import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("### 3.4 无标签自检（交错划分下）", "### 3.5 无标签自检（交错划分下）")
s = s.replace("### 3.4 划分方式的影响（本文最重要的方法论教训）", "### 3.3 划分方式的影响（本文最重要的方法论教训）")
# fix ordering: renumber cleanly
s = s.replace("### 3.3 划分方式的影响（本文最重要的方法论教训）", "### 3.4 划分方式的影响（本文最重要的方法论教训）") if False else s
s = s.replace("""1. **几何编辑致命，精度编辑无害**：剪枝到 30% 使覆盖率下降 **11.4–20.6 个百分点**（四场景全部落在
   干净态 95% 自助区间之外）；而 SH 8-bit 量化使覆盖率变化 **0.00pp**。""",
"""1. **几何编辑致命，外观/精度编辑无害**：剪枝到 30% 使覆盖率下降 **11.4–20.6 个百分点**（四场景全部落在
   干净态 95% 自助区间之外）；而 SH 阶数 3→1 与 SH 8-bit 量化的覆盖率变化都在噪声内（≤0.7pp）。
   此外**修复很便宜**：剪枝后只需 2–4 个留出视角重新标定即可回到名义水平。""")
s = s.replace("- **编辑类型只有剪枝与 SH 量化**，没有合并、微调、重训；",
              "- **编辑类型覆盖剪枝、SH 阶数、SH 量化**，但没有合并、微调、重训；")
s = s.replace("| 主要结果 | `research/results_v21/cert_inter.json`（交错，主结果） |",
              "| 主要结果 | `research/results_v22/cert_v3.json`（交错划分 + 三类编辑 + 修复曲线，主结果） |")
io.open(p, "w", encoding="utf-8").write(s)
print("paper updated v3")
