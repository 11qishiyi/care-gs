# 全网相关工作调研（2026-11-11）

> 对象：`submission/final/main.pdf`（"Valid but Unusable: What Coverage Certificates Miss When 3DGS Assets Are Edited"）
> 问题：全网是否已有与我们同题/近题的工作？
> 检索渠道：arXiv API（9 组查询，按提交日期倒序，取近 20 条/组）、OpenAlex（7 组宽检索）、
> Semantic Scholar、DSH `awesome-gaussian-skills` 知识库（1066 条方法 / 26 类，快照 2026-11-06）、
> Crossref（DOI 解析）、CVF Open Access、Semantic Scholar 元数据。
> 检索时间：2026-11-11 19:30–20:05 (Asia/Shanghai)。

## 一、结论

1. **没有同题论文**：在 arXiv、OpenAlex 与插件 1066 条方法索引中，**没有**任何工作同时做
   "签发后的编辑对保形/覆盖率证书的影响" + "覆盖率与下游任务排序是否一致" 这两件事。
2. **有一篇概念上最近的**：`Doula & Mühlhäuser 2026`（arXiv:2610.28937）把
   "推理配置变化（量化模式、serving 温度）导致的 conformal score 分布漂移" 形式化为
   **inference-time model shift**，并证明它在模型与任务都不变时就会破坏 split-conformal 交换性。
   对象是语言模型、编辑是推理配置、度量是覆盖率；与本文的 3DGS 资产参数改写、逐像素渲染覆盖、
   外加任务解耦不同。**必须引用**，否则审稿人会认为我们不知道"模型漂移破坏 CP"这一支。
3. **第二篇概念近邻**：`Usama & Qadir 2026`（arXiv:2611.04192）用 declared change envelopes
   认证"模型更新只在声明的区域内改变了行为"。它认证的是"改动位置"，我们测量的是"证书失效幅度"。
   引用一句话即可。
4. **3DGS 证书方向本身只有三篇**：VSCP（arXiv:2609.10307）、Manifold-GS（arXiv:2608.00214）、
   AURA（engrXiv 10.31224/7689）——都已在我们的相关工作里，且都不测量编辑后失效与任务解耦。
5. **术语"certified"在 3DGS 里被多种含义占用**（几何/拓扑保证、全局最优性、per-carrier 可靠性），
   本文用 XM4D（arXiv:2611.07902）再补一个"certifiable = 全局最优"的例子，避免读者把"certified"
   误读成"覆盖率保证"。
6. **感知质量评估是一支独立文献**（3DGS-VBench+、GS-PQM、GScomp-QA 等），审稿人可能问"为何不用
   感知指标"。已加一段说明两者对象不同：感知分数是资产之间的排序，证书是单个资产的逐像素错误率界。
7. 因此：**贡献边界成立**，但需要（且已完成）四类引用补强：模型漂移 CP、声明式更新认证、
   可证明剪枝、感知质量。

## 二、分层清单

### A. 证书 / 保形（与本文同一对象）

| 工作 | 出处 | 做了什么 | 与本文重叠 | 威胁 | 处理 |
|---|---|---|---|---|---|
| VSCP | arXiv:2609.10307（2026-09） | view-structured conformal，按视角分解尺度，收紧区间 | 同为 3DGS 的 split-conformal 覆盖 | 低（互补） | 已引；描述"tighten the interval by factorising scale over views" |
| Manifold-GS | arXiv:2608.00214（2026-07） | "certified" 指几何/拓扑（varifold-conservative） | 同为"certified asset"，不同保证 | 低 | 已引；写明"not rendering error" |
| AURA | engrXiv 10.31224/7689（2026-07） | per-carrier 可靠性 + isotonic 校准 + certified LOD 阶梯 | 同族证书、同族剪枝 | 中（最近的正面近邻） | 已引，含 AUC/场景数/exchangeability 提醒逐项核对 |
| XM4D | arXiv:2611.07902（2026-11） | certifiably globally optimal 的 4D 几何优化 | 只共享 "certified" 一词 | 低 | 新增引用（术语区分） |
| **本文** | — | 编辑后证书失效幅度 × 剂量曲线 × 四族任务解耦 | — | — | — |

### B. 模型更新 / 模型漂移下的证书（概念最近）

| 工作 | 出处 | 做了什么 | 与本文重叠 | 威胁 | 处理 |
|---|---|---|---|---|---|
| Doula & Mühlhäuser | arXiv:2610.28937（2026-10） | 形式化 inference-time model shift；量化/温度改变分数分布即破坏交换性；主张审计协议 | **"编辑模型 → 证书失效"的同一逻辑**，对象是 LLM | **中高（概念）** | 新增引用；写明对象/编辑/度量差异，并用"8-bit SH 量化 0.0 点"说明"是否失效是定量问题" |
| Usama & Qadir | arXiv:2611.04192（2026-11） | declared change envelopes + anytime-valid 检验，认证更新只在声明区域改变行为 | 同为"更新后的证书"，认证对象是行为泄漏 | 低中 | 新增引用（一句话） |

### C. 压缩 / 剪枝（本文的编辑算子与基线）

