"""M8 amendments, written while the M8 dump is still running (no M8 number has been read).

1. Variant count fix: M8.1 listed 15 names but said 14.
2. J3 is replaced by "report M5's E1": M8's grid deliberately covers only the high-rate
   corner (7x-13x measured), so evaluating the 5x/7x dominance points again would repeat
   the M2 mistake (a criterion whose rate points fall outside the grid's byte range).
   Dominance over 5x-12x is already established by M5's E1 replay (8/8 assets at four
   points); M8 does not re-litigate it.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "experiments", "METHOD_PLAN.md")
TEXT = """
### M8.4a 修订（2026-11-14 00:20，M8 数据落盘之前）

写此修订时 M8 的 dump 正在跑（`/workspace/res/m8/dump/` 已有 7 个 npz，日志停在
`=== flowers_i7k ===`），**尚未读出任何 M8 的 PSNR / 覆盖率 / 字节数字**，也没有
`m8_rd.json`。

1. **变体数**：M8.1 的清单实为 **15** 个（clean 1 + 剪枝 4 + M7 锚点 3 + 高码率候选 6
   + 混合 1），原文写的 14 是笔误。
2. **J3 不再单独评估**：M8 的网格刻意只覆盖高码率角落（实测约 7×–13×），把 5×/7× 的
   支配点再评一遍必然落在网格的字节区间之外——这正是 M2 被判假阴性、M7 的 E1 只剩
   2/8 个码率点的同一个错误。支配性（5×–12×、8/8 资产、每点多丢 ≥3 pp）已由 M5 的
   E1 重放确立，M8 引用它，**不再重新测量**，因此 M8 的结局只由 J1、J2 决定：
   | J1 | J2 | 结论 |
   |---|---|---|
   | ✔ | ✔ | `high_rate_near_lossless_holds` |
   | ✔ | ✘ | `frontier_only` |
   | ✘ | ✔ | `degree_beats_bits_at_high_rate` |
   | ✘ | ✘ | `dead_write_N17` |
3. J1、J2 的阈值（12×、−1.0 pp、0.3 dB、`dPSNR ≥ 0`、15–25 B 窗口、1.0 pp 等价带）
   **一字不改**。
"""
with io.open(P, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(TEXT)
print("appended", len(TEXT), "chars")
