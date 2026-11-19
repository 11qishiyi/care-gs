import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()

# 1) the "drop is 2-4x the CI width" claim is wrong; recompute: 1.45-2.71
s = s.replace("区间较宽（最宽 ±0.056），但**降幅是置信区间宽度的 2–4 倍**，四个场景方向一致。\n扩大样本需要新的、带独立留出集的检查点来源，这是外部约束。",
"""区间较宽（最宽 ±0.056），但**降幅是置信区间宽度的 1.5–2.7 倍**，四个场景方向一致。

扩大样本的**正确**途径是把高密度模型扩到更多场景——Mip-NeRF 360 官方公开桶可达，
已下载 5 个额外场景；真正的瓶颈是训练器产不出"高密度且泛化好"的模型（§3.1a）。""")

# 2) inconsistent wording about external constraint in the abstract already fixed; check 3.1a table note
s = s.replace("对照四个发布检查点（3.1M–5.3M 基元，已收敛）：**−11.4 ~ −20.6pp**。",
              "对照四个发布检查点（3.1M–5.3M 基元，已收敛、17–20 dB 留出精度）：**−11.4 ~ −20.6pp**。")
io.open(p, "w", encoding="utf-8").write(s)
print("paper text corrected")
