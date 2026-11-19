import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()

old_start = s.index("**最接近的工作是 AURA**")
old_end = s.index("- **VSCP**（arXiv 2609.10307）")
new = """**最接近的工作是 AURA**（Attri, 2026；engrxiv DOI 10.31224/7689）：它把导出时可算的
train-view 颜色一致性用等渗（PAVA）校准成逐基元可靠性，再用分裂保形给出剪枝证书，
并扩展成**认证的 LoD 阶梯**（消费者可在任一已发布层级停止，得到丢弃可靠性质量的 family-wise 界）；
在四个场景（Truck / Garden / Kitchen / Room，约 11–13 万基元、留出标注视角 24–35 个）上，
selection AUC 为 0.58–0.72，优于 opacity 的 0.37–0.53。

**分工是清楚的，而且是互补的。** AURA 的证书绑定在**它自己的阈值剪枝准则与预设 LoD 层级**上，
解决的是*如何签发一个可信证书、并让它在阶梯内持续有效*。本文问的是另一个问题：
*证书被带到阶梯之外时会发生什么*——消费者用**自己的准则**剪枝、或做证书未覆盖的编辑
（合并、SH 降阶、微调）。据我们对 AURA 全文的检索，edit / modify / re-certify / recalibrate / invalidate
在文中均未出现，因此本文测量的正是它框架的边界之外。

两个设置上的差异值得说明，因为它们决定了结论的适用范围：
(i) AURA 评估的是约 11–13 万基元的压缩资产，本文主表用 3.1M–5.3M 的发布检查点，
但附录 A 表明 0.2M–0.4M 的紧凑模型同样出现效应，因此结论不依赖模型规模；
(ii) AURA 每场景有 24–35 个留出标注视角，本文只有 16–25 个（受归档可提供的测试视角数限制），
这也是本文区间较宽的直接原因。

因此在 §3.5(c) 关于剪枝准则的结论上，本文不是首次发现，而是**在覆盖率指标上复现了 AURA 在可靠性指标上的观察**。
本文相对 AURA 的独有测量是：编辑后的证书失效幅度、重签成本、以及**覆盖型证书与下游任务损失之间的落差**。

"""
s = s[:old_start] + new + s[old_end:]

# add the setup-comparability note into limitations
s = s.replace("""3. **区域粒度影响绝对数值**（附录 C）：3D 体素区域上的降幅比图像块小 3–4 倍。""",
"""3. **区域粒度影响绝对数值**（附录 C）：3D 体素区域上的降幅比图像块小 3–4 倍。
4. **与 AURA 的设置差异**：它评估约 11–13 万基元的压缩资产、每场景 24–35 个留出标注视角；
   本文用 3.1M–5.3M 的发布检查点、16–25 个留出视角。前者影响模型规模，已在附录 A 用紧凑模型对照覆盖；
   后者影响区间宽度，是数据提供的视角数决定的。""")
io.open(p, "w", encoding="utf-8").write(s)
print("related work rewritten with verified AURA facts")
