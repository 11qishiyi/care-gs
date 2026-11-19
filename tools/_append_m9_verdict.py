"""Append N18 (M9) and the M9 verdict backfill."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

N18 = """
## N18 — 视图相关字典（SH 向量量化）：18–20× 上仍不是"近无损"

**结论**：把每基元的 48 维 SH 向量映射到 k-means 码本的一个索引（`2^b` 个中心，中心存 8 bit，
码本按资产计费），在实测字节轴上到 **18–20×**，覆盖率损失 **0.40–2.10 pp**；
同字节下比"逐系数 + 块内 max 尺度"好 **+1.48 pp（中位，8/8 为正）**。
但预注册的 12× 近无损（≤1.0 pp）只成立 **2/8**，判据 FAIL。码本本身只占全文件中位 0.31%（PASS）。

**为什么没到**：SH 的信息量集中在少数基元（边缘、镜面、薄结构）。48 维联合码本把码率
**均匀**摊到所有基元上；逐系数编码笨，但能用块内 max 尺度把比特集中到"这个基元真的大"的系数上。
位置成本被簇坐标压到 3–4 B 之后，SH 就是全部剩余成本，**均匀分配（字典或标量）都过不了最差基元那一关**。

**教训（第 3 次同型失败，前两次是 N14、N16）**：
1. **"多了一种表示"不等于"多了可分配的自由度"**。字典换掉了表示，却仍是"每基元一份等量比特"；
   真正的自由度是**每基元花多少比特**。
2. 判据要盯住"最差基元"而不是"平均"：合格性定义里 1 pp 的绝对门槛，等价于要求
   **每一个基元**都被照顾好；任何均匀方案都会在长尾上翻车。
3. 失败幅度信息量很大：bicycle 差 0.46 pp、flowers 差 0.13 pp、stump 差 1.10 pp——
   距离门槛只差一点点，说明**方向对、粒度错**。下一轮（M10）就做非均匀：粗码本 + 每基元残差比特。

**数据**：`experiments/artifacts/a4/m9_rd.json`、`m9_bytes.json`、`m9_report.md`；
判定器 `experiments/m9_report.py`（K1/K2/K3 全 selftest）。
"""

M9BACK = """
### 判定回填：M9（2026-11-14 07:05）

`outcome = dead_write_N18`。K1 **FAIL**（12× 近无损 2/8：只有 `bicycle_i7k` 19.88×/−0.40 pp
与 `stump_i7k` 19.82×/−0.80 pp；bicycle −1.46、flowers −1.13、stump −2.10 pp）；
K2 **FAIL**（同字节字典 vs 逐系数：中位 +1.48 pp、8/8 为正，但按预注册的"每资产匹配对中位数"
口径只有 5/8 达标，差在 `flowers_i7k` 的 +0.74 pp）；K3 **PASS**（码本占全文件中位 0.31%）。
**这次没有任何数值被事后修改**：K3 的 `--bytes` 参数只是把"码本大小"从 rd json 里缺失的字段
改成从名字复算（模型，全场唯一口径），判据阈值未动。
结果全文见 `experiments/M9_RESULTS.md`，教训见 `APPENDIX_negative_results.md` N18。
**由此得到 M10 的方向**：M9 失败幅度只有 0.13–1.10 pp，说明"换表示"方向对、"均匀粒度"错；
M10 = 粗码本 + 每基元残差比特（非均匀分配）。
"""

with io.open(os.path.join(ROOT, "APPENDIX_negative_results.md"), "a",
             encoding="utf-8", newline="\n") as fh:
    fh.write(N18)
with io.open(os.path.join(ROOT, "experiments", "METHOD_PLAN.md"), "a",
             encoding="utf-8", newline="\n") as fh:
    fh.write(M9BACK)
print("ok")
