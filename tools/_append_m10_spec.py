"""Append the M10 pre-registration: two-stage (residual) dictionary for the SH block."""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "experiments", "METHOD_PLAN.md")
TEXT = """
## M10 规格：两级字典（残差向量量化）

预注册时间 2026-11-14 07:20，**M10 数据落盘之前**（`/workspace/res/m10` 不存在，
节点 2139512 已于 06:20 释放，尚未租新节点）。

### M10.0 动机：M9 差的是粒度，不是表示

M9 判负，但幅度很小：12× 近无损差 0.46 pp（bicycle）、0.13 pp（flowers）、1.10 pp（stump），
而单级字典在同字节下已经比逐系数好 +1.48 pp（中位，8/8 为正）。诊断是**粒度**：
一个共享中心要同时服务"有强方向瓣的基元"和"几乎恒定的基元"。
两级字典把同样的比特拆成"粗中心 + 局部残差"：第二本码本在**第一级的残差上**训练，
中心自然落在第一级系统性出错的地方。这是神经压缩里的标准做法（RVQ），在 3DGS 上还没人做过。

### M10.1 编码器

- 第一级：`2^b1` 个 48 维中心（8 bit 存储），每基元存 `b1` bit 索引；
- 第二级：在残差 `v_i − C1[a1_i]` 上训练 `2^b2` 个中心，存 `b2` bit 索引；
- 重建：`v̂_i = C1[a1_i] + C2[a2_i]`；码本按资产计费（两本都算）。
- 字节模型：`bytes_sh = (b1+b2)/8 + (2^b1 + 2^b2)·48 / stored`。
- 组合：`bytes/prim = 8（9 标量@8bit）+ 3c/8（簇位置）+ bytes_sh`。

### M10.2 变体（16 个，`--variant-set m10`）

`clean`；锚点 `c8_o8_sh2`(13.84 B, 17.0×)、`c8_o8_sh3`(31.1 B)、`vq10_c8_o8`(12.35 B, 19.1×)、
`vq12_c8_o8`(12.63 B, 18.7×)；残差阶梯 `rvq6-2`(8 bit)、`rvq8-2`(10)、`rvq8-4`(12)、
`rvq10-2`(12)、`rvq10-4`(14)、`rvq8-6`(14)、`rvq12-4`(16)、`rvq10-6`(16)（均 `_c8_o8`）；
位置对照 `rvq8-4_c10_o8`、`rvq10-4_c10_o8`；低码率点 `p30_rvq10-4_c8_o8`。

### M10.3 判据

- **L1 近无损前沿 ≥12×**（与 K1 同定义：实测码率 ≥12×、覆盖率损失 ≥−1.0 pp、
  `0 ≤ dPSNR ≤ 0.3`），合格资产 **≥6/8**。这是 M9 唯一没拿到的那条。
- **L2 两级胜过单级**：同字节（±10%）下 R VQ 比**单级字典**（`vq*`）少丢 ≥0.3 pp，
  每资产取最佳配对，达标 **≥6/8**。
- **L3 包络**：15–25× 区间内，RVQ 族的最佳点比所有非 RVQ 变体（标量/单级字典/剪枝）的
  最佳点少丢 ≥1.0 pp，达标 **≥6/8**。
- 结局：L1∧L2 → `rvq_holds`（可写"12× 近无损"）；只有 L2 → `rvq_beats_single_stage`；
  只有 L1 → `frontier_only_rvq`；都不 → 写 N19。
- 禁止条款：不得事后改 b1/b2 集合、±10% 窗、L1/L2/L3 阈值、k-means 迭代数与种子；
  不得对 `dPSNR < 0` 的成员算合格；不得把码本排除在字节之外。

### M10.4 执行

S0 本机自检（qfp_rd / m4_bytes / m1_analyse / m1_check_bytes / m10_report 全绿）。
S1 租 A40 → setup（重下 9587304864 B）→ push → `run_m10.sh`：dump 8 资产 × 16 变体
（含两级 k-means）→ `m10_bytes` 逐资产并发（`--skip-flat`）→ `m1_analyse --bytes-json` →
`m10_report.py` → 回传 → **立即释放**。预算 ~2 h ≈ ¥6。
"""
with io.open(P, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(TEXT)
print("appended", len(TEXT))
