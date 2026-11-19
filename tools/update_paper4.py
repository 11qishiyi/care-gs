import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""1. **几何编辑致命，外观/精度编辑无害**：剪枝到 30% 使覆盖率下降 **11.4–20.6 个百分点**（四场景全部落在
   干净态 95% 自助区间之外）；而 SH 阶数 3→1 与 SH 8-bit 量化的覆盖率变化都在噪声内（≤0.7pp）。
   此外**修复很便宜**：剪枝后只需 2–4 个留出视角重新标定即可回到名义水平。""",
"""1. **几何编辑致命，外观/精度编辑无害**：剪枝到 30% 使覆盖率下降 **11.4–20.6 个百分点**（四场景全部落在
   干净态 95% 自助区间之外）；而 SH 阶数 3→1 与 SH 8-bit 量化的覆盖率变化都在噪声内（≤0.7pp）。
   此外**修复很便宜**（2–4 个留出视角即可重签），**且剪枝准则的选择能把损失减半**
   （敏感度准则 −4.9~−10.0pp，不透明度准则 −11.6~−19.8pp）。""")
s = s.replace("| 主要结果 | `research/results_v22/cert_v3.json`（交错划分 + 三类编辑 + 修复曲线，主结果） |",
              "| 主要结果 | `research/results_v22/cert_v3.json`（交错划分 + 三类编辑 + 修复曲线，主结果） |\n| 剪枝准则对照 | `research/results_v23/tail_prune.json` |")
io.open(p, "w", encoding="utf-8").write(s)
print("paper updated with pruning-criterion guidance")
