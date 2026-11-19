import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""**几何编辑致命，外观/精度编辑无害**：剪枝到 30% 使覆盖率下降 **11.4–20.6 个百分点**
   （4 场景、8–13 个部署视角，视角级自助区间全部排除）；""",
"""**几何编辑致命，外观/精度编辑无害**——但仅限高密度已收敛模型：剪枝到 30% 使覆盖率下降
   **11.4–20.6 个百分点**（4 个发布检查点，3.1M–5.3M 基元，视角级自助区间全部排除）；
   在 5 个轻量自训模型（≤241k 基元）上该效应**不存在**（−0.7~+3.2pp，见 §3.1a）；""")
s = s.replace("| 分辨率鲁棒性 | `research/results_v31/cert_f2.json` |",
              "| 分辨率鲁棒性 | `research/results_v31/cert_f2.json` |\n| 适用区间（5 个轻量模型反例） | `research/results_v35/*.json` |")
io.open(p, "w", encoding="utf-8").write(s)
print("abstract + refs updated")
