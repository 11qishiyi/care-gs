import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("""| **`PAPER_certificate_invalid.md`** | 论文草稿（7 节，含摘要、结果、诚实边界、可复现性、下一步） |""",
"""| **`PAPER_certificate_invalid.md`** | 论文草稿（9 组结果 + 4 张图 + 诚实边界 + 可复现性） |
| **`APPENDIX_negative_results.md`** | 附录：八个被否定方向的完整证据链（假设 / 检验 / 结果 / 判定） |
| **`figures/`** | 四张图，全部由 `make_figures.py` 从原始 JSON 生成 |""")
io.open(p, "w", encoding="utf-8").write(d)
print("index updated with appendix")
