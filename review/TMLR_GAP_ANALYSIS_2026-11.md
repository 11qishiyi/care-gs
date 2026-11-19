# 我们 vs TMLR 最近论文：差距分析（2026-11 版）

> 目标：回答一个问题——**我们这篇「3DGS 质量证书在几何编辑后失效」的测量类论文，和 TMLR 最近发布的工作差在哪里。**
> 证据链：TMLR 官方全量索引 5081 篇（2022-05 ~ 2026-11）→ 最近窗口 884 篇（2026-07~11）→ 三路关键词筛选 159 条候选 → 逐篇卡片（`research/tmlr/CARDS_3D.md` / `CARDS_CP.md` / `CARDS_EVAL.md`）。
> 我方事实基线一律以 `review/WORK_PORTRAIT.md`（从 `submission/final/main.tex` v4 校对）为准；**本文所有我方数字都已按该卡校正**（旧会话总结里的 10.9–18.6pp、"2–12×"、26–71%、"≳2M 基元" 均已废止）。

## 0. 结论速览（六条）

1. **差距不在"题目"，在"证据形态"**：TMLR 最近的近邻论文几乎全部给**一个可复用的东西**（新 benchmark、新数据集、新修正分数、新判据/算法、或一条定理）；我们给的是**一个资产上的测量 + 三条判据**。前者可以直接被下一个人用，后者需要读者自己搬运。这是最实的差距。
2. **3DGS 在 TMLR 是薄赛道**：2024/2025/2026 分别只有 1/7/4 篇 3DGS 或辐射场论文（占当年产出 0.1–0.5%）。好处是我们不太可能撞车；坏处是**审稿人池子薄**，AE 有"TMLR 是否具备相应评审专长"的桌面拒稿权，而且审稿人会用**通用 ML 的评测规范**来量我们，而不是 3DGS 社区的惯例。
3. **保形预测在 TMLR 是厚赛道且在涨**：2023→2026 是 1→3→9→22 篇，2026-10 单月 4 篇。我们用的 split conformal + 逐像素边际覆盖是最弱的一档；TMLR 审稿人**默认懂条件覆盖、非交换性、训练条件覆盖**，我们目前的表述（"valid but uninformative"）会被要求落到这些术语上。
4. **"测量/复现/审计"在 TMLR 是一等公民**：2026 年 1867 篇里有 **144 篇**标题属评测/分析/复现类（7.7%），其中 **23 篇**拿到了认证（13 篇 Reproducibility、7 篇 J2C），认证率 16% 略高于全刊 12.2%。TMLR 的 Scope 明文收录 reproducibility studies 与 "methods for assessing performance"。**文章类型不是问题。**
5. **我们真正缺的三样**（按审稿杀伤力排序）：① 外部效度（单一归档 4 场景、1/4 分辨率）——近邻论文普遍 2–8 个数据集起步；② 理论落地（我们没有把"编辑后覆盖失效"写成任何一个已知定理的实例，尽管它就是一个非交换性/条件覆盖失效）；③ 可复用的交付物（论文里 `tool` 零命中，`scripts/advise.py` 没进正文）。
6. **我们比近邻强的地方是真强，不要自我削弱**：统计口径（400 次划分、有效独立样本 77–508、明确拒绝把 split-to-split 分位称作置信区间），以及**"协议敏感性"这一层**——但后一条要收窄说（红队驳回了我原来的写法）：TMLR 里已经有人在同一层做过口径敏感性（XFeat 的 underspecified evaluation details、ShapeNet-55 的发布检查点自带另一套验证协议、RegressionMSR 的实现偏离算法两轴），我们能主张的只有"**没人对渲染证书做过，且没人证明过口径会改变失效幅度而不只是绝对值**"。

---

## 1. 数据与方法

| 项 | 内容 |
|---|---|
| 语料 | JMLR 官方 TMLR 论文索引页（含 Featured/Outstanding/Reproducibility/Survey/J2C 认证标记），抓取时间 2026-11-11 23:27，**5081 条**，覆盖 2022-05 ~ 2026-11 |
| 最近窗口 | 2026-07 ~ 2026-11 共 **884 篇**（8 月 249、9 月 194、10 月 212、11 月 63） |
| 筛选 | 三个桶：3DGS/辐射场/3D 重建（2026 全年 38 条）、保形/不确定性/校准（46 条）、评测/基准/复现/协议（75 条）→ 交三路 scout 逐篇取证 |
| 摘要获取 | OpenReview API 与 PDF 被 Cloudflare 拦（返回 "Verifying your browser"）；改用 arXiv abs 页、mlanthology 单篇页、作者项目页、检索摘要片段。**取不到摘要的条目在卡片里显式标注为"仅标题级"，不做摘要级断言** |
| 统计口径 | 月份分布、认证率、领域趋势均在全量 5081 条上算，不是抽样 |

