import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("""**论文数字校验**：""",
"""**算子单元测试**：`python research/code/tests/test_operators.py`（CPU，无需 GPU，13 项断言全部通过）。
其中最关键的是 `test_conformal_finite_sample_coverage`——分裂保形预测有**精确的有限样本保证**，
而分位数索引一个 off-by-one 就会悄悄破坏它。整个报告都建立在这个算子上。

**论文数字校验**：""")
io.open(p, "w", encoding="utf-8").write(d)
print("index updated with unit tests")
