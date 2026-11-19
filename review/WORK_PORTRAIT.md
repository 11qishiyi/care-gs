# WORK_PORTRAIT · 我们这篇论文是什么（事实卡）

> 用途：任何 scout / reviewer 引用"我方工作"时**只引本页**；细节回原文。
> **权威排序（冲突一律以 1 为准）**：① `submission/final/main.tex`（= 投稿正文 v4，917 行，无 `\input` 依赖）
> ② `PAPER_certificate_invalid.md`（md 长版，2026-11-09）③ `PAPER_certificate_invalid_v3.md`
> ④ `DELIVERABLES.md` / `SUBMISSION_CHECKLIST.md` / `review/TMLR_GAP_BRIEF.md`（**会话总结，数字与节号滞后**）
> 标注 `[冲突]` 处均已按 ① 校正。行号指 `main.tex`。

## 0. 一句话设定 / 一句话贡献 / 类型

- **设定（英文原句，摘要 L23-28）**："A 3D Gaussian Splatting (3DGS) asset can be shipped with a distribution-free *coverage
  certificate* … Such a certificate is a statement about one model, yet assets are re-pruned, re-quantised and re-fitted by
  whoever receives them."
  **中文**：3DGS 资产随附"以 1−α 概率单像素渲染误差 < q"的免分布覆盖率证书，但证书只描述**签发时刻**的模型，而接收方会再剪枝/量化/微调。
- **贡献（摘要 L50-51 收束句)**："A certificate can therefore be valid and uninformative at the same time; validity is cheap to
  restore, and what it costs is width."
  **中文**：证书可以**同时"有效"且"无用"**；恢复有效性很便宜（两个视角），代价全在**区间宽度**上。
- **类型（一句话）**：TMLR 审稿人眼里这是**测量/实证研究**（measurement study），**不是方法创新、不是理论**——正文四处显式自述（英文引文见本卡 §6），
  全文无一处方法新颖性主张。**但"工具"这一半是空缺**：`main.tex` 里 `tool` 0 命中，`scripts/advise.py`（证书顾问工具）
  只在 `PAPER_certificate_invalid_v3.md` §5 出现，**未进投稿正文**。

## 1. `[冲突]` 必读：brief/DELIVERABLES 的数字是**旧口径**，论文已换

| 旧说法（来源） | 论文实际（位置） | 引哪个 |
|---|---|---|
| 剪 30% 掉 **10.9–18.6pp**（BRIEF L10、DELIVERABLES L71、md v3 §3.1） | 主口径是 **10.8–27.7**：bicycle −22.1[−25.2,−18.8] / flowers −10.8 / stump −27.7 / treehill −15.2（**Table 1** L223-226、摘要 L30） | **10.8–27.7**。10.9–18.6 只活在**附录 A**（L838），并被明确标注为 *normalised 口径* 的对照片 |
| 证书**低估实际损失 2–12 倍**；覆盖率 −4.6pp 时重定位 −16.8pp（BRIEF L15、DELIVERABLES L15） | **该主张已被论文撤回**。§3.4（L506-513）："A claim of the form 'coverage under-reports damage by a factor of k' is therefore **not well posed**: the factor ranges from zero to well above one"，改为 0/36–36/36 且三场景**反向** | **禁用"2–12×"/"4.6 vs 16.8"**。撤回机制：旧值拿 **3D 体素证书** 对 patch 任务；论文改以**逐像素证书**为主口径，而体素把效应缩小 1.9–4.9×（App A L839） |
| SH 3→1 **≤0.7pp**（BRIEF L11）/ 0.2–2.0pp（md） | **0.0–3.3 点**（bicycle −3.3 最大；treehill −0.0），8-bit 量化恰好 **0.000**且被当作"估计器噪声地板"（Table 2 L279-280、L316-321） | "SH 降阶 ≤3.3 点，8-bit 量化 = 0.000" |
| 重签 **2–4 个视角**、区间放宽 **26–71%**（BRIEF L11） | **两个**标定视角即恢复有效性（三场景落进 ±3 点；treehill 过覆盖 0.971，需 9 视角，App B L847-854）；放宽 **53–122%**（30% 剪枝）/ **325%**（10%）（§3.6 L642-645） | **53–122%** |
| 适用区间 = "训练收敛 **≳2M** 基元的发布检查点"（BRIEF L16） | 论文**没有**这个阈值；只说 *fully optimised assets*，且 200k 剪枝+微调仍复现 −10.3~−12.9 ⇒ "**optimisation depth, not density**"（§5 L746-751、App C） | 不要引 ≳2M |
| **节号**：DELIVERABLES 的 §3.3="低估 2–12 倍"、§3.5="三条判据" | 那是 **md 长版**编号；tex 里 §3.2=dose+criterion、§3.3=GT 口径、§3.4=效用解耦、§3.5=任务族、§3.6=重签价、§3.7=循环自检 | **引节号只引 tex** |

