"""Append the M8 pre-registration (band truncation + cluster positions at the high-rate
corner).  Written before any M8 data exists; the arithmetic comes from M5's *measured*
bytes and M3's band-truncation rows, not from M7's outcomes."""

import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "experiments", "METHOD_PLAN.md")
TEXT = """
## M8 规格：高码率角落——减阶 + 簇内位置（把近无损前沿推过 12×）

预注册时间 2026-11-13 23:50，**M8 数据落盘之前**（M8 变体尚未在任何节点上渲染，
`m8_rd.json` 不存在）。本节的动机只用到 M5 的**实测字节**与 M3 的减阶行，不引用 M7
的任何判定（M7 的 CPU 分析此刻仍在跑）。

### M8.0 动机：12× 处的位预算算术

M5 实测（bicycle）：`m16_o8_sh2` 模型 28 B → 实测 18.40 B（12.83×），而它的 PSNR 损失
在 flowers 上是 −1.27 dB——**在 12× 处，SH 的 2 bit 是维一的大项损失，位置和标量都已
经"免费"**。要把 12× 做进 0.3 dB，必须换一类杠杆：

| 目标 | 每基元字节上限（12×） | 位置 | 9 个标量 @8b | SH 可用 |
|---|---|---|---|---|
| 现状 `m16_o8_sh2` | 19.7 | 6.0 | 8.0 | 5.7（48 系数 ≈ 0.8 bit） |
| 减阶 `d1_*`（12 系数） | 19.7 | 3.1（c8） | 8.0 | 8.6 → 4 bit |
| 减阶 `d2_*`（24 系数） | 19.7 | 3.1（c8） | 8.0 | 8.6 → 2 bit |

也就是说：**在同样的字节下，"丢掉高阶带 + 保留低阶带的更多位" 比 "保留全部带、每带
1 位" 更省失真**——这正是 M3 的 E2（bits 胜 degree）在 25–45 B 窗口的反向情形，M8 就是
把 E2 搬到 15–25 B 的窗口里再问一次。M7 的簇内位置把位置项从 6.0 B 压到 3.1 B，是让这笔
算术成立的前提；两件事必须一起做。

### M8.1 变体（14 个，`--variant-set m8`）

`clean`；剪枝基线 `p30 p20 p10 p05`（3.3×–20×）；近无损锚点 `c8_o8_sh3`
`c10_o8_sh3` `c12_o8_sh2`；高码率候选 `d1_c8_o8_sh4` `d1_c10_o8_sh4` `d1_c8_o8_sh5`
`d2_c8_o8_sh4` `d2_c10_o8_sh3` `d1_c12_o8_sh4`；混合 `p50_d1_c8_o8_sh4`。

模型字节（K=16 场景）：`d1_c8_o8_sh4` = 3.094 + 8 + (12·4/8 + 2) = **19.09 B（12.36×）**；
`d1_c10_o8_sh4` = 19.84 B（11.90×）；`d1_c8_o8_sh5` = 20.59 B；`d2_c8_o8_sh4` =
3.094 + 8 + (24·4/8 + 2) = **25.09 B（9.41×）**；`d1_c12_o8_sh4` = 20.59 B。

### M8.2 判据

- **J1 近无损前沿 ≥12×（合格成员制）**：每资产存在成员满足 实测码率 ≥12×、
  绝对覆盖率损失 ≥ −1.0 pp、`dPSNR ≤ 0.3 dB` 且 `dPSNR ≥ 0`（沿用 M7 的合格性定义，
  再次排除靠归档 GT 曝光失配"提升"PSNR 的成员）；合格资产 ≥ 6/8。
- **J2 减阶优于降位（高码率窗口）**：在 15–25 B 的实测字节窗口内，`d*` 族最佳比
  `sh*`（全带低比特）族最佳少丢 ≥1.0 pp，正号资产 ≥ 6/8；若两者差 <1.0 pp 判等价
  （因为此窗口里 `sh` 族只有 1–2 bit，等价也是一种结论）。
- **J3 支配性延续**：符族对剪枝族在 `{5,7,9,12}×` 中 ≥4 点少丢 ≥3.0 pp、区间不含 0、
  ≥6/8 资产同向（E1 原样重放）。
- 结局：J1∧J2 → `high_rate_near_lossless_holds`（可写"12× 近无损"的标题级结论）；
  J1 只 → `frontier_only`；J2 只 → `degree_beats_bits_at_high_rate`；都不 → 写 N17。
- 禁止条款：不得事后改 12×/1.0 pp/0.3 dB 的门、不得改 15–25 B 窗口、不得删掉
  失败的资产、不得把 `dPSNR < 0` 的成员算作合格。

### M8.3 执行

`--variant-set m8` 已加入 `qfp_rd.py` 与 `m1_analyse.py` 的语法（`d<k>_c<bits>_...`，
两处字节模型由 `m1_check_bytes.py` 比对）。先在当前节点 2139436 上跑 dump（8 资产 ×
14 变体，无感知指标，约 20 min）→ `m4_bytes --skip-flat` → `m1_analyse --bytes-json
--protocol m3` → `m8_report.py` → 回传 → 释放节点。
"""
with io.open(P, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(TEXT)
print("appended", len(TEXT), "chars")
