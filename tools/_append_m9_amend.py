"""Append M9.4a: the grid amendment made before any M9 data existed."""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "experiments", "METHOD_PLAN.md")
TEXT = """
### M9.4a 网格修订与 K2 聚合（预注册 2026-11-14 01:30，**数据落盘前**）

证据：此刻 `/workspace/res/m9` 不存在，节点 2139436 于 01:12 释放后未再租用，
`experiments/m9_rd.json` 不存在。

**修订 1（覆盖缺口，N16 的教训）**：初版 12 变体里，字典族全部落在 11.8–14.2 B/prim，
而逐系数 SH 最便宜的两行是 `c10_o8_sh3`(31.8 B) 与 `c12_o8_sh2`(26.6 B)——
K2 的 ±15% 匹配窗**在任何资产上都不会有配对**，判据不可测。这正是 M2、M7
两次失败的同一种错误（网格 × 判据码率点没有覆盖矩阵），因此在数据前补齐 5 行
同字节的逐系数基线：`d0_c8_o6_sh2`(11.84 B)、`d0_c8_o8_sh2`(13.84 B)、
`d0_c10_o6_sh2`(12.59 B)、`d0_c12_o8_sh2`(15.34 B)、`d1_c8_o6_sh2`(14.09 B)。
网格由 12 变体变 **18 变体**。

**修订 2（K2 聚合）**：初版只写"同字节日下 VQ 比逐系数少丢 ≥1.0 pp"，没规定一个资产有
多对匹配时怎么聚合。**取该资产所有匹配对的差值中位数**（不是最大值），原因：
取最大值等于允许用一对幸运配对代表整个资产，而中位数要求字典在窗口内普遍更好。
报告仍列出每一对，"最佳对"只作参考。

**不变项**：K1/K3 的阈值与定义、±15% 窗、b 的取值集合 {6,8,10,12,14}、
k-means 种子与迭代数、`dPSNR ≥ 0` 的合格性条款全部不动。
"""
with io.open(P, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(TEXT)
print("appended", len(TEXT))
