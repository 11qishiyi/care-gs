import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""1. **几何编辑致命，外观/精度编辑无害**：剪枝到 30% 使覆盖率下降 **11.4–20.6 个百分点**
   （4/4 场景，降幅是置信区间宽度的 2–4 倍）；而 SH 阶数 3→1 与 SH 8-bit 量化的变化都在噪声内（≤0.7pp）。""",
"""1. **几何编辑致命，外观编辑轻微，精度编辑无害**：剪枝到 30% 使覆盖率下降 **10.9–18.6 个百分点**
   （4/4 场景，400 次随机划分的配对区间全部排除零）；SH 阶数 3→1 只掉 **0.2–2.0pp**，
   SH 8-bit 量化则是 **0.00pp**。三层差距一个数量级。""")
io.open(p, "w", encoding="utf-8").write(s)
print("abstract synced with 3.2")
