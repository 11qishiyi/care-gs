"""Append the M9 pre-registration: vector-quantised SH (a view-dependent dictionary)."""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "experiments", "METHOD_PLAN.md")
TEXT = """
## M9 规格：SH 向量量化（视图相关字典）

预注册时间 2026-11-14 01:20，**M9 数据落盘之前**（节点 2139436 已于 01:12 释放，
尚未租新节点，`/workspace/res/m9` 不存在）。

### M9.0 动机：瓶颈已被定位到 SH，而 SH 一直是"逐系数编码"

M7 与 M8 把 7–13× 的约束压到了视图相关项上：
- 位置换成簇坐标后几乎免费（`c12_o8_sh4` 7.49× 只付 −0.02 pp）；
- 9 个标量 @8 bit 全免费（M2 的 `iso_*` 族，0.00–0.02 pp）；
- 而 SH 3→2 bit 要付 1.86 pp（stump 6.55 pp），减阶（保留更少带、给更多位）**不划算**
  （M8 的 J2：中位 +0.08 pp，判等价）。

到目前为止 SH 一直是**逐基元逐系数**编码（每基元自己的块内 max 尺度 + 每个系数独立量化），
48 个系数的联合冗余完全没被利用。但 SH 块之间高度冗余：大量基元的 3–15 阶系数接近 0，
同类材质/法向的基元共享几乎相同的角度曲线。**这正是向量量化（VQ）擅长的事**：
把一个基元的 48 维 SH 向量映射到码本里的一个索引。

### M9.1 编码器

- 输入：每基元的 48 维 SH 向量 `v_i`（`sh0` 3 维 + `shN` 45 维，按系数顺序拼接）。
- 码本：`2^b` 个中心（b ∈ {6,8,10,12,14}），用 minibatch k-means（固定种子、固定迭代数）
  在该资产**自己的** checkpoint 上训练；中心量化到 8 bit（每中心 48 B），码本按资产计费。
- 每个基元存 `b` bit 索引；解码时 `v_i ← centroid[code_i]`。
- 字节模型（替代 `3K·b_sh/8 + 2`）：`bytes_sh = b/8 + (2^b · 48) / stored`。
  例：b=12、5.26M 基元 → 1.5 B + 0.037 B = 1.54 B（对比逐系数 3 bit 的 20 B、2 bit 的 14 B）。
- 与 M7 的簇位置（`c` bit）和 8 bit 标量组合：`bytes/prim = 8 + 3c/8 + b/8 + codebook/stored`。

### M9.2 变体（12 个，`--variant-set m9`）

`clean`；锚点 `c10_o8_sh3`（9.3×）、`c12_o8_sh2`（12.8×）；VQ 主族
`vq8_c8_o8`、`vq10_c8_o8`、`vq12_c8_o8`、`vq14_c8_o8`、`vq10_c10_o8`、`vq12_c10_o8`、
`vq12_c12_o8`；VQ + 减阶对照 `d2_vq12_c8_o8`；混合 `p30_vq12_c8_o8`。

### M9.3 判据

- **K1 近无损前沿 ≥12×**：每资产存在合格成员（实测码率 ≥12×、覆盖率损失 ≥−1.0 pp、
  `dPSNR ≤ 0.3 dB` 且 `≥ 0`；合格性定义与 M7/M8 完全相同）；合格资产 ≥6/8。
- **K2 VQ 胜过逐系数编码**：同字节（±15% 匹配窗）下 VQ 族比逐系数族少丢 ≥1.0 pp，
  正号资产 ≥6/8。
- **K3 字典本身要付账**：把码本字节计入（已计入模型与实测两条路径），并在报告里单独列出
  码本占全文件的比例；**禁止**用"码本不算字节"的口径报告任何码率。
- 结局：K1∧K2 → `vq_dictionary_holds`（可写"12× 近无损"）；K1 只 → `frontier_only_vq`；
  K2 只 → `vq_beats_scalar_only`；都不 → 写 N18。
- 禁止条款：不得事后改 b 的取值集合、k-means 迭代数/种子、±15% 窗、K1/K2 阈值；
  不得对 `dPSNR < 0` 的成员算合格；不得用未量化码本报告码率。

### M9.4 执行

S0 本机自检（k-means 收敛与码本一致性、字节账、解析、报告器反例）。
S1 租 A40 → setup（重下 9587304864 B 归档）→ push → `run_m9.sh`（dump 8 资产 × 12 变体
  含 VQ 训练，约 30 min；`m4_bytes --skip-flat`；`m1_analyse --bytes-json`）→
  `m9_report.py` → 回传 → **释放节点**。预算 ~1.5 h ≈ ¥5。
"""
with io.open(P, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(TEXT)
print("appended", len(TEXT), "chars")
