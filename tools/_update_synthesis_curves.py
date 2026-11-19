"""Synthesis: add the matched-rate table and what it changes."""

import io

P = r"D:\3dsg_1\experiments\METHOD_SYNTHESIS.md"
s = io.open(P, encoding="utf-8").read()

anchor = "## 5. 前沿：多接近无损？"
add = """## 4b. 同码率曲线（`rd_curves.py`，五个独立 dump 合并，8 资产）

每个族只取它自己**真正扫过的那个旋钮**（剪枝率 `p*`、SH 位宽/带数 `c*_o8_sh*`、
字典宽度 `vq*`、两级字典 `rvq*`），逐资产插值到同一码率再取均值，**不外推**：

| 码率 | 剪枝 | 标量 SH | 单级字典 | 两级字典 | 最好的编码族 | 相对剪枝 |
|---|---|---|---|---|---|---|
| 12× | −24.59 | **−1.72** | — | — | 标量 SH −1.72 | **+22.87 pp** |
| 16× | −27.84 | **−3.37** | — | — | 标量 SH −3.37 | **+24.46 pp** |
| 18× | −29.46 | −4.42 | — | — | 标量 SH −4.42 | **+25.03 pp** |
| 20× | −31.08 | −4.54 | **−1.01** | −1.33 | 单级字典 −1.01 | **+30.07 pp** |

两条信息：
1. **同码率下编码族对剪枝的领先随码率上升而扩大**（12× 的 +22.9 pp → 20× 的 +30.1 pp），
   与"剪枝斜率更陡"一致；
2. **字典在 20× 上比标量 SH 好 3.5 pp**（−1.01 vs −4.54），这是 M9 机制结论在等码率轴上的复现；
   也就是说 18× 以上"该换成向量编码"，18× 以下标量 SH 仍然够用。

工具：`experiments/rd_curves.py`（`--json` 可重复、`--rates`、`--out`、`--selftest`）。
**没有覆盖的格子留空**（标量 SH 的阶梯在 5–11× 没有合格成员、字典族在 18× 以下没有成员），
不做任何外推。

""" + anchor
assert anchor in s
s = s.replace(anchor, add, 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
