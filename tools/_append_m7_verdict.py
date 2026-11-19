"""Append the M7 verdict (M7.4b + outcome) to METHOD_PLAN.md, once, with numbers."""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "experiments", "METHOD_PLAN.md")
TEXT = """
### M7.4b 判据状态扩展（写于 M7 结果产出之前）

预注册的结局表只区分「H3 通过 / 不通过」。E1 的"不通过"实际含两种情况：**被推翻**
（有对照点且 QFP 更差）与**覆盖不足**（该码率点没有两族成员可比）。`m7_report.py`
因此把 H3 拆成 `pass / fail / under_covered / unmeasurable` 四态，并新增两个结局名
`local_coding_positive_dominance_untested` / `local_coding_negative_dominance_untested`。
扩展只会让结论更弱，H1/H2 的阈值一字未改。

### 判定回填：M7（2026-11-14 00:30）

`outcome = local_coding_negative_dominance_untested`。详见 `experiments/M7_RESULTS.md`。

- **H1 FAIL**：簇编码对全局网格，同字节覆盖率损失中位数 **+0.28 pp**（+0.04…+1.19），
  **8/8 资产同向**；阈值 2.0 pp，只达到 1/7。
- **H2 FAIL**：≥12× 且 `dPSNR ∈ [0, 0.3]`、损失 ≥−1.0 pp 的合格成员 **0/8**。
- **H3 覆盖不足**：只有 9×/12× 两点同时有两族；这两点 QFP 少丢 **+20.33 pp**（min
  +11.14）与 **+19.08 pp**（min +15.67），与 M5 的 E1 同量级。
- **机制**：`m16_o8_sh4` 7.50×/−0.45 pp → `c12_o8_sh4` 7.49×/−0.02 pp（位置换成簇
  之后几乎免费）；而 SH 3→2 bit 要从 −0.24 pp 掉到 −2.10 pp（stump −6.55 pp）。
  **7–13× 的约束是视图相关项的位宽，不是位置精度。**
- 教训进 N16：动作空间的上限由最贵的属性决定；判据必须做"网格 × 码率点"覆盖检查
  （M2、M7 两次踩同一个坑）；簇编码省模型字节多、省实测字节少。
"""
with io.open(P, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(TEXT)
print("appended", len(TEXT), "chars")
