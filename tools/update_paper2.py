import io, re
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()

s = s.replace("""- 保留 50% 基元：覆盖率下降 **1.1–3.2** 个百分点；
- 保留 30% 基元：覆盖率下降 **5.8–15.5** 个百分点，**四个场景全部落在干净态的 95% 区间之外**；
- 同时发现证书本身**显著过度保守**（4 个场景中 3 个的干净态覆盖率 95% 区间不含名义值 0.90）。""",
"""- 保留 50% 基元：覆盖率下降 **1.1–3.2** 个百分点；
- 保留 30% 基元：覆盖率下降 **5.8–15.5** 个百分点，**四个场景全部落在干净态的 95% 区间之外**；
- **但 SH 8-bit 量化不改变覆盖率**（0.00pp）——失效的是**几何编辑**，不是精度编辑；
- 同时发现证书本身**显著过度保守**（4 个场景中 3 个的干净态覆盖率 95% 区间不含名义值 0.90）。""")

# renumber the later sections
s = s.replace("### 3.3 无标签自检：可用但保守", "### 3.4 无标签自检：可用但保守")
s = s.replace("### 3.4 一个必须正面说明的现象：证书本身是过度保守的", "### 3.5 一个必须正面说明的现象：证书本身是过度保守的")
s = s.replace("- **编辑类型只有剪枝**，没有覆盖合并、量化、微调；",
              "- **编辑类型只有剪枝与 SH 量化**，没有覆盖合并、微调、重训；")
s = s.replace("| 原始结果 | `research/results_v17/cert_audit.json`（主结果）、`results_v19/cert_ci.json`（含自助区间）、`results_v18/cert_hard.json`（失败的收紧尝试） |",
              "| 原始结果 | `research/results_v17/cert_audit.json`（主结果）、`results_v19/cert_ci.json`（含自助区间）、`results_v20/cert_quant.json`（量化对照）、`results_v18/cert_hard.json`（失败的收紧尝试） |")
io.open(p, "w", encoding="utf-8").write(s)
print("paper updated: quantisation dichotomy")
