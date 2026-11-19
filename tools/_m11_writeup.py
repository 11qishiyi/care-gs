"""Append N20 (M11 verdict) and backfill the M11 verdict into METHOD_PLAN."""
import io
import time

# ---- N20 -------------------------------------------------------------------
N = r"D:\3dsg_1\APPENDIX_negative_results.md"
s = io.open(N, encoding="utf-8").read()
assert "N20" not in s, "N20 already present"

n20 = """
### N20 — 每基元编码模式选择：调度救不了贴在一起的族（M11）

**问题**：M9（单级字典）与 M10（两级字典）都在 19× 上停在 0.3–2.4 pp，最好单点仍差 12× 近无损
门槛。它们的失败形状相同：一个**统一**的编码规则被强加给所有基元，而 SH 块的分布是长尾的
（大多数块接近 0，少数块很大）。M11 把规则下放：每个基元在 `ZERO / DICT / SCALAR` 之间自选，
选择依据是精确块误差加一个字节价格的拉格朗日项，模式标志 2 bit 计入文件。

**做了什么**：22 个变体 × 8 资产 × 400 splits，全部在**实测字节**轴上评估（zstd-12 ∘ Morton ∘
位平面打包），判据在数据落盘前预注册（P1 12× 近无损 ≥6/8、P2 同字节 ±10% 胜单族 ≥0.5 pp ≥6/8、
P3 18–20× 地板），网格在判定前按 M11.4b 扩充过一次（加 b_s∈{2,3} 的点，阈值一字未改）。

**结果**：`dead_write_N20`。P1 **5/8**（`bicycle`、`treehill`、`treehill_i7k` 缺）；P2 中位
**+0.56 pp** 但只 **4/8**；P3 `under_covered`（18–20× 只有 5 个资产有成员）。

**为什么失败——一条可以复用的机制**：
1. 选择器不是新族，它是**两个已有族的逐基元调度**，收益上限就是两族的差。满量程资产上
   `vq12` 与最优调度只差 **0.04 pp**（bicycle 19.84× vs 20.02×），因为 12-bit 码本在 5.26M
   基元上摊成 0.04 B/基元，字典本来就够好；调度无中生有不了精度。
2. 它**只**在"码本摊不薄"的资产上赢：四个 `_i7k` 双胞胎（基元少 40%）拿到 **+0.56…+4.05 pp**。
   同一套代码、同一套判据，收益从 0 跳到 4 pp，唯一的自变量是 `N`。
3. 字节价格参数 α 几乎惰性：同一 b_s 下 α 从 1 到 8 只挪 0.4 B。决定模式的是
   "标量能否把这块的误差压到 0"（b_s=4 时 26 B、b_s=2 时 14 B，字典 1.5 B），而不是价格。

**教训**：
- **先量"两族的差"，再决定要不要调度**。族间差距小于判据阈值时，任何调度器的上限都被钉死；
  这次如果先做一次两族在同一实测码率上的插值对照（`rd_curves.py` 已经能算），就能在租机前
  看到 0.04 pp 这个数，省下一整轮。
- **固定成本（码本）的摊薄程度是资产属性**，不是方法属性。任何"码本 + 索引"的那一类方法，
  其成立与否会随基元数移动；在 8 资产上按 6/8 计数，等于把"资产规模"这个隐藏变量当噪声。
- **判据与网格的覆盖矩阵要事前画**：M2、M7、M11 三次都是判据点落在网格外，三次都只能记
  `under_covered` 而不能给结论。这条已经写进 N16，仍未解决——解决办法是把覆盖矩阵作为
  预注册的**必填项**（每个判据 × 每个码率点标注"哪个变体覆盖它"）。
"""

with open(N, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(n20)
print("N20 appended", time.strftime("%H:%M:%S"))

# ---- METHOD_PLAN backfill --------------------------------------------------
P = r"D:\3dsg_1\experiments\METHOD_PLAN.md"
t = io.open(P, encoding="utf-8").read()
assert "判定回填：M11" not in t
mp = """
### 判定回填：M11（2026-11-14 13:15）

**结局 `dead_write_N20`**（P1 FAIL 5/8、P2 FAIL 4/8 中位 +0.56 pp、P3 `under_covered` 5/6）。
完整表格与机制见 `experiments/M11_RESULTS.md`，负结果见 `APPENDIX_negative_results.md` 的 N20。

三条对后续轮次的约束：

1. **先算族间差，再租机**。M11 的收益上限是 `vq12` 与最优调度之差，实测 0.04 pp（满量程资产），
   这一个数用 `rd_curves.py` 在 CPU 上就能算出来，不需要 GPU。
2. **资产规模是隐藏变量**。同一方法在 8 资产上 5/8、在 `_i7k` 上 4/4（+0.56…+4.05 pp）。
   以后按 6/8 计数时，必须同时报"按基元数分层的通过率"。
3. 本轮的工程遗留：`gsplat` 必须 `--no-deps` 装（否则 pip 拉 2.6 GB torch）并补 `rich`、
   `jaxtyping`、`ninja`；`matcli node exec` 的 70 分钟空闲限制会杀掉 `bytes` 的父进程，
   长任务要用 `experiments/m11_finish.sh` 这类守候脚本收尾。`run_m11.sh` 的 setup 已按此修正。
"""
with open(P, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(mp)
print("METHOD_PLAN backfilled")
