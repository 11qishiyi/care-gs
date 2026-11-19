"""Append the M8 verdict to METHOD_PLAN.md and the N16/N17 entries to the appendix."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP = os.path.join(ROOT, "experiments", "METHOD_PLAN.md")
APP = os.path.join(ROOT, "APPENDIX_negative_results.md")

MP_TEXT = """
### 判定回填：M8（2026-11-14 01:10）

`outcome = dead_write_N17`。详见 `experiments/M8_RESULTS.md`。

- **J1 FAIL**：≥12× 且（损失 ≥−1.0 pp、`dPSNR ∈ [0,0.3]`）的合格成员只有 **2/8** 资产
  （`bicycle_i7k` `d2_c10_o8_sh3` 12.50×/−0.48 pp/+0.101 dB；`stump_i7k` 12.41×/−0.69
  pp/+0.094 dB）。
- **J2 FAIL**：15–25 B 窗口内减阶减损中位数 **+0.08 pp** → 判**等价**，`bicycle` 甚至
  −1.48 pp。与 M3 的 E2（降位胜、−0.53 pp、6/8）方向一致，说明**带数不是杠杆**。
- 最好单点：`d2_c8_o8_sh4` 在 8/8 资产落在 10.3×–11.1×、损失 −0.16…−1.80 pp、
  PSNR 与 clean 持平或更好 —— 近无损前沿从 M7 的 ~9× 挪到 **~10.6×**，但没到 12×。
- 教训进 N17：减阶"看起来省字节"（少 36 个系数）但表达力掉得更快；`d1_*` 在 12–15×
  反而崩到 −1.7…−3.6 pp；PSNR 在低比特 SH 上会因归档 GT 失配而"假提升"，合格性条款
  必须排除 `dPSNR < 0`。
"""

APP_TEXT = """
### N16 — 局部（簇相对）位置编码：方向对，幅度不够（M7）

**做法**：按 Morton 序把基元切成 256 个一块，每块自带 3 分量原点与步长（24 B/块），块内
偏移量化到 `c` bit（6–24），取代场景级全局网格；解码端由重建位置的 Morton 码复算块序，
无索引流。

**结果**（8 资产 × 18 变体，实测字节轴：位平面打包 + Morton + zstd-12，400 splits）：
- 同字节下簇编码**每次都赢**（8/8），但只赢 **+0.04…+1.19 pp**（中位 +0.28 pp），
  预注册门槛是 +2.0 pp → H1 FAIL。
- ≥12× 且 `dPSNR ∈ [0, 0.3]` 的合格近无损成员 **0/8** → H2 FAIL。
- 支配性重放只剩 9×/12× 两个码率点（网格没覆盖 5×/7×）→ H3 覆盖不足；这两点上 QFP
  分别少丢 +20.33 pp / +19.08 pp。

**为什么幅度这么小**：位置项一旦换成局部坐标就几乎免费（`c12_o8_sh4` 7.49× 只付
−0.02 pp），于是 7–13× 的约束换成了**视图相关项的位宽**（SH 3→2 bit 要付 1.86 pp，
stump 6.55 pp）。**一个动作空间的上限由最贵的属性决定，不由最便宜的那个决定**——这是
A 系列到 M 系列反复踩的同一条。

**教训**：①判据必须配"网格 × 码率点"覆盖矩阵（M2、M7 两次因覆盖不足而无法测量）；
②簇编码省的是**模型字节**，实测只省约 1.6 B（全局 16 bit 位置在 Morton 序下已被 zstd
压得很好）；③"换坐标"能修精度，但修不了错的位置——错在 SH。

### N17 — 减阶 vs 降位：带数不是杠杆（M8）

**做法**：把 M3 的 E2（25–45 B 窗口，降位胜）搬到 15–25 B 窗口：`d1_*/d2_*`（丢高阶带、
给留下的系数更多位）对 `sh2/sh3`（全带低比特），配合 M7 的簇位置。

**结果**（8 资产 × 15 变体，实测字节轴）：
- J2：同窗口内减阶比全带低比特**中位只多 +0.08 pp**（判等价），`bicycle` 甚至 −1.48 pp
  → 减阶不是杠杆。
- J1：合格近无损 ≥12× 只有 2/8 资产 → 前沿停在 **~10.6×**（`d2_c8_o8_sh4`：8/8 资产
  10.3–11.1×、损失 −0.16…−1.80 pp）。
- `d1_*` 在 12–15× 崩到 −1.7…−3.6 pp：degree 1 只有 12 个系数，每系数给到 4–5 bit 也
  不如 48 系数 2 bit。

**教训**："少存系数"看起来省字节（少 36 个系数 = 省 18 B），但表达力掉得更快；而且在
归档 GT 的曝光失配下，低比特 SH 会**假提升** PSNR（flowers `d1_*` dPSNR −1.18 dB，
treehill 全场景 clean 只有 9.41 dB），任何"近无损"判据都必须要求 `dPSNR ≥ 0`，否则会把
指标缺陷当成方法收益。
"""

for path, text, marker in ((MP, MP_TEXT, "判定回填：M8"), (APP, APP_TEXT, "N16 — 局部")):
    s = io.open(path, encoding="utf-8").read()
    if marker in s:
        print("already present in", path)
        continue
    with io.open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("appended to", path)