**一个诚实的说明**：本报告的"最近"指 2026 年 7–11 月（TMLR 是滚动出版，11 月截至抓取日只有 63 篇）；3DGS 桶额外回溯到 2026 全年与 2024–2025 的 TMLR 先例，因为该方向在 TMLR 太薄，只看最近三个月会得到"零篇"的错误印象。

## 2. TMLR 最近的版图：三个数字决定我们的处境

### 2.1 我们所在的 3DGS 赛道很薄

| 年份 | TMLR 总数 | 3DGS/辐射场 | 占比 |
|---|---|---|---|
| 2024 | 955 | 1 | 0.1% |
| 2025 | 1432 | 7 | 0.5% |
| 2026（至 11 月） | 1867 | 4 | 0.2% |

2026 年的 4 篇：DP-Splat（10 月，贝叶斯非参数复杂度控制）、FastAvatar（8 月）、Trip-to-Gaussian（6 月）、BrightDreamer（3 月）。**没有一篇做"资产编辑后的质量保证"**——这是我们的位置，也是我们的空位。（计数按标题关键词；另有 Gaga: Group Any **Gausians**（6 月）因标题拼写错误未被命中，实际约 5 篇。）

同时这条薄赛道上已经有一个对我们极不利的先例：**Monocular Dynamic Gaussian Splatting: Fast, Brittle, and Scene Complexity Rules**（2025-06，拿到 **Survey 认证**）——一篇 3DGS 的 apples-to-apples 评测论文，它用**多个已有数据集 + 一个自建受控合成数据集**，结论是"数据集变化压倒方法差异"。它证明了 TMLR 接受 3DGS 评测类论文，也顺手立了**证据量的基线**：多数据集 + 自建受控数据。我们目前只有 4 个场景、单一归档。

### 2.2 我们借用的保形预测赛道很厚且在涨

| 年份 | 2023 | 2024 | 2025 | 2026（至 11 月） |
|---|---|---|---|---|
| 标题含 conformal | 1 | 3 | 9 | **22** |

2026 年 10 月单月 4 篇，11 月已出 2 篇。这意味着：审稿人不会是"没听过保形预测"的人，而是会用条件覆盖、非交换性、有效样本量、训练-标定独立性来逐条量我们的人。**我们的机会恰恰在这里**：这 22 篇里没有一篇处理"模型参数被后处理改动后，证书失效"。

### 2.3 "测量/复现/审计"在 TMLR 是一等公民，不是退路

| 2026 年 | 篇数 | 带任一认证 | 认证率 |
|---|---|---|---|
| 全部 | 1867 | 228 | 12.2% |
| 评测/分析/复现类标题 | 144 | 23 | **16.0%** |

其中 13 篇是 **Reproducibility 认证**（该认证的定义是"以复现为主目的，且必须通过额外 baseline/分析/ablation 提供显著增值"）。认证率数值上高于全刊均值（16.0% vs 12.2%），但**这个差在统计上不显著**（两个比例检验 z≈1.3，p≈0.19；且认证本身有申请/选择效应），所以正确结论只能是：**没有证据表明"测量类"在 TMLR 更难拿认证**，而不是"被主动奖励"。（此条经红队复核后下调，见 `review/TMLR_REDTEAM.md` §3。）

## 3. TMLR 的收录标准：对我们最有利也最危险的三句话

