import io

Q = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(Q, encoding="utf-8").read()
old = '''    # buy back 2 B from the nine scalars and spend it on SH
    "msc12-4-a1_c8_o6", "msc12-6-a4_c8_o6",
    # low-rate corner
    "p30_msc12-4-a1_c8_o8",
])'''
new = '''    # buy back 2 B from the nine scalars and spend it on SH
    "msc12-4-a1_c8_o6", "msc12-6-a4_c8_o6",
    # M11.4b: the realised mixes at 4-6 bits per scalar coefficient land at 5-8x,
    # because a scalar-coded primitive then costs 26-38 B and the selector almost
    # always pays it.  The 12-20x region the criteria live in needs 2-3 bit scalars.
    "msc12-2-a2_c8_o8", "msc12-2-a4_c8_o8", "msc12-2-a8_c8_o8",
    "msc12-3-a1_c8_o8", "msc12-3-a4_c8_o8", "msc10-2-a2_c8_o8",
    "msc12-2-a2_c8_o6",
    # low-rate corner
    "p30_msc12-4-a1_c8_o8",
])'''
assert old in s
io.open(Q, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("M11_VARIANTS extended")

P = r"D:\3dsg_1\experiments\METHOD_PLAN.md"
t = io.open(P, encoding="utf-8").read()
assert "M11.4b" not in t
note = """
### M11.4b 网格修订（2026-11-14 10:20，dump 日志已出、分析判定尚未运行）

`dump` 的逐变体一行结果（n、B/prim、倍率、PSNR）在落盘时就打印，因此下面这条修订写在
**任何判据被计算之前**，且不改动任何阈值：

**观察到的事实（不是结论）**：在已注册的 15 个变体里，`b_s ∈ {4,6}` 的选择器变体全部落在
**4.98x–8.06x**（例如 bike `msc12-4-a1_c8_o6` 34.3 B = 6.89x、`msc12-6-a4_c8_o6` 46.7 B =
5.05x），而在 `b_s = 2` 的那一个点上是 **18.18x**（treehill，13.0 B）。机制是算术的：一个
标量编码基元要付 `3K·b_s/8 + 2` 字节，b_s=4 时是 26 B、b_s=2 时是 14 B，而字典编码只要
1.5 B；既然标量路径能把该基元的块误差降到 0，选择器在 λ 归一化下几乎总会买它。

**因此原网格覆盖不到 P1（≥12x）与 P3（18–20x）所在的码率区间**——这与 M2、M7 的
"判据与网格不匹配"是同一个失败模式。按 M7.4b 的先例，补救只能靠**扩充网格**，不能靠
事后改判据。新增 7 个变体（全部是已注册语法内的点，b_s ∈ {2,3}，α ∈ {2,4,8}）：

| 变体 | 模型 B/prim | 说明 |
|---|---|---|
| `msc12-2-a2_c8_o8` | 12.88* | 2-bit 标量 + 字典，α=2 |
| `msc12-2-a4_c8_o8` | 12.88* | 同上，α=4（字节更贵 → 更多字典） |
| `msc12-2-a8_c8_o8` | 12.88* | 同上，α=8 |
| `msc12-3-a1_c8_o8` / `msc12-3-a4_c8_o8` | 12.88* | 3-bit 标量，两端 α |
| `msc10-2-a2_c8_o8` | 12.60* | 更窄字典 |
| `msc12-2-a2_c8_o6` | 10.88* | 再省 2 B 标量 |

\\* 同样用全字典回落值；真实倍率仍由实测字节给出。**判据本身一个字都没改**：P1 仍是
≥12x 且损失 ≤1.0 pp 且 `0 ≤ dPSNR ≤ 0.3`，P2 仍是同字节 ±10% 内 ≥0.5 pp，P3 仍是
18–20x 内 ≤1.0 pp，结局表与禁止条款同前（M11.4a 已声明 P1/P3 可记 `under_covered`）。
新增的 7 个点让网格从 4.98x–21.8x 变成 **4.98x–21.8x 且中段（12–20x）有 10 个点**。
"""
with open(P, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(note)
print("M11.4b appended")