## 2. 贡献清单 C1–C6（对应 L101-129 六条 bullet）

| # | 内容（论文原话要点） | 证据形态 / 样本量 | 位置 |
|---|---|---|---|
| C1 | 剂量—反应式**测量**证书失效：4 个发布检查点、每场景 400 次标定/部署划分、两种区域粒度，并报**有效独立样本数 77–508** 而非假设像素独立 | 实验测量；4 资产 × 4 预算 + 3 编辑族；配对降幅 + 2.5/97.5 分位 | §3.1 Table 1；§3.2 Table 2；§2 "How many independent scores" L192-198 |
| C2 | 固定预算下的**准则对照**：Fisher 敏感度在三资产压掉 42–56% 的 stored-opacity 损伤；经典重要性（opacity×volume）在**每个**资产都最差（最高 −61.8 点，q +328%）；flowers 反向（−10.8→−19.2）⇒ "no criterion dominates" | 测量；3 准则 × 4 资产，同一 30% 预算 | §3.2 Table 3 L359-369 |
| C3 | **单边 GT 归一化口径**把幅度最多改变 **2.4×**（衰减因子：stump **0.42×**、bicycle 0.84×、treehill 0.84×、flowers 1.01×；对应 PSNR 22.2/23.9→17.1/13.9 dB），对称缩放不会（1.04–1.17×）；并论证**只有免标签口径可用于证书** | 测量 + 因果分析；4 口径 × 4 资产 | §3.3 Table 4 L408-419、L431-444 |
| C4 | **阈值扫描**检验"覆盖率即代理"：三族任务在 36/36 格全部受损，但"任务损失>覆盖率损失"的格数从 **0/36 到 36/36** 随资产变；温和剪枝处排序在三/四个场景**反转** | 测量；3 配置 × 12 (tol,peak) 格 = 36 格/场景 × 4 资产 | §3.4 Table 5 L459-478 |
| C5 | 再加两族任务：全局配准一致性只丢 2.5–11.3 点，局部匹配丢 11.1–34.4，证书丢 10.8–27.7；两视角相对位姿旋转 <1° ⇒ 同编辑下**四把尺子差 4–11 倍**（去掉 treehill 仍 4.2–10.9） | 测量；3 手工任务族 + 1 学习型检查（LoFTR, App E） | §3.5 Table 6 L552-567 |
| C6 | **修复的价码**（配对分位）：任意标定规模都能恢复覆盖率，但 30% 剪枝后 q 增长 53–122%，对照"精确 no-op"编辑给出的零宽度噪声地板 | 测量；n=2..full 修复曲线 + 配对 q 增长 | §3.6 + App B |

**明确不主张为贡献的两条**（论文自己降级）：① 分块划分破坏交换性、训练视角混入标定集 —— "we report this as a **trap** … **rather than as a contribution**"（L202-203）；② "用标定集自检"是循环论证 —— 放进 §3.7，只作为**加强流程规则**的负面结果。

## 3. 方法栈（保形用法，务必精确）

- **split conformal**（单一划分分位数，非 full/Jackknife+）：q = Quantile_{⌈(n+1)(1−α)⌉/n}({r})，**α=0.10**，n = 标定**像素**数（§2 Certificate L162-167）。
- **非一致性分数**：逐像素残差 r = |I_render − I_gt|（通道均值）。
- **证书对象**：**per-pixel marginal coverage**（论文自述"最弱但仍可核对"的声明；AURA 是 per-carrier mean-unreliability、VSCP 是 view-structured ⇒ **对象不同**，这是拒绝 head-to-head 的理由）。
- **coverage 定义**：部署像素中 r ≤ q 的比例；**区域变体**用 64×64 图块内 max 残差 / 0.25 单位世界体素内 max 残差（§2、App A）。
- **划分**：每场景 **400 次随机 calibration/deployment 划分**，每个留出视角只渲染一次；报均值 + 2.5/97.5 分位。论文**明确称其为 split-to-split intervals，不是置信区间**（L186-188）。
- **自助区间：只有一处** —— registration 列用 **view-level paired bootstrap**（Table 6 标题 L547）；其余全是 split-to-split 分位。`[冲突]` DELIVERABLES 说的"视角级自助 CI"是工具名（`certificate_audit.py`），不是正文措辞。
- **为什么要按视角重采样**：split-to-split sd 0.013–0.034，若像素独立应约 1e-4 ⇒ 有效样本量 **77–508**（L192-198）。
- **可信度锚**：fresh 覆盖率 0.898–0.902 vs 名义 0.900（L235-238）；8-bit SH 是**精确 no-op** ⇒ q 增长 0.000（L316-321）。
- **两条协议前提**（陷阱，非贡献）：标定视角必须与任何被优化视角不相交；交错划分，分块划分会掩盖近一半退化（App D）。

