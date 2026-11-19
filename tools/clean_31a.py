import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()

# 1) §3.1a: drop the stale interleaved compact numbers (-17.7..-20.6) and keep only the three-way table
s = s.replace("""| 场景 | 原始检查点 | **紧凑+微调模型** | 剪 30% 降幅 |
|---|---:|---:|---:|
| flowers | 3.13M | 0.28M（13.5 dB） | **−20.6pp** |
| bicycle | 5.26M | 0.32M（—） | **−19.9pp** |
| treehill | 3.37M | 0.39M（—） | **−20.4pp** |
| stump | 4.29M | 0.29M（—） | **−17.7pp** |

**四个场景、四个只有 280k–390k 基元的紧凑模型，降幅 −17.7 ~ −20.6pp**
（同场景短训练模型的对照是 −0.8 ~ +3.2pp）。

**一个只有 279k 基元、留出精度只有 13.5 dB 的模型，照样掉了 20.6 个百分点。**""",
"""紧凑模型的基元数与留出精度：flowers 0.28M / 13.5 dB、bicycle 0.32M、treehill 0.39M、stump 0.29M，
都远小于原始检查点（3.1M–5.3M）。它们的剪枝效应见下表（严格三分划分，见本节末）。""")

# 2) fix the stump mean in the three-way table (was mistyped as -7.3)
s = s.replace("| stump | 0.29M | **0.900** [0.876, 0.924] | 0.797 | **−7.3pp** [−11.6, −8.8] |",
              "| stump | 0.29M | **0.900** [0.876, 0.924] | 0.797 | **−10.3pp** [−11.6, −8.8] |")
s = s.replace("2. 剪枝后的降幅 **−10.3 ~ −12.9pp**", "2. 剪枝后的降幅 **−10.3 ~ −12.9pp**")

io.open(p, "w", encoding="utf-8").write(s)
print("3.1a cleaned: removed stale interleaved numbers, fixed stump mean")
