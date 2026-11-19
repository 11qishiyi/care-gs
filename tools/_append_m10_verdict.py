"""Append N19 (M10) and the M10 verdict backfill."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

N19 = """
## N19 — 两级字典（残差 VQ）：方向对、幅度不够

**结论**：把 SH 块编成"粗中心 + 残差中心"（两本 k-means 码本，都按资产计费），
在实测字节轴上、18.9–21.0× 区间：
- 相对单级字典 **8/8 资产更好，中位 +0.42 pp**（bicycle +1.09、stump +1.32 最大）；
- 但绝对损失仍是 **−0.24 … −2.37 pp**，`≤1 pp` 只成立 **2/8**（bicycle_i7k −0.55、stump_i7k −0.89）；
- 15–25× "包络"判据 0/8 通过（中位 +0.22 pp），**该判据本身有设计缺陷**：
  两族各自取区间内最优点，却没有控制区间内的码率差，对手的最佳点总落在更高码率上。

**为什么又一次只前进半步**：M9（单级字典）已经证明"换表示"能赚 +1.48 pp；
M10 证明"换粒度"再赚 +0.42 pp。两者加起来仍不够把 19× 的损失压到 1 pp 以内。
**这说明 SH 的剩余误差不是均匀码率下的码本问题，而是"哪些基元该多花钱"的问题**：
差的基元（强方向瓣、薄结构、镜面）需要更多比特，而均匀码本无论单级两级都只能给平均量。

**教训**：
1. **残差级是对的**（8/8 为正），但收益 0.4 pp 量级——「更聪明的码本」这条线已经接近饱和。
2. **判据要控制混入变量**：L3 把"两族最优点"直接相减，等价于允许对手用更高码率换更好的点，
   这类判据在低斜率区必然判负；下一轮若要比较包络，必须**逐点插值到同一码率**再比
   （M5 的 `interp_points` 已经做过这件事，这里没有复用，是我的疏忽）。
3. **12× 的近无损在 18–20 B/基元的编码器上根本不可达**：位置 3–4 B、标量 8 B、SH ≥3 B
   已经把下限锁死；要 12× 必须动标量（M2 的 `o6` 已验证 6.2× 只付 0.36 pp，可组合）。

**数据**：`experiments/artifacts/a4/m10_rd.json`、`m10_bytes.json`、`m10_report.md`；
判定器 `experiments/m10_report.py`（L1/L2/L3 全 selftest）；代码在 `qfp_rd.quantize_rvq`、
`m4_bytes._codebook_pair`。
"""

BACK = """
### 判定回填：M10（2026-11-14 09:10）

`outcome = dead_write_N19`。L1 **FAIL**（12× 近无损 2/8：`bicycle_i7k` 19.57×/−0.55 pp、
`stump_i7k` 19.50×/−0.89 pp）；L2 **FAIL**（两级 vs 单级同字节：8/8 为正、中位 **+0.42 pp**，
但每资产 0.3 pp 门槛只过 5/8）；L3 **FAIL**（0/8，中位 +0.22 pp，判据未控制区间内码率差）。
结果全文见 `experiments/M10_RESULTS.md`，教训见 `APPENDIX_negative_results.md` N19。

**M9 + M10 的合并结论**（写论文要用的）：
- 单级字典 vs 逐系数：**+1.48 pp**（中位，8/8 为正）；
- 两级字典 vs 单级字典：**+0.42 pp**（中位，8/8 为正）；
- 两者都在 19× 附近把损失留在 **0.3–2.4 pp**，`≤1 pp` 只有 2/8；
- **严格口径的近无损前沿仍是 10.6×**（M8 的 `d2_c8_o8_sh4`）。
→ "更好的码本"这条线已饱和；下一轮应做**每基元编码模式选择**（字典/标量/置零 + 1 bit 标志）
与**标量降位组合**，这两件事是唯一还能同时降低 12× 门槛与 19× 损失的杠杆。
"""

with io.open(os.path.join(ROOT, "APPENDIX_negative_results.md"), "a",
             encoding="utf-8", newline="\n") as fh:
    fh.write(N19)
with io.open(os.path.join(ROOT, "experiments", "METHOD_PLAN.md"), "a",
             encoding="utf-8", newline="\n") as fh:
    fh.write(BACK)
print("ok")