## 4. 适用区间（scope condition）与反例

- 资产：**一个**公开 3DGS 输出归档的 4 个发布检查点（Mip-NeRF 360 的 bicycle/flowers/stump/treehill），**3.13M–5.26M 基元、40k 迭代、1/4 分辨率**、gsplat 1.5.3；留出视角 22/25/18/16（每第 8 张）。
- 主张范围原话（§5 L746-748）："The effect is a property of **fully optimised assets**, not of Gaussian splatting in general."
- 反例（App C L859-863）：5 个从零短训场景（116k–241k）→ **−0.8 / +0.0 / −0.2 / +1.1 / +3.2**（无效应）；而发布检查点压到 200k 再微调仍 **−10.3~−12.9**。
- 结论句（§5）："The driver is **optimisation depth, not density**, and the deployable regime is exactly the one where the effect appears."
- **混淆声明**在这里：效应依赖"是否来自完整训练"，而论文只有这一个**二分**，没有刻画优化程度的连续指标（`PAPER_certificate_invalid_v3.md` §6 明写"本文没有刻画'优化程度'的连续指标"，tex 把它软化成 density/depth 论证）。

## 5. 已声明限制 / 已知弱点（论文里都写了，引用时别假装没有）

1. **任务族是手工的**（故意如此，以排除学习模型混淆）：结论只覆盖这三族，"downstream utility" 一词已被摘要限定为 "within the three task families we implement"（L41-42）；学习型 matcher 只作鲁棒性检查（App E）；**稠密 SfM 前端未测**（§5 L756-763）。
2. **treehill**：对 captured GT 仅 **9.4 dB**，病因是"亮度 + 高光裁剪"（5/18 视角 >5% 饱和，最高 11.1%；p99 残差 3.4 vs 其它 <1.7），**无免标签口径可修**（§3.1 L244-256）。
3. **treehill 位姿指标处在分辨率极限**：fresh 只有 **12/17** 对通过，30% 编辑只移动一对 ⇒ Table 6 脚注 + Fig.2 标题**明说不作解释**（L548-550、L527-529、L617-619）。
4. **registration 自曝反向 caveat**：只拟合平移、fresh inlier 已 0.83–0.93（headroom 小），论文自己写 "Both caveats push **against** the argument that follows"，故只主张"四把尺子中最不敏感"而非"不敏感"（L586-594）。
5. **AURA head-to-head 不可定义**（对象不同，只比对象与量、不比实现，§4 L678-685）；`[补充]` DELIVERABLES §十一：工程上亦受阻（AURA-Core 要 Py≥3.11，per-carrier 标签脚本不在 wheel 内）。
6. **单一归档 / 1/4 分辨率 / α=0.10 固定**（§5 Scope L751-754）；merge 编辑只在 bicycle/flowers（Table 2）。
7. 微调/重训作为编辑类型、同场景独立重采集、第三种以上准则族（学习掩码、逐视角敏感度）**均未测**（§5）。
8. 引用的 AURA 指标（selection AUC 0.58–0.72、107k–130k carriers）是 AURA 自报值，本文**未复算**（§4 L670-677）。

## 6. 新颖性措辞（逐句英文原句，不要转述成更强的话）

