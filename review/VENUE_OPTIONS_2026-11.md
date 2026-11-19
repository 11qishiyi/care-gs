# 投稿 venue 备选评估（2026-11-12）

> 问题：除了 TMLR，《Valid but Unusable》还有没有更合适的去处？
> 方法：两个并行 scout 只查**官方页面**（scope / CFP / 审稿政策 / 时间线），并核对**已发表的同型先例**（测量类、无新方法、无新数据集）。拿不到的一律写"未取到"。
> 结论见 §5；本文件只做证据留痕，不改论文。

## 0. 一条硬约束先说

所有候选都是 **archival**，**不能并行投**：TMLR / DMLR / NeurIPS E&D 三者互斥（DMLR 明文允许 arXiv 与非 archival venue 并行，但禁止与另一 archival venue 并行）。所以这是**单选**，不是组合。arxiv 预印本在所有候选都允许。

---

## 1. 四个真实候选（按"是否需要改造"排序）

### A. TMLR（现状即投，基线）
- Scope 明文收："experimental and/or theoretical studies yielding new insight"、"reproducibility studies"、"new approaches for analysis"；接受标准写明 "**even if the contribution or significance of the work is modest**"。
- 滚动、无截稿、公开评审（可在评审中改稿）、J2C 认证可上 NeurIPS/ICLR/ICML 的 J2C track。
- 时间：第三方评审→决定的**中位数 45.3 天**（[OpenReview 审计，4,865 份投稿](https://zrobertson466920.github.io/TMLRAudit/)），总周期通常 4–6 个月。
- 改造量：**0**（`submission/final/` 已就绪：tmlr.sty、14 页、437 条断言、OpenReview 字段）。
- 风险：AE 桌面拒稿（"insufficient reviewer expertise"，3DGS 在 TMLR 很薄）；R1/R2 形态问题（见 `review/TMLR_REDTEAM.md`）。

### B. DMLR（Journal of Data-centric ML Research，JMLR 家族）
- Scope 明文收**无新数据集、无新方法**的分析："audits of existing datasets, identifying significant problems with existing datasets and their use"；"**Methodology and empirical evaluation** …"；"Systematic analyses of existing systems on novel datasets or benchmarks that yield important new insight"（[submissions](https://data.mlr.press/submissions.html)）。
- 滚动、**单盲** + 决定后公开评审；官网流程：EIC 预审 ≤2 周 → 3 审稿人 4 周 → rebuttal+discussion 3 周 → AE 决定 1 周 ≈ **10 周/轮**；实测提交→见刊 **3.5–4.6 个月**；**零费用**。
- 模板 `dmlr2e.sty`（tmlr.sty 不能用），强制 **Broader Impact Statement**，附录必须在参考文献后；**页数上限未取到**（14 页体量可保）。
- **同型先例（都在 OpenReview 实取）**：
  - *Constructing Confidence Intervals for "the" Generalization Error – a Comprehensive Benchmark Study*（2025，`x7kCj9OU2c`）——13 种 CI × 19 问题，评 coverage/宽度/运行时间，**Reproducibility 认证**；
  - *Evaluating Durability: Benchmark Insights into Image and Text Watermarking*（2024，`IaUzVUf0CL`）——100 种图像扰动协议 + 代码，纯"扰动下掉多少"的测量；
  - *Beyond Borders: Quantifying Geographic Domain Shift in Automotive Perception*（2026，`go887vmxL8`）——纯观测性测量，3 个现成数据集，作者原话 "observational and does not establish causality"。
- 必须补：① 换模板 + Broader Impact；② **把 framing 改成 data-centric**（把证书讲成"随资产发布的质量元数据"，问题落成"已发布数据资产的元数据在资产演化后失效"）；③ 必须有可复用产物（匿名 repo：`scripts/advise.py` + 400 次划分驱动 + 每资产证书）；④ 补配对 bootstrap 或明确的不确定性传播说明（审稿人里有专做 CI/coverage 的人）。
- 风险：**AE 预审被判"这是渲染/视觉评测，不是 data-centric ML"**——DMLR 唯一硬拒口是 scope + 格式。

### C. NeurIPS 2027 E&D（原 Datasets & Benchmarks，2026 年起改名）
- 官方博客原句：*"the Datasets & Benchmarks Track at NeurIPS 2026 has been officially renamed the **Evaluations & Datasets (ED)** Track … evaluation becomes an object of scientific study in its own right"*（2026-03-23）。
- Scope 里**几乎逐字为我们写的**："**Compare evaluation designs and demonstrate how different assumptions lead to different results or conclusions**"；"Analyze strengths, limitations, or failure modes of existing benchmarks or evaluation practices"；"Provide rigorous reproduction, **auditing**, and **stress-testing** of prior evaluations"；"**Submissions need not introduce a new model or outperform prior work.**"；审稿指南："Originality may be achieved by … **showing how different evaluation assumptions lead to different scientific conclusions. New framing is sufficient — no need to beat a baseline.**"
- 但：**一年一窗**（2026：abstract 05-04 / full 05-06 / notification 09-24）→ 下一窗口 **2027-05**，见刊 2027-09；**正文 9 页**（现 14 页要砍 ~35%）；双盲；分析类稿代码非强制但需填 justification。
- 同赛道竞争：*NerfBaselines*（NeurIPS 2025 D&B，"3DGS/NeRF 评测协议微小差异就能抬高指标"）已经占了这个位置；另有 *Mind the Gap*（arXiv 2607.01556，3DGS 评测测的是近轨迹插值，**16 场景 spatial-holdout benchmark toolkit 准备发布**）。→ 投这里，我们会被放进"3DGS 评测协议"赛道与他们比。
- 历史包袱：官方复盘写明 **2025 年 84% 的 D&B 录用稿引入了新数据集**——2026 改名才真正对我们友好，但录用习惯需要时间改。

### D. CVM（Computational Visual Media，清华大学出版社，IEEE Xplore 收录）
- Scope 明文含 **"Editing and composition of visual media"**——"编辑后证书失效"正中该条。
- 周期（SciOpen 官方）：**28 天首决 / 93 天录用 / 60 天出版**——四个候选里最快。
- 同型先例：*From Far and Near: Perceptual Evaluation of Crowd Representations Across Levels of Detail*（CVM 12(4), 2026, `10.26599/CVM.2026.9450562`）——**单个角色 + 24 人用户研究**，无新方法、无新数据集、10 页。这是"单资产规模"能被接受的最强证据。
- 必须补：把标题/摘要从质问式（"What … Miss"）改成"**评估协议 + 失效清单 + 修复配方 + 公开脚本**"三件套；编辑对 "novel ideas, methods, and systems" 里的 method 会咬。
- 风险：受众偏图形/视觉媒体，保形预测的语义审查弱（双刃：容易过，但对论文的方法学价值加成小）。

## 2. 明确不推荐

| venue | 官方依据 | 为什么不适合现在的稿子 |
|---|---|---|
| **IJCV** | "Regular articles (up to 25 journal pages) present **major technical advances**"；scope 全文无 benchmark/evaluation 字样；中位首决 37 天（官网另注 ~96 天） | 先例（RealX3D 55 场景、Text-to-3D-QA 3,600 mesh）都靠**大网格/新指标**立项；4 场景 + 无方法撑不住 |
| **TPAMI** | "particular emphasis on machine learning for pattern analysis"；首决中位 2.62 月、录用 10.05 月 | 4 场景测量会被 desk-reject 判 importance 不足 |
| **3DV** | 2027 摘要/全文 **2026-08-28 已截稿**；8 页正文 | 下一窗口 2027-08（3DV 2028）；且 CFP 要求新数据集/协议/指标 |
| **Pattern Recognition** | "papers whose primary concern falls outside … should be directed elsewhere"；20–35 页 | 领域框定错位（需改写成 CP/UQ 叙事），周期 206 天 |
| **DMLR Special Track** | 官方页：面向"曾在 NeurIPS D&B 被拒且评价很高"的稿 | 我们是新稿，不符合入口条件 |
| **JMLR / AISTATS / COLT** | 理论向 | 无理论界 |

## 3. 决策表（按你优化什么）

| 你优化的目标 | 选谁 | 代价 |
|---|---|---|
| **最小改动 + 风险可控**（现状投） | **TMLR** | 0 改造；面对 R1/R2 与薄赛道评审池 |
| **期刊体量 + 显著性门槛更宽 + 同型先例多** | **DMLR** | 2–4 天（换模板 + 改 framing + 补匿 name repo）；风险是 AE scope 预审 |
| **最高可见度（NeurIPS 三个字）** | **NeurIPS 2027 E&D** | 10 个月等待 + 14→9 页 + 双盲 + 必须交 artifact；并与 NerfBaselines/Mind the Gap 同赛道 |
| **最快见刊（保底）** | **CVM** | 28 天首决、93 天录用；需重写为"协议+清单+配方"；受众偏图形 |

## 4. 我的判断（一句话版）

**现状：TMLR 仍是最优的"风险调整后"选择；但如果把"贡献形态"当第一位的，DMLR 是唯一值得换的期刊；NeurIPS E&D 的 scope 最贴我们的发现，代价是 10 个月 + 35% 删减 + 撞上已有的两条 3DGS 评测工作；CVM 是保底快车道，不是首选。**

理由三条：
1. **换刊解决不了我们最弱的那一项（广度）**——4 个场景在任何 venue 都是弱项；而"贡献可以不大、只要证据准确"这句话只有 TMLR 写在官方标准里。
2. **DMLR 是唯一"先例形态与我们同物种"的期刊**（CI 基准 / 扰动鲁棒性测量 / 观测性 domain-shift 测量），且滚动、无页数上限、单盲，3.5–4.6 个月见刊；代价是 framing 必须改成 data-centric，且必须先有匿名代码。
3. **E&D 的 scope 是四个里最贴的，但它把我们从"证书失效"推到"3DGS 评测协议"赛道**——那里已有 NerfBaselines 和 Mind the Gap（后者还带着 16 场景 toolkit 在路上）。**我们的差异化在证书，不在协议排名。**

## 5. 执行建议（若采纳"先 TMLR"）

1. 先做 `TMLR_GAP_ANALYSIS_2026-11.md` §6 的 A 档十条（半天）+ 把 `scripts/advise.py` 补进附录（1–2 天）——**这份工作对四个 venue 都增值**，不浪费。
2. 投 TMLR（滚动，随时可投）。
3. 并行准备 DMLR 版：`dmlr2e.sty` + Broader Impact + 匿名 repo；**TMLR 一被拒（含 reveal 与否的决定）即可换投**，不用从零开始。
4. 若 TMLR 被拒且决定走 E&D：用 2027 年 5 月窗口，届时把 4 场景扩到 8–12 场景（3DV/TMLR 都在扩场景，成本已知：每场景一次下载 + 审计）。

## 6. 未取到 / 需自行确认

- DMLR 页数上限；DMLR Special Track 是否接受 E&D 被拒稿（需邮件问编辑部）。
- NeurIPS E&D 2027 CFP 与 2026 录用率；2026 官方录用列表（OpenReview 会场页被拦）。
- IJCV 审稿轮次；TPAMI "insufficient novelty" 的官方表述；3DV CFP 原文（站点抓取被拦）；CVM 2025+ 作者指南 PDF。
- 上表所有"周期"数字均为官方页/官方社论口径，非个人经验值。

---

# 第二轮：按"主题相关性"重查（2026-11-12 追加）

用户追问"没有更相关的期刊吗"——上一轮按"接受测量类"筛，这一轮按**主题**（3DGS/渲染/压缩/质量，以及保形/不确定性）重查。结论：**主题上确实有比 TMLR 更相关的期刊，但没有一个"既主题相关、又不需要把论文改造成另一种稿子"。**

## 7. 3DGS / 渲染 / 压缩 方向（scout A，官方 scope + OpenAlex 逐刊检索）

| 期刊 | 主题相关 | 收不收无方法稿（官方） | 同型先例（可查） | 要补什么 | 周期（官方） |
|---|---|---|---|---|---|
| **IEEE TCSVT** | **5/5**（3DGS 压缩主场：*Compression in 3DGS: A Survey* 2026、*GSCodec Studio* 2026） | 半：官方写 "**review articles and surveys are acceptable, even if new data/concepts are not presented**"——**只对综述开口**，不对测量开口 | *Video Quality Evaluation Methodology and Verification Testing of HEVC Compression Performance*（2015）——纯方法学+验证测试，无新编解码器 | 4→**8–12 场景**；剪枝升级为真实码流算子（GSCodec/LightGaussian/Compact3DGS）；**加 LPIPS 或 20–30 人主观**；覆盖率误差进 RD 曲线 | 未取到（IEEE 不公布中位数） |
| **IEEE TVCG** | 4/5 | 半：现行 Xplore scope 无 evaluation 字样；**旧版 IFOA 明列 "user studies and evaluation"** | *On the Efficiency of Image Metrics for Evaluating the Visual Quality of 3D Models*（2015）——**评"既有度量本身"**，与我们"四把尺子差 4–11 倍"同物种 | 至少 20 人用户研究；编辑算子谱系；与 PSNR/SSIM/LPIPS/FLIP 对照；交脚本+证书格式 | 未取到 |
| **Computers & Graphics** | 4/5 | 否（scope = graphics systems & applications + SOTA + tutorial） | *3D reconstruction and precision evaluation of industrial components via GS*（2025）——纯精度评测 | 叙事改成"资产管线里的**质量元数据 + 编辑后重认证配方**"；交 artifact（有 **GRSI 可复现徽章**）；4–6 场景可保 | **42 天复审决定 / 91 天录用 / 12 天上线** |
| **JVCIR** | 3/5 | 否 | *A critical survey of image inpainting quality assessment metrics*（2017）——批评既有指标 | 必须有感知指标或主观数据 | 15 天首决 / 215 天录用（最慢） |
| **Machine Vision & Appl.** | 3/5 | 半：明文 "**Papers must include a significant experimental validation component**" | 仅 1 篇综述（radiance-field 编辑） | 需要机器视觉应用落点（SLAM/机器人/AR 用 GS 资产） | **首决中位 30 天** |
| **IEEE TMM** | 3/5 | 否 | 2010/2025 各一篇"度量比较"；3DGS 29 篇里 **0 篇纯评测** | **MOS + 感知指标 + benchmark 数据集，三样全缺** → 等于重做一篇 | 未取到 |
| IEEE TIP / TCI / ACM TOG / JCGT | 2/5 或更低 | 明确要 novel theory/algorithm（TIP）、image formation（TCI）、SIGGRAPH 级新颖性（TOG）、short practice notes（JCGT） | 3DGS/NeRF + 评测 **0 命中** | 不适用 | 未取到 |

## 8. 保形 / 不确定性 方向（scout B）

| Venue | 相关度 | 收不收"无定理实证"（官方） | 同型先例 | 周期 | 分 |
|---|---|---|---|---|---|
| **Machine Learning**（Springer） | 4/5 | 收："**Provides robust support through empirical studies**" | COPA 特刊（Mach Learn 108, 2019）；Carlevaro et al. 2024 保形分类 | 滚动 | 4 |
| **Neural Networks**（Elsevier） | 3/5 | 收（含 engineering applications） | Papadopoulos 2011（CP 回归区间）；Lei & Bellotti 2023 | 滚动 | 3 |
| **JMLR** | 3/5 | 原则上收，但"audience too narrow 可判不适"、35 页、不收未邀综述 | *Split CP and Non-Exchangeable Data*（2024）；"replication probability of benchmark experiments"（2024，纯元研究） | 滚动 | 3 |
| **DMLR** | 3/5 | 收，但必须 data-centric 为主 | OpenOOD v1.5（2024） | 滚动 | 3 |
| **JDIQ**（ACM） | 2/5 | 收 empirical evaluations，但框在信息质量 | "Measuring the (Lack of) Quality of Disinformation"（2025） | 滚动 | 2 |
| **UAI / AISTATS** | 2/5 | 要 novel theory/methodology；AISTATS 2027、UAI 2026 均已截稿 | 清一色方法/理论（无纯测量型先例） | 下一个窗口 2027 | 2 |
| **IJUFKS** | 1/5 | **明确不收** image/video processing 的应用稿 | — | — | 1 |

## 9. 两条比 venue 更重要的发现（来自这轮检索）

### 9.1 直接前作已经报告了"逐像素边际覆盖 ≠ 视图级覆盖"

**Chu et al., "View-Structured Conformal Prediction for 3D Gaussian Splatting", arXiv:2609.10307（2026-09-09）**：
> pixel-pooled calibration 在 13 个真实场景上达到 **"89.9% marginal pixel coverage but only 61.4% view-event coverage at a 90% target"**。

这正是我们"valid but uninformative"的一半（我们论文已引该工作，记作 VSCP）。**后果**：任何 venue 的审稿人只要知道 VSCP，就会问"你的新意是不是已经被做过了"。**我们必须把贡献切到他们没碰的三条轴**：① 编辑诱导的失效（剪枝 10.8–27.7 点）；② 修复成本（2 视角 → 宽度 +53–122%）；③ 协议敏感性（GT 口径 2.4 倍）。这同时意味着：不要把论文卖成"证书可能没用"（已被占），要卖成"证书在资产被改动后会坏，且坏多少可测"。

### 9.2 "批判 + 测量"这个 genre 落在应用型期刊，不落在理论期刊

**Kladny, Schölkopf, Koch, Baumgartner, Muehlebach, *A critical perspective on finite sample conformal prediction theory in medical applications*, Artificial Intelligence in Medicine, 2026, doi 10.1016/j.artmed.2026.103462**——无新方法、无定理，纯"理论被误用"的批判 + 一个测量（n=10 时 90% 的标定覆盖率低于 19%）。这既是我们"training-conditional vs unconditional"硬伤的**同类论述**（可正面引用，说明这是领域级问题而非我们的弱点），也说明：**我们这个 genre 的同类论文最终去了应用领域期刊**——对应到 3D/图形，就是 TCSVT / TVCG / C&G。

## 10. 第二轮结论

- **"更相关"成立的对象**：TCSVT（最相关，3DGS 压缩主场）、TVCG（"评既有度量"先例最像我们）、C&G（周期最快、4–6 场景可保）。
- **但它们都要求把论文变成另一种稿子**：TCSVT 要 8–12 场景 + 感知/LPIPS + 码流立场；TVCG 要用户研究；C&G 要"质量元数据+重认证配方"的重写（这条最轻）。
- **保形主题上更相关的是 Machine Learning（Springer）**（COPA 传统 + 明文收 empirical），但 3DGS 审稿池在那里更薄。
- **TMLR 仍是最优的"无需改造"解**，而且它的接受标准页面现在有更硬的依据（见下）。

### TMLR 官方接受标准里最硬的一句（本轮新取到）

> "a proper reproduction report that **systematically studies the robustness or generalization of published methods and offers actionable lessons for readers** can satisfy this criterion"；
> "**research-method novelty is not a necessary condition**"；
> 并明确**禁止**以 "not novel enough / not impactful enough" 拒稿。

来源：<https://jmlr.org/tmlr/acceptance-criteria.html>。→ 这是四个候选里**唯一把"不许用不够新拒你"写进评审政策**的期刊。