摘自 [TMLR 投稿与编辑政策](https://jmlr.org/tmlr/editorial-policies.html)（2026 版）：

- **Scope 明文收录**："experimental and/or theoretical studies yielding new insight into the design and behavior of learning in intelligent systems"、"accounts of applications of existing techniques that shed light on the strengths and weaknesses of the methods"、"reproducibility studies of previously published results or claims"、"new approaches for analysis, visualization, and understanding"。
  → 我们的文章类型（测量 + 分析 + 判据）**在 Scope 之内**，不需要伪装成方法论文。
- **接受标准**："Are the claims made in the submission supported by accurate, convincing and clear evidence?"、"Would at least some individuals in TMLR's audience be interested in knowing the findings?"，且明说 "Papers should be accepted if they meet the criteria, **even if the contribution or significance of the work is modest**"。
  → 这一句是我们最强的护身符：**不需要"顶会级创新"**，只需要"证据准确 + 有人关心"。反过来说，我们的风险全在"证据是否 accurate/convincing"上，而不在"够不够新"。
- **桌面拒稿的四条理由**：out of scope、**TMLR having insufficient reviewer expertise to adequately handle**、poor quality/unlikely to meet criteria、format violations。
  → 第二条对我们这种"薄赛道 + 单归档"的论文是真实风险，应对方式只有一个：**把论文写成让非 3DGS 审稿人也能独立核验的样子**（协议、统计、脚本、断言），也就是我们已有的 437 条断言复现声明的方向，但要把它从"复现声明"升级成"可复核的交付物"。

**另一条硬约束**：TMLR 不接受会议论文的扩展版（no reuse of text/figures/results），但允许 arXiv 预印本重叠。我们的投稿包目前是干净的，这一点在 `SUBMISSION_CHECKLIST.md` 已有对照。

---

## 4. 近邻地图：TMLR 最近到底在做什么

三路 scout 共产出 **45 张卡片**（3D 侧 14、保形侧 17、评测侧 14；去重后 44 篇，Conformal Data Contamination 两侧都出卡）。其中 **5 张完全未取到摘要、1 张只有仓库 README 级证据、1 张标题/月份冲突**，均已逐张标注。下面只保留**会影响我们论证**的条目。

### 4.1 3DGS 侧：全库只有 4 篇，唯一近邻是 DP-Splat（本报告最重要的一条发现）

Lead 用全量 5081 条复核过（可复算）：**标题含 `Splat`/`Splatting` 的 TMLR 论文历史总量 = 4 篇**；**标题含 conformal/certificate 且与 3D/高斯/辐射场交叉 = 0 篇**；**"编辑 + 3D"仅 1 篇且是"用 3DGS 做视频编辑"**。

| 论文 | 与我们什么关系 |
|---|---|
| **DP-Splat**（2026-10，arXiv 2607.10912） | **最强近邻，也是我们最该主动引用的一篇**。它把 3DGS 当有限混合、用 Dirichlet 过程先验让分量数自适应，报**占用分量少 3.9–7.9×**，同时报"**全光栅化留出视角比未剪枝基线低 3.4–9.0 dB**"，而同一摘要另一处说点空间预测在 0.33 dB 内。**它是"评测协议决定幅度"的独立先例**（红队纠正过我原来的写法：它比的是"点空间预测 vs 全光栅化"两种**评测协议**，不是 GT 光度前处理，所以只能说"同族现象的独立先例"，不能说"复现了我们的 C3"；且证据只到摘要级）。它的"well calibrated"是对**拟合完成、未动过**的模型一次性报告——恰好停在我们论文的起点。 |
| Diffusion Models are Secretly Zero-Shot 3DGS Harmonizers（2026-04） | **编辑算子来源**。它做"把物体插入 3DGS 场景并重光照"，是真实的下游编辑，但只报编辑后 PSNR，不问编辑前结论是否还成立。按我们的 C2，这类**外观编辑不该破坏证书**——这是一个可交叉验证的预测。 |
| Incremental3D（2026-04）、Gaga（2026-06） | 局部插入/高斯分组，都是"几何编辑"的真实形态，同样不做证书对照。 |
| **Squeeze3D**（2026-10） | TMLR 唯一"压缩 3D 资产"的论文，radiance field 压 **>650×** 且"视觉质量可比"。它是审稿人问"你剪 30% 就说证书失效，是不是太粗暴"的最可能来源——答法：它报的是**视觉均值**，我们报的是**有限样本覆盖率**，而我们自己的 C4（0/36→36/36）与 C5（四把尺子差 4–11 倍）正是"视觉持平 ≠ 任务无损"的证据。 |
| **Monocular Dynamic Gaussian Splatting**（2025-06，**Survey 认证**） | **体裁先例，且是我们的助力**：TMLR 已发过一篇结论为"3DGS 脆弱、真实数据复杂度淹没方法差异"的 3DGS 测量/分析论文。它证明 TMLR 收这类工作；它的结论也支持我们"幅度由协议决定"。 |

**结论**：TMLR 的 3DGS 内容是"生成与重建方法"，**质量保证类是空白**；而这个空白不是因为我们没想到，是因为**没人把"编辑事件"和"已发出的保证"连起来**——DP-Splat 有压缩事件、D3DR 有编辑算子、Squeeze3D 有压缩比，三块零件齐了，没有一篇拼起来。

### 4.2 保形侧：TMLR 审稿人默认的参照系（这一侧最危险）

2026 年 22 篇 conformal，我们读了 12 篇 + 5 篇 2023–2025 参照系。三篇直接决定我们的命运：

1. **Are foundation models good conformal predictors?**（2026-03，17 模型 × 3 CP 方法 × 多数据集）——它已经系统审计过 CP 在"分布漂移 / 做过 confidence calibration / few-shot 适配"三种现实扰动下的鲁棒性，结论是**只掉效率、不掉边际覆盖**。
   → 我们**不能**说"没人审计 CP 的鲁棒性"；能说的只有：**"参数容量被删除"是一个此前未被测试、且真能打坏覆盖率的扰动轴**——而这句话是拿它自己的负结果背书的。
2. **Rethinking Post-Hoc Calibration in Semantic Segmentation**（2026-10）——证明**给所有 logit 加同一常数（softmax 概率完全不变）也会让多个标准校准器失效**，且在分割里这个偏移逐像素变化。
   → 我们**不能**说"参数层面无害改动破坏校准"是新观察；能说的是"它破坏的是 ECE、不是覆盖率，且没有剂量-反应曲线"。
3. **On Training-Conditional CP and Binomial Proportion CIs**（2025-02，j2c）——**这是我们的硬伤来源，也是最好的护身符**：它指出 training-conditional CP 用于安全证书**不提供有效保证**，正确工具是 BPCI；零失败情形下单侧 95% 下界 L = α^(1/n)，**n=2 时只有 0.224，要 90% 需 n≈29 个独立单元**。
   → 我们"**2 个视角就能恢复**"这句话，如果被读成"2 个视角就能给覆盖率保证"，就是错的。必须**拆成两句**：偏差校正（经验陈述，有 400 次划分支持）vs 覆盖率保证（需要 ≈29 个零失败独立单元，我们不声称）。主动写清反而是加分——而且**"修复便宜、证书不便宜"本身正是我们的发现**。

**可借的理论工具**（把经验结论升级成有条件陈述）：LoBoost 的"局部标定规模足够大才有效"（说明我们只声称边际覆盖是对的）、OTCP 的"多变量联合证书"（把我们"四把尺子互相打架"从缺点改写成动机）、TRUST 的"用模拟数据做分布无关条件覆盖"（但需承担"模拟来自已坏模型"的风险，正好是我们 trap 那条）。
**不能碰的**：等变函数 ECE 界（Berman 2026）——3DGS 几何编辑不改等变性，硬套会被抓。

**一句必须写进 intro 的差异化陈述**（scout-cp 起草，我认可）：
> *Conformal failure modes studied so far change either the data distribution (shift), the score's parameterization (calibration), or the training objective (conformal training). In all of them exchangeability is either explicitly violated (and therefore watched for) or preserved by construction. Our regime removes the model's **capacity** while leaving the scene, camera path and α untouched: exchangeability remains formally satisfied, yet the score distribution has moved. That is why the certificate looks valid and is not.*

这句话同时挡住四路攻击（"扰动轴早研究过""OOD 覆盖早研究过""后处理早研究过""参数化敏感性早研究过"）。

### 4.3 评测侧：TMLR 接受"测量"，但同类合格样本都额外交了一件规范性产物

14 篇卡片归纳出 TMLR 的 5 种合法贡献形态：① 证伪标准检查 + 给修正量（Temporal Leakage，2026-11）；② 审计已发表物（AuditOwl，609 处不一致 / 120 条人工判 1.7% 错）；③ 复现（2026 年 11 篇带 Reproducibility 认证）；④ 协议敏感性 / 度量可靠性测量（4 篇）；⑤ 带保证的方法。
**我们是 ④ + ②，类型合法**。但**四篇 ④ 类无一例外都给了"该怎么做"**：Generalization Measures 给"把度量当 regime 相关排序信号"；Benchmarking Transfer Learning 给"标准化协议 + 组合 scorer"（且发现**源任务准确率这个平凡基线打败大多数花哨 scorer**）；Label-free Metrics 给"何时可靠、怎么解读"；Many Circuits 给"必须做 edge-level 评测"。
**我们只有两句规范性句式**（"certificate must carry the criterion"、"issue the certificate after the edit"），没有 checklist、没有推荐协议、没有修正分数。**这是成本最低、收益最大的一处补齐。**

同构度最高的三篇（直接可抄）：

| 论文 | 可抄什么 | 我们的差距 |
|---|---|---|
| **XFeat Revisited**（2026-08，Repro 认证） | 区分 re-evaluation vs reproduction；把"论文/补充材料/公开代码三者不一致 ⇒ **underspecified evaluation details**"做成一条独立贡献 | 我们只在 §3.3 报了倍数，**没有把"证书协议里还有哪些未写明自由度"列成清单**（我们其实已有三条：GT 归一化、交错 vs 分块划分、标定视角与优化视角不相交） |
| **Revisiting RegressionMSR**（2026-09） | **same-batch 2×2 因子设计**：4 个 cell 共享同一批 coalitions/folds/真值，只动 2 个协议轴 | 我们的 Table 4 本质就是同款（每留出视角只渲染一次 + 400 次划分共享随机性），**只是标题没这么写**——改表述即可 |
| **ShapeNet-55 matched-control audit**（2026-11，3D 点云） | 26 个检查点 SHA-256 + 212 份日志 + 一键脚本 + 配对种子 CI + 公开 ~99 GPU-h 预算；并自曝"发布检查点里存的 metrics 用的是另一套验证协议" | 我们有 437 条断言的校验脚本，**没有公开检查点清单/日志/一键复现包**，正文也没写 GPU 预算 |

**关于"工具"**：AuditOwl 这类审计论文的标准配置是**工具 + 人工精度评估**（11 人 × 30 组 × 120 条）。我们的 `main.tex` 里 `tool` **零命中**，`scripts/advise.py` 没进正文——**"measurement and tool" 里的 tool 在正文不存在**。要么补进正文，要么从定位里删掉，不能含糊。

---

### 4.4 与已有 related-work 调研的分工（避免两份文件打架）

`review/LITERATURE_SURVEY_2026-11.md` 回答的是"**全网有没有同题**"（arXiv 9 组查询 + OpenAlex 7 组 + Semantic Scholar + awesome-gaussian-skills 1066 条方法），结论是无同题、最近概念近邻是 **Doula & Mühlhäuser 2026（arXiv:2610.28937）的 inference-time model shift**，且已引。本报告回答的是"**TMLR 这个期刊最近发了什么、审稿人会拿什么量我们**"。两者不重叠，合起来是完整的两问。

但这里有一处**必须自己先处理掉的矛盾**，本报告在卡片里没有人提到：

- Doula & Mühlhäuser 说**推理配置变化（量化模式、serving 温度）导致的 conformal score 漂移会破坏 split-conformal 交换性**；
- 我们自己的 C2 说 **8-bit SH 量化对覆盖率是精确 no-op（q 增长 0.000）**。

审稿人只要同时读到这两句，就会问"你和它矛盾"。可核对的对齐方式（现成，只需写清楚）：**两者改的东西不在同一层**——他们的量化改的是**模型函数**（推理配置换了、输出真的变了），我们的 SH 8-bit 量化**在本管线里是精确 no-op**（存储精度与渲染消费精度一致，像素值逐位不变，因此它同时是我们的估计器噪声地板）。换句话说：**我们不是"量化不会破坏 CP"的反例，而是"没有真正改变函数时，CP 也不动"的负对照**。这句话应该出现在 C2 的讨论里，而不是留给审稿人去拼。

---

## 5. 差距矩阵（八维，逐维给判定与代价）

| # | 维度 | 我们 | TMLR 最近同类常态 | 判定 | 补齐代价 |
|---|---|---|---|---|---|
| 1 | **问题设定的空白** | "证书 × 资产编辑"交点 | 标题级扫描：全库 0 篇 conformal+3D、0 篇证书+3D、4 篇 Splat 无一做编辑后保证 | **我们赢，但只能说"标题级扫描无命中"**（漏检已知：Gaga 拼写错误；正文级复核未做，见 §7-1） | 0（写进 intro gap 句，措辞留余地） |
| 2 | **贡献形态** | 测量 + 两条 normative 句 | ④ 类四篇全部额外交"协议/判据/修正分数/checklist" | **我们输** | 低（checklist + 表述重组） |
| 3 | **理论落地** | 无理论界；"2 视角恢复"未区分保证与偏差校正 | 保形侧默认用 BPCI / 条件覆盖 / 非交换性说话；Coppola & Mazo 可直接打 | **我们输，且有硬伤风险** | 低（改两句措辞 + 引一篇） |
| 4 | **证据广度（外部效度）** | 4 资产、1 归档、1/4 分辨率、α=0.10 | DP-Splat 8 场景；Monocular Dynamic GS 多数据集+自建合成集；Label-free Metrics 260 模型×6 数据集；Are FMs good CP 17 模型 | **我们输（最实的一击）** | 高（补场景/第二归档，¥ 与时间） |
| 5 | **统计口径** | 重采样纪律：每场景 400 次划分 + 配对 2.5/97.5 分位 + 有效独立样本 77–508，明确不自称 CI；**但**任务侧数字无区间、36 格自我声明不作推断 | 保形侧审稿人（不是 3DGS 侧）用 BPCI / 条件覆盖给分；对比对象选错会虚高 | **净平**：重采样纪律赢、推断 warrant 输（红队修正了原来"我们赢、代价 0"的判定） | 中（给任务列补 bootstrap；与维度 3 合并处理） |
| 6 | **可复现交付** | 437 条断言校验脚本；无公开检查点/日志/一键包，正文无 GPU 预算 | ShapeNet-55 审计、RegressionMSR 验证闸门 | **我们输** | 中（工程） |
| 7 | **差异化陈述** | 目前没有一句把"交换性形式成立但分数分布已变"写成机制 | 保形侧每篇都有自己的失效机制句 | **我们输（缺一句关键句）** | 极低（加一句） |
| 8 | **文章类型与体裁** | 测量/分析类 | TMLR Scope 明文收录；2026 年 144 篇评测类、认证率 16% > 全刊 12.2%；3DGS 有 Survey 认证先例 | **我们赢，不需要伪装成方法论文** | 0 |

**一句话总结**（经红队修正后）：我们赢在**问题空白 + 体裁契合 + 重采样纪律**，输在**广度（维度 4）、交付形态（维度 2/6）、推断 warrant（维度 3/5）**；维度 2/3/5/7 全部是文字工作（含一处必须补的区间），维度 4 是真金白银。

---

## 6. 动作清单（按"投稿前是否必做"分档）

### A 档 · 投稿前必做，全是文字，不改实验（预计半天）

> 红队的优先级建议：**若只能做三条，做 A2 + A3 +（A8 与 A10 合并成一张表）**。A2 是唯一真正的硬伤修补；A3 用最便宜的文本动作把最大弱点换成"有边界、且边界做过实验的适用区间"；A8+A10 合并后是全文唯一能补上的可复用交付物。**A6 不建议先做**（正文明细见 `review/TMLR_REDTEAM.md` §3）。

| # | 动作 | 依据 |
|---|---|---|
| A1 | intro 加 §4.2 那句"capacity changed / exchangeability formally intact"的差异化陈述 | 挡四路攻击 |
| A2 | 把"2 个视角恢复"拆成 **①偏差校正（经验，有 400 次划分）②覆盖率保证（需 ≈29 个零失败独立单元，不声称）**，并引 Coppola & Mazo (TMLR 2025) | 把硬伤变成主动发现："修复便宜、证书不便宜" |
| A3 | 摘要/§5 加一句 **declared non-test**（Many Circuits 句式），并把"反例定适用区间"（从零短训 −0.8~+3.2 / 200k 再微调 −10.3~−12.9 / optimisation depth, not density）**上移到摘要** | 外部效度的最强素材现在埋在 §5 |
| A4 | Table 4 改写成"共享同一批像素 / 同一批划分的 2×2"，标题写清 same-batch | 对齐 RegressionMSR |
| A5 | 36 格扫描加一句"我们报配对分位，**不做显著性/FDR 声明**" | 对齐 Conformal Data Contamination 的 FDR 语言 |
| A6 | 引用 **DP-Splat** 作为"口径决定幅度"的**外部独立复现**（点空间 vs 全光栅化差 3.4–9.0 dB） | 我们最有力的新增引用：别人替我们作证 |
| A7 | 引用 **XFeat Revisited / RegressionMSR** 作为同层协议敏感性先例；引 **Monocular Dynamic GS** 作为 TMLR 体裁先例 | 让审稿人看到我们知道 TMLR 的基准 |
| A8 | 把"协议未写明自由度"列成**清单表**（GT 归一化、交错 vs 分块划分、标定/优化视角不相交、α 固定、区域粒度） | XFeat 的做法 |
| A9 | C2（敏感度准则优于 opacity）显式承认是 **AURA 结论在覆盖率指标上的复现**，而不是新发现 | `NOVELTY_AUDIT` 已判"不新"，现在会被抓 |
| A10 | 给"证书签发协议"一张 **checklist**（含三条判据 + 何时重签 + 需要几个视角 + 宽度代价） | 补维度 2，成本最低的规范性产物 |
| A11 | 在 C2 的 8-bit 讨论里补一句与已引 **Doula & Mühlhäuser（inference-time model shift）** 的对齐：他们改的是模型函数、我们的是精确 no-op 负对照 | 见 §4.4，否则是自相矛盾的一处 |

### B 档 · 小实验，1–3 天 / 少量算力

| # | 动作 | 封住哪一问 |
|---|---|---|
| B1 | 补 **4-bit / 6-bit SH 量化**一格 | "RAWDet-7 都测到 4-bit，你为什么只测 8-bit" |
| B2 | 补**平凡基线表**（fresh 覆盖率、精确 no-op 的 q 增长作为 baseline 行） | "你的代理指标比平凡基线强吗"（Benchmarking Transfer Learning 的立论方式） |
| B3 | 补 **2–4 个场景或第二个归档**（3DGS 公开场景成本低） | 维度 4，唯一治本的一击 |

### C 档 · 需要拍板的定位问题

| # | 决策 | 两个选项 |
|---|---|---|
| C1 | "工具"这一半 | ① 把 `scripts/advise.py` 补进正文并给一致性/精度数字（对齐 AuditOwl）；② 从"measurement and tool"定位里删掉 tool，只做测量 |
| C2 | 是否补一键复现包 | ① 出（检查点清单 + 日志 + 脚本 + GPU 预算）；② 不出，但 Limitations 显式认领（ShapeNet-55 审计已把标准抬到这里） |

### 不能说的话（负面清单，防止把把柄递给审稿人）

1. **禁用**"证书低估实际损失 2–12 倍 / −4.6pp vs −16.8pp"——论文 §3.4 已撤回（"not well posed"）。
2. **禁用**"TMLR 无人研究后处理破坏校准/不确定性"——至少三篇在（Rethinking Post-Hoc Calibration、Are FMs good CP、Small Updates Big Doubts）。
3. **禁用** Downshifting / FACTER / Hierarchical Sparse 三篇的任何内容——摘要未取到，只有标题级推断。
4. **不能说**"2 个视角就能给覆盖率保证"——见 A2。
5. **不能说**"剪 30% 掉 10.9–18.6pp"——那是附录 A 的 normalised 旧口径。

---

## 7. 红队复审：三条最可能的拒稿理由（比"差距"更紧迫，全文见 `review/TMLR_REDTEAM.md`）

一个独立红队（以"要拒这篇"的审稿人立场，只读 `main.tex` v4）给出的判断是：**危险的不是证据量，是主张的形态**——我们把两条可以被打成"同义反复"或"未建立"的主张放在摘要最前面，把三条能救命的材料放在附录。

| # | 拒稿理由（审稿人措辞） | 为什么这是我们与 TMLR 近邻的真正差距 | 最小修补 |
|---|---|---|---|
| **R1** | *"The authors' own mechanism paragraph shows a threshold statistic cannot track any task depending on sub-threshold structure; the measurement is a signature of a definition, not a finding."* | 我们 **§3.4 自己写了机制**（"This is a threshold effect, and the measurements above are its direct signature"），等于把 §3.4 的测量降格为定义的推论。TMLR 的 ④ 类论文（Generalization Measures / Many Circuits / XFeat）都在**给可反驳的量化结论**，没有一篇把结论写成自己的定义 | 把"certificate does not track utility"从**结论**降为**背景**，把真结论换成"**幅度跨任务不可迁移（0/36–36/36）+ 符号在编辑强度上非单调**"，摘要与 §3.4 各改 3 句 |
| **R2** | *"Every coverage number carries a 2.5/97.5 bracket and no task number carries any; the claimed reversal sits inside the coverage drop's own bracket."* | 这正是维度 5 里"推断 warrant 输"的具体形态：**Table 5 全表零区间**，而 Table 6 的 registration 列已经在用 view-level paired bootstrap——同一篇论文里两套标准。实测 50% 处 bicycle 差值 1.4–1.8 点落在覆盖率区间 [−7.0,−2.9] 内、flowers 1.2 点同量级 ⇒ **不分离**；只有 stump 5.4、treehill 4.6–7.3 分离 | 把 bootstrap 套到 task 列（前提：per-view 分数已存盘，**需作者确认**）；把"三/四个场景反转"改成"stump/treehill 分离、bicycle/flowers 不分离" |
| **R3** | *"The title is plural — 'Coverage Certificates' — yet only one object and one granularity is tested, and the other granularity sits unused in the same table."* | 我们自己在 §3.2 写"The region definition is a first-class choice, not a detail"，但 §3.4–§3.5 的解耦测试**只用 pixel**；而 Table 2 已有 block 列（treehill 10%：pixel −44.9 vs block −13.4，**3.35×**）。**粒度修正的方向本身随资产翻转**这件事我们从没说过——它同时是我们最强的自辩材料和最大的软肋 | 优先：标题/摘要限定为 **per-pixel marginal**，把 region 写成 scope condition；次选：Table 2 的 block 列与 Table 5 的任务列做并置小表（标注非配对） |

**红队发现的一处我们没意识到的弱点**（值得单独记一笔）：**Fig. 1 的"非线性"是阈值统计量的形状，不是剪枝的性质**。旧 q 下的覆盖率就是残差分布的 CDF 在 q 处的取值 $F_\text{edited}(q)$，**任何**把残差分布单调右移的编辑在 q 固定时都会给出"尾段平、穿过后陡"的形状；四组数（1.0/4.9/22.1/60.0、0.8/3.6/10.8/40.8、1.5/7.4/27.7/62.4、2.2/6.1/15.2/44.9）**同时符合**"q 已落进残差主体"和"删掉的基元越来越重要"两种解释，曲线本身不能判别。而 §3.4 的机制恰好就是前者——于是 §3.1 归因剪枝、§3.4 归因阈值，全文没缝合。修补只需文本：主张改成"编辑把残差分布右移、30% 处旧 q 已进主体"，补报 **q 与 median r 的比值**（Table 1 已有 median r）。

**这三条的性质与本报告 §5 的八个维度不同**：§5 是"与 TMLR 同行比我们缺什么"，§7 是"按 TMLR 的接受标准，我们的证据陈述会不会被直接打回"。红队的结论是：**R1/R2 危险、R3 可挡**，且 R1/R2 的修补都不需要新实验——只是**叙述层级的重排**。这与红队对我这份报告的修正方向一致（见下）。

---

## 8. 证据与限制（本报告自己的诚实边界）

1. **TMLR 全量索引是标题级的**：领域统计（3DGS 4 篇、conformal 22 篇、评测类 144 篇）都基于标题匹配，会漏掉"标题不含关键词但内容相关"的论文。已知漏例：Gaga 的标题拼写为 "Gausians"，未被 `gaussian` 匹配到。
2. **45 张卡片里 5 张完全未取到摘要**（3D 侧 2：Trip-to-Gaussian、点云综述；评测侧 3：Downshifting、FACTER、Hierarchical Sparse），另有 1 张只有 README/PDF 片段级证据（RegressionMSR）、1 张标题与月份冲突（Small Updates, Big Doubts）。根本原因是 OpenReview 被 Cloudflare 全面拦截。这些卡片只做标题级推断，**本文未把它们当事实使用**。
3. **保形侧的否定性结论范围**：严格限定在 46 条候选 + 17 张卡片内；"TMLR 无人研究参数后处理导致覆盖失效"这句话，我按全量标题扫描（conformal × 3D = 0、certificate × 3D = 0）支持其**3D 部分**，但**通用 ML 部分的"无人"未经全量正文核实**，不应写成绝对断言。
4. **我方数字全部来自 `review/WORK_PORTRAIT.md`**（其权威源为 `submission/final/main.tex` v4）；与 `DELIVERABLES.md`／`TMLR_GAP_BRIEF.md` 冲突处，一律以后者为准，冲突清单见 `WORK_PORTRAIT.md` §1。
5. **本报告没有改任何论文文件**。A 档动作需要在 `submission/final/main.tex` 上执行，并由 `tools/verify_tex_v3.py` 重跑 437 条断言——这是下一步，不是本报告已完成的。
6. **两条由 Lead 复核并确认的事实**（scout 卡里标为"待核"的）：
   - **剂量-反应的具体点数**：`main.tex` Table 2（`tab:dose`）bicycle 行为 **70/50/30/10% = −1.0 [−1.9,−0.3] / −4.9 [−7.0,−2.9] / −22.1 [−25.2,−18.8] / −60.0 [−62.1,−58.0]**，同一行 q 增长 **+4% / +23% / +105% / +325%**；其余三场景同表，30% 档为 flowers −10.8 / stump −27.7 / treehill −15.2。**这组数字已核，可引。**
   - **"Small Updates, Big Doubts"（CARDS_CP #12）标题/月份冲突**：判为**不可引**；"参数改动破坏校准"的先例功能由 **Rethinking Post-Hoc Calibration（#5）**承担，不影响任何结论。
7. **红队提出、本报告未解决的一处数字 nit**（需作者确认）：`main.tex` L193-195 报 split-to-split sd **0.013–0.034** 反算有效样本量得 **78–533**，而正文写 **77–508**；只有取 σ=0.0133–0.0342 才得 508。一个自带 437 条断言的稿件被审稿人手算对不齐不划算，建议把 sd 显示到三位小数。
8. **本报告已被红队修正过四处**（§0-6 的口径层级主张、§2.3 的认证率推断、§4.1 的 DP-Splat "复现"措辞、§5 第 1/5 维判定）；修正记录留在正文里，不删原文——因为"我们自己的报告也会过度自信"这件事本身就是这个项目最该记住的教训。


