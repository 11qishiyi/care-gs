"""Append the M11 pre-registration: per-primitive mode selection."""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "experiments", "METHOD_PLAN.md")
TEXT = """
## M11 规格：每基元编码模式选择（MSC）

预注册时间 2026-11-14 09:35，**M11 数据落盘之前**（`/workspace/res/m11` 不存在，节点 2139541 已于 09:05 释放）。

### M11.0 动机：均匀码率这条线已经饱和

M9（单级字典 +1.48 pp）、M10（两级字典再 +0.42 pp）都在 19× 上把损失停在 **0.3–2.4 pp**，
`≤1 pp` 只有 2/8。同码率曲线（`rd_curves.py`）显示 20× 上字典比标量好 3.5 pp，
18× 以下标量更好。**也就是说，"最好的编码"取决于码率和基元本身**，而我们的每一族都强迫
所有基元用同一种编码。M11 允许每基元自己选：

- 模式 `DICT`：字典索引（`b_d` bit，两本码本按资产计费，复用 M10 的两级字典）；
- 模式 `SCALAR`：块内 max 尺度 + 每系数 `b_s` bit（复用 published 量化器）；
- 模式 `ZERO`：整块置零（0 bit，对多数近零基元几乎无损）。

每个基元 2 bit 模式标志（4 个码值，1 个保留）。选择规则是**拉格朗日**：
对每个基元算三种模式的平方误差 `D_m` 与字节 `c_m`，取 `D_m + λ·c_m` 最小者；
λ 扫描得到一条 RD 曲线（λ 越大越省）。**失真用 SH 块自身的精确平方误差**（不是重渲），
这是代理——P2 就是检验这个代理够不够。

### M11.1 字节模型

`bytes/prim = 8（标量 @8bit，或 6 @o6 变体）+ 3c/8 + 2/8（模式标志）+ Σ_m θ_m·c_m`
其中 `c_DICT = b_d/8 + (2^b1+2^b2)·48/N`，`c_SCALAR = 3K·b_s/8 + 2`，`c_ZERO = 0`。

### M11.2 变体（14 个，`--variant-set m11`）

- 锚点：`c8_o8_sh2`、`c8_o8_sh3`、`vq12_c8_o8`、`rvq10-4_c8_o8`；
- MSC 主族：`msc_<b_d>_<b_s>_l<λ码>`，`b_d∈{10,12}`、`b_s∈{4,6}`、λ ∈ {低,中,高} 三档；
- MSC + 标量降位：`msc_o6_10_4_l<λ>`、`msc_o6_12_6_l<λ>`（用 6 bit 的 9 个标量换 2 B 给 SH）；
- 低码率角落：`p30_msc_12_4_lhigh`。

### M11.3 判据

- **P1 近无损 ≥12×**：每资产存在成员（实测码率 ≥12×、覆盖率损失 ≥−1.0 pp、`0 ≤ dPSNR ≤ 0.3`），
  合格资产 **≥6/8**。这是 M7/M9/M10 三次都没拿到的那条。
- **P2 模式选择优于任何单一编码**：同码率（±10%）下 MSC 比 `scalar`/`vq`/`rvq` 三族中的**最好者**
  少丢 ≥0.5 pp，合格 **≥6/8**。
- **P3 高码率损失 ≤1.0 pp**：18–20× 区间内 MSC 的覆盖率损失 ≤1.0 pp 的资产 **≥6/8**。
- 结局：P1∧P2 → `msc_holds`；P2 只 → `msc_beats_families`；P1 只 → `frontier_only_msc`；都不 → 写 N20。
- 禁止条款：不得事后改 λ 档位、b_d/b_s 取值、±10% 窗、三条阈值；不得对 `dPSNR < 0` 的成员算合格；
  不得把模式标志或码本排除在字节之外。

### M11.4 执行

S0 本机自检（模式选择器单调性、字节账、λ 扫描单调、解析、判定器反例）。
S1 租 A40 → setup → push → `run_m11.sh`：dump 8 资产 × 14 变体 → `m11_bytes` 逐资产并发 →
`m1_analyse --bytes-json` → `m11_report.py` → 回传 → **立即释放**。预算 ~2 h ≈ ¥6。
"""
with io.open(P, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(TEXT)
print("appended", len(TEXT))
