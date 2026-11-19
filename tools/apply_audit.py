import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()

# 1) Related work: lead with AURA and draw the division of labour
s = s.replace("""## 4. 相关工作定位

- **AURA / VSCP** 给出 3DGS 的保形界，但都要求每次编辑后重新标定；本文测量"不重新标定会怎样"，
  并进一步指出**即使重新标定，覆盖率这个指标本身也不足以反映真实损失**。""",
"""## 4. 相关工作定位

**最接近的工作是 AURA**（Attri, 2026；engrxiv DOI 10.31224/7689）：它给每个基元一个校准的可靠性标签，
用分裂保形给出**剪枝证书**并扩展成认证的 LoD 阶梯，交付到 glTF/USD/SPZ，
并用 selection AUC 证明校准置信度剪枝优于 opacity（0.58–0.72 vs 0.37–0.53）。

**分工是清楚的**：AURA 解决*如何签发一个可信证书*；本文问的是*证书签发之后会发生什么，
以及证书这个指标本身够不够*。前者假定资产按证书指定的方式使用，本文测量的正是这个假定被打破的情形。
因此在 §3.5(c) 关于剪枝准则的结论上，本文不是首次发现，而是**在覆盖率指标上复现了 AURA 在可靠性指标上的观察**。

- **VSCP**（arXiv 2609.10307）把保形区间按视图结构因子化以降低区间宽度，是"把证书做得更紧"；
  与本文"证书会不会失效"互补。
- **Manifold-GS**（arXiv 2608.00214）的 "certified" 指几何/拓扑认证（varifold 质量守恒、开曲面片导出），
  与本文的渲染误差覆盖保证是两种不同含义，需在同一句里澄清。
- **Dong & Li**（Pattern Recognition 180:114249, 2026）对多视图重建的深度做保形校准，
  作用于重建阶段而非资产编辑之后。
- **"代理指标不能预测下游任务"** 这一现象在几何视觉中已被一般性讨论（Lacuna, 2026 研究笔记）；
  本文给出它在 3DGS 资产审计中的**定量形式**（1.9–12.1 倍）与机制解释。
- **"证书会因假设改变而失效"** 在 AI assurance 文献中是已知原则（如 assumption-bound certificate leases）；
  本文的贡献不是提出该原则，而是**在 3DGS 上量化它**。""")

# 2) §3.5(c): downgrade the wording from "our finding" to "replication"
s = s.replace("**（c）如果非要剪枝，选对准则。** 同样 30% 预算，只改选择准则：",
              "**（c）如果非要剪枝，选对准则。** 同样 30% 预算，只改选择准则"
              "（这一方向与 AURA 在可靠性指标上的观察一致，这里给出它在覆盖率指标上的形式）：")

# 3) abstract: cite the conceptual precedent for claim 2
s = s.replace("""   覆盖率只问"误差是否越过阈值"，而下游任务对阈值以下的**排序变化**同样敏感。""",
"""   覆盖率只问"误差是否越过阈值"，而下游任务对阈值以下的**排序变化**同样敏感。
   "代理指标不能预测下游任务"在几何视觉中已被一般性讨论，本文给出它在 3DGS 资产审计中的定量形式。""")
io.open(p, "w", encoding="utf-8").write(s)
print("related work + wording updated")
