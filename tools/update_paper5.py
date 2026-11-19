import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""1. **几何编辑致命，外观/精度编辑无害**：剪枝到 30% 使覆盖率下降 **11.4–20.6 个百分点**（四场景全部落在
   干净态 95% 自助区间之外）；""",
"""1. **几何编辑致命，外观/精度编辑无害**：剪枝到 30% 使覆盖率下降 **9.7–17.2 个百分点**
   （3 个场景、62–85 个部署视角，降幅是置信区间宽度的 2.5–4 倍）；""")
s = s.replace("- **场景数只有 4**，全部来自同一归档；",
              "- **场景数只有 4**（其中 3 个有 train GT 可用于大样本统计），全部来自同一归档；")
s = s.replace("- 视角数 8–13，置信区间较宽（如 bicycle 的干净态区间 [0.802, 0.914]）；",
              "- 用全部视角时干净态覆盖率落在 0.82–0.89，**低于名义值**（证书偏乐观）；只用 test 子集时为 0.86–0.91。\n  两者不可直接混用，这是我们尚未解决的一致性问题；")
s = s.replace("| 主要结果 | `research/results_v22/cert_v3.json`（交错划分 + 三类编辑 + 修复曲线，主结果） |",
              "| 主要结果 | `research/results_v24/cert_all.json`（全部视角，大样本）、`results_v22/cert_v3.json`（test 子集，三类编辑 + 修复曲线） |\n| 全部视角场景构造 | `research/code/calib/archive_all.py` |")
io.open(p, "w", encoding="utf-8").write(s)
print("paper updated with all-views result")
