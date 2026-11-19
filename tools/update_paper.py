import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""我们在 4 个场景（Mip-NeRF 360 的 flowers / treehill / bicycle / stump）上测量了失效幅度：

- 保留 50% 基元：覆盖率下降 **1.1–3.2** 个百分点；
- 保留 30% 基元：覆盖率下降 **5.8–16.1** 个百分点（四个场景全部单调下降）。""",
"""我们在 4 个场景（Mip-NeRF 360 的 flowers / treehill / bicycle / stump）上测量了失效幅度，
并用**视角级自助法**给出置信区间（覆盖率是视角级的量，有效样本量是视角数而非像素数）：

- 保留 50% 基元：覆盖率下降 **1.1–3.2** 个百分点；
- 保留 30% 基元：覆盖率下降 **5.8–15.5** 个百分点，**四个场景全部落在干净态的 95% 区间之外**；
- 同时发现证书本身**显著过度保守**（4 个场景中 3 个的干净态覆盖率 95% 区间不含名义值 0.90）。""")
s = s.replace("""| 原始结果 | `research/results_v17/cert_audit.json`、`results_v18/cert_hard.json` |""",
"""| 原始结果 | `research/results_v17/cert_audit.json`（主结果）、`results_v19/cert_ci.json`（含自助区间）、`results_v18/cert_hard.json`（失败的收紧尝试） |""")
io.open(p, "w", encoding="utf-8").write(s)
print("paper updated with CIs")