| 工作 | 出处 | 与本文关系 | 处理 |
|---|---|---|---|
| PUP 3D-GS | CVPR 2025 | 本文三准则之一（Fisher 对角） | 已引，补页码 |
| LightGaussian | NeurIPS 2024 | 全局重要性剪枝 + 蒸馏 + VQ | 已引（本轮修正标题/发表处） |
| EAGLES | ECCV 2024 | 量化嵌入 + 由粗到细 + 剪枝 | 已引（本轮修正标题/发表处） |
| Provable Pruning via Coresets | arXiv:2607.02721（2026-07） | **资产侧可证明剪枝**（加权 coreset 定理） | 新增引用，并写清"保证约束的是渲染目标，不是签发后的证书" |
| LinearMask-GS | BMVC 2026 / arXiv:2609.10095 | 学习掩码剪枝（第四类准则族） | 新增引用（局限段） |
| 3DGS.zip | arXiv:2407.09510 | 压缩方法综述 | 未加（压缩不是本文对象；如审稿人要求可补） |

### D. 感知质量评估（相邻、不同对象）

| 工作 | 出处 | 说明 |
|---|---|---|
| Quality Assessment of 3DGS: Distortions, Benchmarks, Open Challenges | arXiv:2609.23027（2026-09） | 综述：现行 QA 仍用渲染视角代理协议 |
| GS-PQM | arXiv:2610.00195（2026-09） | 参数域质量度量（SVR），面向压缩后资产 |
| GScomp-QA / 3DGS-VBench+ / 3DGS-VBench / GS-QA / MUGSQA | 2605.26880 / 2611.04498 / 2508.07038 / 2502.13196 / 2511.06830 | 主观/客观质量数据集与基准 |

处理：新增 "Perceptual quality" 一段（引综述 + GS-PQM），写清"感知分数是资产间排序，证书是单资产逐像素错误率界"。

### E. LOD / 流式（"资产会被再简化"的场景支撑）

CLoD-GS（2510.09997）、KoalaGS（2610.28615）、Matryoshka GS（2603.19234）、Budgeted-GS（2610.03162）、FilterGS（2603.23891）等。
处理：未逐篇引用；本文"AURA 已把证书扩成 LOD 阶梯"一句已覆盖该场景。若审稿人要求"资产被流式简化"的证据，可补 1 篇。

## 三、威胁评估（对当前稿件）

| 潜在审稿意见 | 现状 | 是否已处理 |
|---|---|---|
| "模型漂移破坏 conformal 已知（LLM 量化）" | 本轮前未引 | ✅ 已引 Doula & Mühlhäuser，并在 §4 说明对象/编辑差异 + SH 量化反例 |
| "certified 一词被滥用，你们的证书是什么" | 已有 §2 对象定义 | ✅ 加 XM4D 例子，集中"certified≠coverage"的清单 |
| "为什么不用感知质量指标" | 原本未提 | ✅ 新增 Perceptual quality 段 |
| "压缩文献只引三篇" | 已引 PUP/LightGaussian/EAGLES | ✅ 再补 coreset（可证明剪枝）与 learned-mask 两支 |
| "资产被再简化是常态吗" | 有 AURA LOD 一句 | ⏳ 可选：补一篇 LOD 引文 |
| "LLM CP 量化会失效，你们 8-bit SH 却说无影响，矛盾？" | 本轮前无法回答 | ✅ §4 已写：SH 量化扰动比残差低两个数量级，故 0.0 点——是否失效是定量问题 |

## 四、本轮对论文的改动

1. §4 "Conformal inference under changed distributions"：新增 inference-time model shift（Doula & Mühlhäuser）
   与 declared change envelopes（Usama & Qadir）两句，并加"8-bit SH 量化 0.0 点"的定量对照。
2. §4 "Certificates for splat assets"：补 XM4D（certifiable = 全局最优）。
3. §4 新增 "Perceptual quality" 段（Liu et al. 综述 + GS-PQM）。
4. §4 Compression 段：补 coreset 剪枝与 learned-mask 剪枝（上一轮插件评审已加，本轮并入同一叙事）。
5. 参考文献新增 5 条（doula2026modelshift、usama2026update、xm4d2026、liu2026qa、martin2026gspqm），
   并补全 VSCP（Chu, Pan, Shi）、Manifold-GS（B. Li）、LinearMask-GS（Ryu, Lee）的作者列表。

验证：`tools/verify_tex_v3.py` **405 断言 0 失败**；补充材料零配置 405/0；单测全过；
`SOURCE_DATE_EPOCH=1700000000` 双遍编译与投稿 PDF **逐字节相同**；PDF **14 页 / 371,275 B**，Overfull 0。
正文（不含参考文献与附录）约 11.5 页，仍低于 TMLR 的 12 页门槛。

## 五、检索边界（诚实声明）

- arXiv/OpenAlex/S2 只覆盖英文公开文献；未检索中文期刊、专利、学位论文与闭源工业报告。
- 2026-10 之后的新 arXiv 条目可能尚未进入 OpenAlex 索引；arXiv API 覆盖到 2026-11-10。
- 插件知识库快照 2026-11-06、1066 条，**不含** PUP、AURA 这类非 arXiv 或早期会议工作——"库内查不到"不等于不存在。
- 本轮只对 6 篇做了摘要级细读（AURA、Doula、Usama、XM4D、Liu 综述、GS-PQM），其余为标题/摘要级。
- 没有做全文精读的能力边界：不能保证"某篇 2026 年的 workshop 论文里有一节做了类似测量"；
  建议投稿后设置 arXiv 关键词提醒（"conformal + Gaussian splatting"、"certificate + splatting"）。