- 唯一优先权句（**已加 hedged 限定**，L67-68）："The natural questions, *how much of the guarantee survives an edit* and *is the certified quantity the one that matters*, have, **to our knowledge, not been measured together**."
- 贡献定性（L712-714）："What we contribute is the **measurement of what those methods would have to repair**, and the observation that the repair, when labels are available, is cheap in data and expensive in width."
- 再定性（L718-720）："Our contribution is **not the phenomenon but its quantification** for splat certificates, and, specifically, the **non-monotonicity**: a proxy can be conservative at one edit strength and anti-conservative at another."
- 与 AURA 的分工（L678-679）："Our question is **different in kind rather than in method** …"
- 自我类型（§6 Broader impact L780-781）："**This is a measurement study** of quality guarantees for reconstructed assets. It **proposes no new generative capability and releases no new dataset**."
- 主张边界（§5 L752-754）："what we report is a measurement on these assets under a stated protocol, **not a law** about 3DGS assets in general."
- 全文 grep **无** "novel / first to / we propose / our method / we introduce / state-of-the-art / outperform"；无 SOTA 比较表。**这是可控的，不要替论文加码。**

## 7. 论文已引的最近邻（审稿人一定拿来对）

AURA（per-carrier 等渗校准 + split-conformal 剪枝证书 + certified LoD 阶梯；selection AUC 0.58–0.72 vs opacity 0.37–0.53）· VSCP（按视角分解 scale 以收紧区间）· Manifold-GS（"certified"= 几何/拓扑）· XM4D（certifiable 全局最优）· Dong & Li（重建阶段保形深度）· coreset 可证明剪枝（mousa2026provable）· 学习掩码剪枝 LinearMask-GS · PUP（Fisher 对角，三准则之一）· **LLM inference-time model shift（doula2026modelshift，概念最近邻）** · Usama & Qadir（declared change envelopes）· Lacuna 代理指标笔记（§3.4 主动引为概念先例）。全部在 §4。

## 8. 是否被包装成方法创新？（审稿风险点，逐条核对过）

- **写明是测量**：是，四处（§6、§4×2、§5），且主动把两条方法学发现**降级为 trap**（L202-203）—— 反向信号，说明作者在自我克制。
- **唯一可被读成"方法/协议贡献"的地方**：两条规范性句式 —— "a certificate **must/should carry** the criterion it was issued under"（L109-110、L393）与 "**issue the certificate after the edit, not before it**"（§3.6 L647-649）。这不是方法创新，但会被当成 design rule 去检验。
- **具体风险**：C2 的 "sensitivity 优于 opacity" 与 AURA 已报告的 "calibrated confidence 剪枝优于 opacity" **结论重叠**；`NOVELTY_AUDIT_2026-11.md` 判为"**不新**"并要求写成"在覆盖率指标上复现"。论文当前写法是"no criterion dominates / 三资产成立、flowers 反向"，**比旧版弱、但未显式承认是复现** ⇒ 这是最容易被打的一处。
- **没有做的事**（别替它吹）：不提出新的剪枝/证书方法，不提出理论界，不给修复算法（只给"价码"），不做 SOTA 比较，不发布数据集。

## 9. 定位索引（引用即指到这里）

| 事实 | 文件 · 位置 |
|---|---|
| 摘要 / 六条贡献 bullet | `submission/final/main.tex` L22-52 / L101-129 |
| 设定、证书数学、协议、有效样本量 | 同上 §2 L131-203（q 公式 L164-166，400 划分 L184-190，n_eff L192-198） |
| Table 1 主测量（10.8–27.7） | L210-229 · 正文 L231-257 |
| Table 2 剂量-反应 + 非几何编辑 | L261-309 · 正文 L311-335 |
| Table 3 三准则 × 四场景 | L348-371 · 正文 L373-393 |
| Table 4 GT 口径 2.4× | L398-420 · 正文 L422-444 |
| Table 5 36 格阈值扫描 | L449-480 · 正文 L482-513 |
| Table 6 四把尺子 | L537-569 · 正文 L571-632 |
| 修复价码 / 循环自检 | §3.6 L634-652、§3.7 L654-666 |
| 相关工作（AURA/VSCP/…） | §4 L668-741 |
| 限制、App A/C/D/E | §5 L743-776；附录 L832-915 |
| 复现声明（437 条断言） | §7 L786-799 |
| md 长版（旧口径，§3.3 称"低估 **1.9–12.1 倍**"，被 brief 简化成 "2–12 倍"） | `PAPER_certificate_invalid.md` 摘要 L17-20、§3.3；节号体系与 tex 不同 |
| 数字校验/清单/查重/检索 | `tools/verify_tex_v3.py`；`SUBMISSION_CHECKLIST.md` §四·§六；`NOVELTY_AUDIT_2026-11.md` §二；`review/LITERATURE_SURVEY_2026-11.md` |
