# CVIU 体裁先例调研：measurement / evaluation / empirical-comparison 论文

**调研日期**：2026-11-12
**目标期刊**：Computer Vision and Image Understanding（CVIU），Elsevier / Academic Press，ISSN 1077-3142，E-ISSN 1090-235X
**用途**：为"非新方法、非新数据集"的 measurement 论文撰写 cover letter 时引用可核验的先例

---

## 0. 结论摘要（TL;DR）

1. **CVIU 有一整期以此为主题的专刊**：*Special Issue on Empirical Evaluation of Computer Vision Algorithms*，CVIU **84(1), pp. 1–199, October 2001**，1 篇 editorial + 10 篇正文，**全部为 evaluation / comparison，无一提出新算法**。这是最强、最难被审稿人反驳的先例（[ScienceDirect 期号页](https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/vol/84/issue/1)）。
2. 五个 genre 在 CVIU **均有可验证先例**。强度排序：**(a) comparison ≈ (b) evaluation-of-evaluation > (c) uncertainty/conformal > (d) 3D quality > (e) reproducibility/negative-result**。
3. CVIU 的 Aims & Scope **明文欢迎"不同于主流观点"的论文** —— 这是官方准入条款，不是我们的辩解：
   > "A wide range of topics in the image understanding area is covered, including papers offering insights that differ from predominant views."
   （来源：publisher page，见 §4.1）
4. **未找到任何 CVIU 官方 "novelty statement" 要求**。Elsevier 的 Highlights 指导语本身就写 "new methods that were used during the study **(if any)**"，且明确 "Not part of editorial consideration"（见 §4.2）。
5. **未取到**任何已发表的"CVIU 因无新方法/增量而拒稿"的记录（官方 editorial、博客、小木虫、知乎均未检索到可引用文本）。论坛层只有审稿慢、desk-reject 个案的零散描述（§4.3，**unverified**）。
6. CVIU 的 evaluation 论文有一条**结构性公约数**：几乎都自带 *unified protocol / benchmark / codebase* 或 *new metric*（§3）。这一点直接决定你的稿子该怎么包装（§5）。

---

## 1. 证据分级约定

本文所有条目按三级标注，**不允许跨级引用**：

| 级别 | 标签 | 含义 | 本文使用的来源 |
|---|---|---|---|
| A | `[P]` verified from publisher page | 直接从 Elsevier / ScienceDirect 页面抓取到的原文 | Guide for Authors、ScienceDirect 期号页、Elsevier Highlights 页 |
| B | `[M]` verified from Crossref / OpenAlex metadata | 由 DOI 注册元数据核验（title / authors / volume / pages / year / abstract） | `api.crossref.org`、`api.openalex.org`、`api.semanticscholar.org` |
| C | `[F]` unverified claim from a forum | 论坛、聚合站、博客；**只能作旁证，不能写进 cover letter** | 小木虫、LetPub/SciRev 聚合站、知乎 |

**关于年份的口径**：表中 `Year` 一律取 Crossref 的 `published-print` 年份（即卷期年）。Elsevier 的 online-first 年份常早一年，`DOI` 字符串里的年份也常是 online-first 年（例：`10.1016/j.cviu.2025.104575` 印在 v263，卷期年为 2026）。**引用时以卷期年为准**。

**关于页数**：2019 年之后 CVIU 改用 article number（如 `104575`），Crossref 不再给出 page range，因此新论文的页数标注为 **未取到**。这不是疏漏，是 metadata 事实。

---

## 2. Task 1 — 五个 genre 的可核验 CVIU 先例

### 2.1 (a) Comparison / benchmark of existing methods with **no new method**

| # | Title | Authors | Year | Vol | Pages | DOI | 一句话贡献 | 为何算该体裁 |
|---|---|---|---|---|---|---|---|---|
| a1 | Superpixels: An evaluation of the state-of-the-art | Stutz D.; Hermans A.; Leibe B. | 2018 | 166 | 1–27 | [10.1016/j.cviu.2017.03.007](https://doi.org/10.1016/j.cviu.2017.03.007) | 用统一 benchmark 评测 **28 个** SOTA superpixel 算法，显式讨论参数优化与 connectivity 强制，并扩展 metrics 使性能可与超像素数量解耦 | 不提出任何新 superpixel 算法；贡献完全是"评测 + 协议 + 指标改良"，27 页纯 evaluation |
| a2 | Systematic evaluation of convolution neural network advances on the Imagenet | Mishkin D.; Sergievskiy N.; Matas J. | 2017 | 161 | 11–19 | [10.1016/j.cviu.2017.05.007](https://doi.org/10.1016/j.cviu.2017.05.007) | 系统拆解 CNN 各设计选择（non-linearity / pooling / width / classifier / 预处理 / learning rate / batch size / 数据洁净度）对 ILSVRC 的影响，先单项后组合 | 无新网络、无新模块；结论是"个体增益之和 > 组合增益"这种**纯实证结论**，是 CVIU 版的 ablation-study 正刊论文 |
| a3 | An evaluation of crowd counting methods, features and regression models | Ryan D.; Denman S.; Sridharan S.; Fookes C. | 2015 | 130 | 1–17 | [10.1016/j.cviu.2014.07.008](https://doi.org/10.1016/j.cviu.2014.07.008) | 跨 **5 个公开数据集**（UCSD / PETS 2009 / Fudan / Mall / Grand Central）、K-fold 协议，比较 holistic vs local vs histogram 特征与 4 类回归器 | 明确以"以往工作跨数据集测试不足、难以比较"为动机，做的是**comparison infrastructure** |
| a4 | Comprehensive comparative evaluation of background subtraction algorithms in open sea environments | Chan Y.-T. | 2021 | 202 | 103101 | [10.1016/j.cviu.2020.103101](https://doi.org/10.1016/j.cviu.2020.103101) | 在海上场景下横向验证 **37 种** background subtraction 方法（从 temporal differencing 到深度模型），给出"哪种最适合 open sea"的选型结论 | 单作者、纯横向评测、结论是选型建议；无新 BS 算法 |
| a5 | A comparison of methods for 3D scene shape retrieval | Yuan J.; Abdul-Rashid H.; Li B.; Lu Y.; Schreck T.; Bai S.; Bai X.; Bui N.-M. 等 | 2020 | 201 | 103070 | [10.1016/j.cviu.2020.103070](https://doi.org/10.1016/j.cviu.2020.103070) | 汇总 2018/2019 两届 SHREC 3D scene retrieval track 的参赛方法，在两个 benchmark 上做统一 comprehensive comparison | 组织者视角的 benchmark/comparison 报告，贡献是"比较结果 + benchmark"，不是新检索算法 |
| a6 | Comparison of Edge Detectors | Heath M.; Sarkar S.; Sanocki T.; Bowyer K. | 1998 | 69(1) | 38–54 | [10.1006/cviu.1997.0587](https://doi.org/10.1006/cviu.1997.0587) | 在统一协议下比较多种 edge detector 的表现 | CVIU 早期的纯 comparison 论文，且是 2001 专刊同一批作者的 methodological 脉络起点 |
| a7 | A comparative study of state-of-the-art evolutionary image registration methods for 3D modeling | Santamaría J.; Cordón O.; Damas S. | 2011 | 115(9) | 1340–1354 | [10.1016/j.cviu.2011.05.006](https://doi.org/10.1016/j.cviu.2011.05.006) | 对当时 SOTA 的 evolutionary image registration 方法做统一比较，服务于 3D modeling | 标题即 "comparative study of state-of-the-art"，无新 registration 算法 |
| a8 | Calibration of omnidirectional cameras in practice: A comparison of methods | Puig L.; Bermúdez J.; Sturm P.; Guerrero J.J. | 2012 | 116(1) | 120–137 | [10.1016/j.cviu.2011.08.003](https://doi.org/10.1016/j.cviu.2011.08.003) | 在"实践"设定下比较全向相机标定方法 | 比较型论文，且明确以 "in practice" 为价值主张（= 实用性而非新颖性） |

**小结**：(a) 是 CVIU 最稳的体裁。跨度 1998→2021，且 **2020/2021 仍有 a4、a5 两篇**，说明不是历史遗留。

---

### 2.2 (b) Evaluation of evaluation（批判/测量既有 metric 与 protocol 的可靠性）

| # | Title | Authors | Year | Vol | Pages | DOI | 一句话贡献 | 为何算该体裁 |
|---|---|---|---|---|---|---|---|---|
| b1 | Special Issue on Empirical Evaluation of Computer Vision Algorithms（editorial） | Flynn P.J.; Hoover A.; Phillips P.J. | 2001 | 84(1) | 1–4 | [10.1006/cviu.2001.0948](https://doi.org/10.1006/cviu.2001.0948) | 为整期 evaluation 专刊定调：empirical evaluation 本身是计算机视觉的一等研究议题 | 期刊层面的制度性承认：CVIU 曾用**整期**资源出版 evaluation 方法论 |
| b2 | On Benchmarking Optical Flow | McCane B.; Novins K.; Crannitch D.; Galvin B. | 2001 | 84(1) | 126–143 | [10.1006/cviu.2001.0930](https://doi.org/10.1006/cviu.2001.0930) | 直接质疑 optical flow 的 benchmarking 实践本身（数据、误差度量、可比性） | 标题即"对 benchmark 的 benchmark"；不提出新 flow 算法 |
| b3 | Edge Detector Evaluation Using Empirical ROC Curves | Bowyer K.; Kranenburg C.; Dougherty S. | 2001 | 84(1) | 77–103 | [10.1006/cviu.2001.0931](https://doi.org/10.1006/cviu.2001.0931) | 把 ROC 分析引入 edge detector 评价，主张单一阈值点指标不足 | 研究对象是**评价方法**，不是检测器 |
| b4 | Evaluating 2D Image Comparison Metrics for 3D Scene Interpretation | Stevens M.R. | 2001 | 84(1) | 179–197 | [10.1006/cviu.2001.0940](https://doi.org/10.1006/cviu.2001.0940) | 检验"2D 图像比较指标"是否真的能预测 3D 场景解释的质量 | **元评价**的教科书样本：测的是 metric 与目标任务效用的关系 |
| b5 | Comparison of Edge Detector Performance through Use in an Object Recognition Task | Shin M.C.; Goldgof D.B.; Bowyer K.W. | 2001 | 84(1) | 160–178 | [10.1006/cviu.2001.0932](https://doi.org/10.1006/cviu.2001.0932) | 把 edge detector 的排名放到**下游识别任务**里重新检验，而非用 edge 指标本身 | 与你的"certificate 不追踪 downstream task utility"**结构完全同构**的先例 |
| b6 | An object-based comparative methodology for motion detection based on the F-Measure | Lazarevic-McManus N.; Renno J.R.; Makris D.; Jones G.A. | 2008 | 111(1) | 74–85 | [10.1016/j.cviu.2007.07.007](https://doi.org/10.1016/j.cviu.2007.07.007) | 指出 F-Measure 在 motion detection 上的评价缺陷，并提出 object-based 的比较方法学 | 研究对象是"怎么算分"，且明确指出常用指标的失效模式 |
| b7 | Comparison of monocular depth estimation methods using geometrically relevant metrics on the IBims-1 dataset | Koch T.; Liebel L.; Körner M.; Fraundorfer F. | 2020 | 191 | 102877 | [10.1016/j.cviu.2019.102877](https://doi.org/10.1016/j.cviu.2019.102877) | 论证既有 depth 评价"只考虑 depth residual 的全局统计量"，提出几何相关的新 criteria，并在新采数据集上重排 SOTA | abstract 原文即攻击 evaluation scheme 本身："established evaluation schemes of predicted depth maps are still limited, as they only consider global statistics of the depth residuals" |
| b8 | Gloss-free Sign Language Translation: An unbiased evaluation of progress in the field | Sincan O.M.; Low J.H.; Asasi S.; Bowden R. | 2025 | 261 | 104498 | [10.1016/j.cviu.2025.104498](https://doi.org/10.1016/j.cviu.2025.104498) | 在统一 codebase 里复现 gloss-free SLT 的关键贡献，标准化预处理/encoder/训练，检验"报告的性能提升到底来自方法还是 setup" | **最新、最纯粹的 evaluation-of-evaluation**：结论是 gains "often diminish when models are evaluated under consistent conditions" |
| b9 | Establishing a unified evaluation framework for human motion generation: A comparative analysis of metrics | Ismail-Fawaz A.; Devanne M.; Berretti S.; Weber J.; Forestier G. | 2025 | 254 | 104337 | [10.1016/j.cviu.2025.104337](https://doi.org/10.1016/j.cviu.2025.104337) | 逐条审查 8 个 human motion generation 指标，指出各自 "unique features and shortcomings"，并给出统一评测 setup | 对象是 **metrics 本身**；贡献是"评价框架"而非生成模型 |
| b10 | Superpixel segmentation: A long-lasting ill-posed problem | Giraud R.; Clément M. | 2026 | 270 | 104831 | [10.1016/j.cviu.2026.104831](https://doi.org/10.1016/j.cviu.2026.104831) | 论证 superpixel 分割在评价层面是长期 ill-posed 的 | 标题即"评价问题是 ill-posed"，2026 年新证据说明该体裁仍在活跃 |
| b11 | RAIN: An embarrassingly simple approach to debiasing attribution evaluation | Duan J.; Song J.; Zhang H.; Xue M.; Wang H.; Song M. | 2026 | 268 | 104773 | [10.1016/j.cviu.2026.104773](https://doi.org/10.1016/j.cviu.2026.104773) | 指出 attribution 评测存在偏差，并用一个"embarrassingly simple"的做法去偏 | 先把既有 evaluation 的偏差量出来，再给最小修正——典型 "evaluation is broken" 叙事 |

**关键观察**：b5（Shin et al. 2001）与 b4（Stevens 2001）两篇，本质上就是"**指标排名在下游任务下不成立**"的实证。你的核心 claim（coverage certificate 与 downstream utility 脱钩）在 CVIU 有一条 25 年长的同构脉络。

---

### 2.3 (c) Uncertainty / confidence / calibration / conformal prediction

| # | Title | Authors | Year | Vol | Pages | DOI | 一句话贡献 | 为何算该体裁 |
|---|---|---|---|---|---|---|---|---|
| c1 | Trustworthy medical imaging: Conformal prediction with adversarial guarantees | Luo R.; Bao J.; Zhou Z.; Dang C.; Colombo N.; Cao S. | 2026 | 273 | 104964 | [10.1016/j.cviu.2026.104964](https://doi.org/10.1016/j.cviu.2026.104964) | 在多种 conformal prediction 方法 + 组合对抗攻击下保证 **valid coverage**，MedMNIST 三个子集验证 | **CVIU 已发表 conformal prediction 论文，且核心词就是 "coverage"** —— 与你的 coverage certificate 同一术语体系 |
| c2 | Picture the suspect: Conformal soft-biometric triage across faces and pedestrians | Fatima N.; Ahmed M. | 2026 | 271 | 104870 | [10.1016/j.cviu.2026.104870](https://doi.org/10.1016/j.cviu.2026.104870) | 用 conformal prediction 做跨人脸/行人的 soft-biometric triage | 第二篇 2026 conformal 论文，说明这不是一次性 outlier |
| c3 | Multimodal vs. unimodal approaches to uncertainty in 3D image segmentation under distribution shifts | Javanbakhat M.; Hasan M.T.; Lippert C. | 2025 | 260 | 104473 | [10.1016/j.cviu.2025.104473](https://doi.org/10.1016/j.cviu.2025.104473) | 比较 3 种 uncertainty estimation 方法（unimodal vs multimodal posterior）在 distribution shift 下的可靠性 | **比较型 uncertainty 论文**：同时命中 (a) 与 (c)，结论是"哪类方法在 shift 下不可靠"——负面结论被接受 |
| c4 | Stochastic BIQA: Median randomized smoothing for certified blind image quality assessment | Shumitskaya E.; Pautov M.; Vatolin D.; Antsiferova A. | 2025 | 259 | 104447 | [10.1016/j.cviu.2025.104447](https://doi.org/10.1016/j.cviu.2025.104447) | 给 blind IQA 提供 **certified**（randomized smoothing）鲁棒性保证 | 把 "certificate" 语言用在**质量度量**上；CVIU 接受"给一个度量配证书"的选题 |
| c5 | Bootstrap optical flow confidence and uncertainty measure | Kybic J.; Nieuwenhuis C. | 2011 | 115(10) | 1449–1462 | [10.1016/j.cviu.2011.06.008](https://doi.org/10.1016/j.cviu.2011.06.008) | 用 bootstrap 为重采样给 optical flow 输出配 confidence/uncertainty | 早期 per-estimate uncertainty 的经典；方法学而非新 flow 算法 |
| c6 | Measuring uncertainty in graph cut solutions | Kohli P.; Torr P.H.S. | 2008 | 112 | 30–38 | [10.1016/j.cviu.2008.07.002](https://doi.org/10.1016/j.cviu.2008.07.002) | 量化 graph-cut 解的不确定性 | 同上：uncertainty 作为一等研究对象 |
| c7 | Quantifying model uncertainty for semantic segmentation of Fluorine-19 MRI using stochastic gradient MCMC | Javanbakhat M.; Starke L.; Waiczies S.; Lippert C. | 2024 | 241 | 103967 | [10.1016/j.cviu.2024.103967](https://doi.org/10.1016/j.cviu.2024.103967) | 用 SG-MCMC 量化分割模型不确定性 | 纯 uncertainty quantification 选题 |
| c8 | Head pose estimation with uncertainty and an application to dyadic interaction detection | Figari Tomenotti F.; Noceti N.; Odone F. | 2024 | 243 | 103999 | [10.1016/j.cviu.2024.103999](https://doi.org/10.1016/j.cviu.2024.103999) | 输出带不确定性的 head pose，并把不确定性传到下游任务 | "uncertainty 是否对下游有用"的 CVIU 版本 |

**注意**：CVIU 的 calibration 论文大多是 **camera calibration**（几何标定），不是 confidence calibration。做 confidence/coverage 方向时必须用 c1–c3 这类词（conformal / uncertainty / coverage / triage），**避免让编辑在标题里看到 "calibration" 而误判为几何标定**。这是本次检索发现的一个实际风险点（OpenAlex 中 `calibration` 命中 52 篇，绝大多数是相机标定）。

---

### 2.4 (d) 3D / rendering quality assessment

| # | Title | Authors | Year | Vol | Pages | DOI | 一句话贡献 | 为何算该体裁 |
|---|---|---|---|---|---|---|---|---|
| d1 | Evaluating the effect of image quantity on Gaussian Splatting: A statistical perspective | Dalal A.; Hagen D.; Robbersmyr K.G.; Knausgård K.M. | 2026 | 263 | 104575 | [10.1016/j.cviu.2025.104575](https://doi.org/10.1016/j.cviu.2025.104575) | 构造 UnrealGaussianStat，对"减少视角数 / 均匀 vs 随机布点"对 3DGS 质量的影响做统计分析，发现相机数超过 ~100 后指标饱和，并拟合出精度随相机数衰减的函数 | **CVIU 已发表"3DGS 输入变量 → 质量指标"的纯测量论文**；它明确说动机是"现有公开数据集不适合做这类统计分析" |
| d2 | A comprehensive overview of methodologies and performance evaluation frameworks in 3D mesh segmentation | Theologou P.; Pratikakis I.; Theoharis T. | 2015 | 135 | 49–82 | [10.1016/j.cviu.2014.12.008](https://doi.org/10.1016/j.cviu.2014.12.008) | 34 页，系统梳理 3D mesh segmentation 的方法学与**性能评价框架** | 以"评价框架"为主语的 3D 长文，CVIU 给足了篇幅 |
| d3 | Error-aware construction and rendering of multi-scan panoramas from massive point clouds | Comino M.; Andújar C.; Chica A.; Brunet P. | 2017 | 157 | 43–54 | [10.1016/j.cviu.2016.09.011](https://doi.org/10.1016/j.cviu.2016.09.011) | 把点云误差模型一路传到重建与渲染，做 error-aware 的构建与绘制 | 研究"误差/质量如何在 3D 管线中传播"，与"编辑后证书失效"同构 |
| d4 | 3D reconstruction of cultural heritages: Challenges and advances on precise mesh integration | Santos Junior J. de O.; Vrubel A.; Bellon O.R.P.; Silva L. | 2012 | 116 | 1195–1207 | [10.1016/j.cviu.2012.08.005](https://doi.org/10.1016/j.cviu.2012.08.005) | 讨论文化遗产 3D 重建中 mesh 集成的精度评估与挑战 | 3D 几何质量评估的应用型先例 |
| d5 | Underwater image quality evaluation via deep meta-learning: Dataset and objective method | Chen T.; Yang X.; Wang T.; Li N.; Zhu S.; Shen X. | 2025 | 257 | 104380 | [10.1016/j.cviu.2025.104380](https://doi.org/10.1016/j.cviu.2025.104380) | 提出水下 IQA 数据集 + objective quality method | **不是 3D，但证明 CVIU 收 "quality assessment" 作为主标题的论文**（image quality 而非 rendering quality） |

**诚实的缺口**：CVIU **没有** dedicated point-cloud / mesh / radiance-field **quality-assessment benchmark** 传统（检索 `point cloud quality assessment`、`mesh quality assessment` 在标题+摘要层面几乎零命中；命中的都是"用 mesh 质量约束做重建"这类方法论文）。做 (d) 时最可靠的锚点是 **d1（3DGS 统计评估）** 与 **d2（评价框架综述）**，不要声称"CVIU 是 3D QA 的主场"。

---

### 2.5 (e) Reproducibility / negative-result / "what does not work"

**重要事实**（OpenAlex source `S185008460`，全刊 4,345 篇，2026-11-12 核验）：

| 标题检索式 | 命中数 |
|---|---|
| `title.search:reproduc` | **0** |
| `title.search:reproducible` | **0** |
| `title.search:replicat` | **0** |
| `title.search:benchmark` | **20** |
| `title.search:comparison` | **16** |

也就是说 **CVIU 没有以 "reproducibility / replication" 为标题的论文**——这个 genre 在 CVIU 是**以别的词存在的**（`unbiased evaluation` / `reality check` / `ill-posed` / `good practices`）。这也是为什么 §2.5 的六篇要按"实际用词"而不是按"genre 名"来找：

| # | Title | Authors | Year | Vol | Pages | DOI | 一句话贡献 | 为何算该体裁 |
|---|---|---|---|---|---|---|---|---|
| e1 | Gloss-free Sign Language Translation: An unbiased evaluation of progress in the field | Sincan O.M.; Low J.H.; Asasi S.; Bowden R. | 2025 | 261 | 104498 | [10.1016/j.cviu.2025.104498](https://doi.org/10.1016/j.cviu.2025.104498) | 统一 codebase 复现后发现"文献中报告的大量提升在一致条件下会消失" | **事实上的 negative result**：结论是"此前的进展被高估"，且公开 codebase（reproducibility 的实际载体） |
| e2 | Survey: How good are the current advances in image set based face identification? – Experiments on three popular benchmarks with a naïve approach | Chen L.; Hassanpour N. | 2017 | 160 | 1–23 | [10.1016/j.cviu.2017.03.004](https://doi.org/10.1016/j.cviu.2017.03.004) | 用一个"naïve approach"在三个 benchmark 上反测当前 advances 到底有多强 | 标题就是反问句 + "naïve baseline"，典型的 reality-check 论文；23 页给了充足篇幅 |
| e3 | Multimodal vs. unimodal approaches to uncertainty in 3D image segmentation under distribution shifts | Javanbakhat M.; Hasan M.T.; Lippert C. | 2025 | 260 | 104473 | [10.1016/j.cviu.2025.104473](https://doi.org/10.1016/j.cviu.2025.104473) | 结论明确"哪一类 uncertainty 方法在 shift 下不可靠" | 负面结论（unimodal 失败）作为主要卖点被接受 |
| e4 | A formal approach to good practices in Pseudo-Labeling for Unsupervised Domain Adaptive Re-Identification | Dubourvieux F.; Audigier R.; Loesch A.; Ainouz S.; Canu S. | 2022 | 223 | 103527 | [10.1016/j.cviu.2022.103527](https://doi.org/10.1016/j.cviu.2022.103527) | 用形式化方法给出 pseudo-labeling 的"good practices" | **方法论/规范类**论文：贡献是"应该怎么做"，不是"我做了什么新模块" |
| e5 | Superpixel segmentation: A long-lasting ill-posed problem | Giraud R.; Clément M. | 2026 | 270 | 104831 | [10.1016/j.cviu.2026.104831](https://doi.org/10.1016/j.cviu.2026.104831) | 论证该任务的评价是长期 ill-posed | 与 e1 同构：否定"我们已在该任务上取得进展"这一前提 |
| e6 | RAIN: An embarrassingly simple approach to debiasing attribution evaluation | Duan J. et al. | 2026 | 268 | 104773 | [10.1016/j.cviu.2026.104773](https://doi.org/10.1016/j.cviu.2026.104773) | 既有 attribution 评测有偏；一个极简做法即可去偏 | 隐含"复杂方法并不必要"的 negative 结论 |

**给 cover letter 的用词建议**：不要写 "reproducibility study" 或 "negative result"（CVIU 无此标题先例，编辑可能判为 out of scope）。改写为 **"unbiased evaluation"**（e1 原词）、**"reality check / how good are current advances"**（e2 原词）、**"what the metric does not track"**（b4/b5 脉络）、**"good practices"**（e4 原词）。这是本次调研最有操作价值的一条发现。

---

### 2.6 专节：CVIU 84(1) 2001 —— 一整期 evaluation 专刊（最强先例）

期号页 `[P]`：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/vol/84/issue/1>（"Volume 84, Issue 1, Pages 1-199 (October 2001)"）

| Pages | DOI | Title | Authors |
|---|---|---|---|
| 1–4 | [10.1006/cviu.2001.0948](https://doi.org/10.1006/cviu.2001.0948) | Special Issue on Empirical Evaluation of Computer Vision Algorithms（editorial） | Flynn P.J.; Hoover A.; Phillips P.J. |
| 5–24 | [10.1006/cviu.2001.0938](https://doi.org/10.1006/cviu.2001.0938) | Experimental Evaluation of FLIR ATR Approaches—A Comparative Study | Li B.; Chellappa R.; Zheng Q.; Der S.; Nasrabadi N.; Chan L.; Wang L. |
| 25–43 | [10.1006/cviu.2001.0934](https://doi.org/10.1006/cviu.2001.0934) | Empirical Evaluation of Dissimilarity Measures for Color and Texture | Rubner Y.; Puzicha J.; Tomasi C.; Buhmann J.M. |
| 44–61 | [10.1006/cviu.2001.0935](https://doi.org/10.1006/cviu.2001.0935) | Measuring the Performance of Shape Similarity Retrieval Methods | Carlin M. |
| 62–76 | [10.1006/cviu.2001.0941](https://doi.org/10.1006/cviu.2001.0941) | Analysis of Irregularly Shaped Texture Regions | García-Sevilla P.; Petrou M. |
| 77–103 | [10.1006/cviu.2001.0931](https://doi.org/10.1006/cviu.2001.0931) | Edge Detector Evaluation Using Empirical ROC Curves | Bowyer K.; Kranenburg C.; Dougherty S. |
| 104–125 | [10.1006/cviu.2001.0939](https://doi.org/10.1006/cviu.2001.0939) | Performance Prediction Analysis of a Point Feature Tracker Based on Different Motion Models | Tissainayagam P.; Suter D. |
| 126–143 | [10.1006/cviu.2001.0930](https://doi.org/10.1006/cviu.2001.0930) | On Benchmarking Optical Flow | McCane B.; Novins K.; Crannitch D.; Galvin B. |
| 144–159 | [10.1006/cviu.2001.0933](https://doi.org/10.1006/cviu.2001.0933) | Performance Evaluation of Document Structure Extraction Algorithms | Liang J.; Phillips I.T.; Haralick R.M. |
| 160–178 | [10.1006/cviu.2001.0932](https://doi.org/10.1006/cviu.2001.0932) | Comparison of Edge Detector Performance through Use in an Object Recognition Task | Shin M.C.; Goldgof D.B.; Bowyer K.W. |
| 179–197 | [10.1006/cviu.2001.0940](https://doi.org/10.1006/cviu.2001.0940) | Evaluating 2D Image Comparison Metrics for 3D Scene Interpretation | Stevens M.R. |

**cover letter 可直接用的一句话**（把 DOI 全部列出即可，审稿人无法反驳）：

> CVIU has a sustained record of publishing evaluation-methodology work as first-class research, including an entire special issue dedicated to it (*Special Issue on Empirical Evaluation of Computer Vision Algorithms*, CVIU 84(1), 2001, pp. 1–199), and it continues to do so in 2025–2026 (e.g., 10.1016/j.cviu.2025.104498; 10.1016/j.cviu.2025.104337; 10.1016/j.cviu.2025.104575).

---

## 3. Task 2 — CVIU evaluation 论文的结构解剖

挑选 8 篇最强、且 `[M]` 级别元数据完整者。**引用的贡献句均为 abstract 逐字原文**（来自 Crossref/OpenAlex/Semantic Scholar 的摘要字段）。

| # | 论文（简称） | 页数 | 数据集 / 场景数 | 新 metric 或 protocol? | 用户研究? | 代码? |
|---|---|---|---|---|---|---|
| 1 | Superpixels (2018) | **27**（1–27） | 未取到（abstract 未给数据集数量；给的是 **28 个算法**） | ✅ 扩展 metrics + benchmark protocol（fair comparison、参数优化、强制 connectivity） | 摘要未声明 → 未取到 | 摘要未声明 → 未取到 |
| 2 | Systematic evaluation of CNN advances (2017) | **9**（11–19） | 1（ILSVRC/ImageNet） | ❌ 无新 metric，纯 ablation 协议 | 摘要未声明 → 未取到 | 摘要未声明 → 未取到 |
| 3 | Crowd counting evaluation (2015) | **17**（1–17） | **5**（UCSD / PETS 2009 / Fudan / Mall / Grand Central） | ✅ K-fold cross-validation protocol + 特征/回归器分类法 | 摘要未声明 → 未取到 | 摘要未声明 → 未取到 |
| 4 | MDE comparison on IBims-1 (2020) | 未取到（article no. 102877） | 1 个新采数据集（IBims-1）+ 若干 SOTA 方法 | ✅ 一组几何相关新 criteria（depth discontinuity、planar region、跨图一致性、距离相关） | 摘要未声明 → 未取到 | 摘要未声明 → 未取到 |
| 5 | 3D scene shape retrieval comparison (2020) | 未取到（103070） | **2** 个 benchmark（2018 版 10 类 / 2019 扩展版 30 类），4+5 与 2+3 个方法 | ✅ benchmark + 可扩展性 protocol | 摘要未声明 → 未取到 | 摘要未声明 → 未取到 |
| 6 | Gloss-free SLT unbiased evaluation (2025) | 未取到（104498） | 未取到（abstract 未列数据集） | ✅ **unified codebase** = 可复现 protocol（标准化 preprocessing / encoder / training） | 摘要未声明 → 未取到 | ✅ 摘要给出 `github.com/ozgemercanoglu/sltbaselines` |
| 7 | Unified eval framework for HMG (2025) | 未取到（104337） | **2** 个公开数据集 + **3** 个生成模型 | ✅ 统一 setup + 1 个新 metric（warping diversity / temporal distortion diversity） | 摘要未声明 → 未取到 | ✅ 摘要给出 `github.com/MSD-IRIMAS/Evaluating-HMG` |
| 8 | Image quantity × 3DGS (2026) | 未取到（104575） | **1** 个新数据集（UnrealGaussianStat）（场景数未取到） | ✅ 统计协议 + 拟合函数（accuracy vs 相机数） | 摘要未声明 → 未取到 | 摘要未声明 → 未取到 |

### 3.1 逐字贡献句（verbatim，供模仿句式）

1. **Superpixels (2018)** — *"We present a comprehensive evaluation of 28 state-of-the-art superpixel algorithms utilizing a benchmark focussing on fair comparison and designed to provide new insights relevant for applications."*
2. **Systematic evaluation of CNN advances (2017)** — *"The paper systematically studies the impact of a range of recent advances in convolution neural network (CNN) architectures and learning methods on the object categorization (ILSVRC) problem."*
3. **Crowd counting evaluation (2015)** — *"This paper presents an evaluation across multiple datasets to compare holistic, local and histogram based methods, and to compare various image features and regression models."*
4. **MDE comparison (2020)** — *"In order to allow for a geometry-aware analysis, we propose a set of novel quality criteria addressing the preservation of depth discontinuities and planar regions, the depth consistency across the image, and a distance-related assessment."*（同段前句：*"established evaluation schemes of predicted depth maps are still limited, as they only consider global statistics of the depth residuals"*）
5. **3D scene shape retrieval (2020)** — *"To solicit state-of-the-art approaches, we perform a comprehensive comparison of all the above methods and an additional new retrieval methods by evaluating them on the two benchmarks…"*
6. **Gloss-free SLT (2025)** — *"This paper presents a comprehensive study of recent gloss-free SLT models by re-implementing key contributions in a unified codebase."*
7. **HMG unified evaluation (2025)** — *"This paper presents a detailed review of eight evaluation metrics for human motion generation, highlighting their unique features and shortcomings."*
8. **3DGS image quantity (2026)** — *"In this paper UnrealGaussianStat dataset is introduced, and a statistical analysis is performed on decreasing viewpoints have on gaussian splatting."*（原文语法略有瑕疵，逐字照录）。同篇 Highlights：*"Quantifying the effect of reducing the number of cameras have on the performance metrics for gaussian splatting by performing statistical analysis."*

### 3.2 从这 8 篇提炼出的"CVIU evaluation 论文长什么样"

| 维度 | 观察到的公约数 | 对你的含义 |
|---|---|---|
| **页数** | 可用元数据的为 **9 / 17 / 27 页**；2001 专刊论文 15–27 页；3D 综述类达 **34 页**（d2）。article-number 时代无法从 metadata 取页数 | 目标 **18–26 页**正文 + 补充材料。低于 12 页容易被判"不够一篇 journal paper" |
| **数据集/场景数** | 1（Mishkin, IBims-1, 3DGS）→ 5（crowd counting）→ 28 算法 / 37 方法。**没有"必须 ≥N 个数据集"的门槛** | 你的 **9 scenes** 在数量上不是短板；短板会被说成"只有 4 个是公开 asset"。**必须把 400 calibration splits 的统计功效写成主角** |
| **新 metric / protocol** | **8 篇里 6 篇有**（1,3,4,5,6,7,8）。唯一没有的是纯 ablation 的 Mishkin | ⚠️ **最关键的一条**：CVIU 接受"没有新方法"，但几乎不接受"没有新 protocol/metric"。你的 **494 automated assertions + one-click reproduction script** 就是 protocol，必须升格为贡献条目，而不是"附录里的工程细节" |
| **用户研究** | 8 篇摘要**均未声明** human/user study | 不必做 user study；做了也不是加分主项 |
| **代码** | 2025 年后的两篇（6,7）**都在摘要里给了 GitHub URL**；较早的未声明 | 2025+ 的规范是**摘要直接写 URL**。建议照做 |
| **贡献句句法** | 主动词：*present a comprehensive evaluation / systematically studies the impact of / presents an evaluation across / we perform a comprehensive comparison / presents a comprehensive study … by re-implementing*。宾语是 **"the impact/effect of X on Y"** 或 **"N methods"**。**从不出现 "we propose a novel …"** | 你的贡献句应写成 *"We measure the effect of asset edits (pruning / quantisation) on the validity of a distribution-free coverage certificate for 3D Gaussian Splatting."* 而不是 "We propose a certificate audit framework" |
| **动机句** | 高频句式：*"X remain unclear / are still limited / hindered the development of a unifying benchmark"* | 你的动机句：*"whether the certificate survives asset editing remains unmeasured"* |

---

## 4. Task 3 — 显式的拒稿风险证据

### 4.1 `[P]` CVIU Guide for Authors：官方对"非主流观点"的准入条款

抓取自 <https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/publish/guide-for-authors>（2026-11-12，HTTP 200）：

**Aims and scope（逐字）**：
> "The central focus of this journal is the computer analysis of pictorial information. Computer Vision and Image Understanding publishes papers covering all aspects of image analysis from the low-level, iconic processes of early vision to the high-level, symbolic processes of recognition and interpretation. A wide range of topics in the image understanding area is covered, **including papers offering insights that differ from predominant views**."

**Peer review（逐字）**：
> "This journal follows a single anonymized review process. **Your submission will initially be assessed by our editors.** If your submission is deemed suitable, it will typically be sent to be reviewed by a minimum of two reviewers for an independent expert assessment of the scientific quality. Our editors decide whether to accept or reject your article."

**判读**：
- ✅ 有**编辑初筛（desk screening）**，措辞是 "deemed suitable" —— 未定义标准，因此 scope 判断是编辑自由裁量。
- ✅ Aims & scope 明文欢迎 "insights that differ from predominant views"，这是**唯一**一条能直接支撑"非主流/批判性"论文的官方文本，务必在 cover letter 引用。
- ❌ **在该页面可抓取到的章节中（About the journal / Ethics and policies，至 "Delayed publication" 为止）不存在任何 "novelty statement" / "novel contribution" 要求**。页面后半（Writing and formatting 及之后）**未取到**（web_fetch 在该处截断），因此"全文无 novelty 要求"这一更强断言应标注为 **未取到**。

### 4.2 `[P]` Elsevier 官方 Highlights 指导：novelty 不是 editorial 门槛

抓取自 <https://www.elsevier.com/researcher/author/tools-and-resources/highlights>（2026-11-12，HTTP 200）：

> "Highlights are three to five … bullet points that help increase the discoverability of your article via search engines. These bullet points should capture **the novel results of your research as well as new methods that were used during the study (if any)**."

> "**The small print** — **Not part of editorial consideration** and not required until the final files stage."

**判读**：这是比 Guide for Authors 更硬的反证。
1. "**new methods … (if any)**" —— 官方措辞本身允许"没有新方法"。
2. "**Not part of editorial consideration**" —— 即使写了 Highlights，也不进入编辑决策。

### 4.3 `[F]` 论坛 / 聚合站（**unverified，仅供风险评估，不可引用**）

| 来源 | 内容 | 可靠性 |
|---|---|---|
| [minicod 聚合页](https://www.minicod.com/journals/computer-vision-and-image-understanding-9cf81d80)（聚合 LetPub / SciRev，47 条投稿记录，页面自述"Treat it as a rough guide"） | Acceptance rate **79%**、Rejection **21%**、Desk rejections **7%**；first review median **183 天**；一条 2025-11-06 的 "Desk rejected" 记录称"审稿意见明显不错，但主编直接拒了" | 低。样本 47，自选样本偏差极大；**不构成"因无新方法被拒"的证据** |
| [小木虫 CVIU 期刊页](https://muchong.com/bbs/journal.php?view=detail&jid=2010)（21 人参与，75k 阅读） | 全部是审稿周期抱怨：平均 13 个月；一条明确写"三次修改补充，弄到 **30 多页**" | 低。但"改到 30 多页"这条旁证支持 §3.2 的页数预期 |
| [知乎：论文老是被拒是一种什么体验](https://www.zhihu.com/question/56645254) | 有答主列出投稿链 "pami -> tip -> tmm -> pr -> csvt -> **cviu**"，但**未说明在 CVIU 的拒稿理由** | 低。**不含 CVIU novelty 拒稿信息** |
| [fabiao.com CVIU 拒稿应对](https://www.fabiao.com/sci/10773142/105.html) | 泛泛而谈"拒稿理由包括研究创新性不足"，是**通用模板文**，非 CVIU 实例 | 极低。**不可引用** |

### 4.4 未取到（明确列出，避免误引）

- **未取到**：CVIU 公开的 **reviewer guidelines** 文档（Elsevier 未公开发布 CVIU 专用审稿表；`peer review` 页只说明 single-anonymized + ≥2 reviewers）。
- **未取到**：CVIU 主编关于 **novelty 要求** 的 editorial。检索 `editorial` / `editor-in-chief` / `aims and scope` 未命中任何讨论 novelty 门槛的 CVIU 社论。
- **未取到**：任何**已发表**的"CVIU 因 incremental / no new method 而拒稿"的记录（英文博客、Reddit、小木虫、知乎、CSDN 均无）。
- **未取到**：CVIU 官方 **article types** 列表（是否单列 "Survey" / "Review" / "Evaluation" 栏目）。
- **部分未取到**：CVIU 148 (2016) 1–2 客座 editorial（Farinella G.M.; Kanade T.; Leo M.; Medioni G.G.，DOI [10.1016/j.cviu.2016.05.010](https://doi.org/10.1016/j.cviu.2016.05.010)，pp. 1–2，`[M]` 已核验）的**正文**。搜索索引摘要显示该文写有 *"54 submissions had to be rejected without review because they were considered out of scope"*（[PDF 链接](http://cvrr.ucsd.edu/publications/2016/CVIU_2016_special_issue_part1.pdf)），但**本次直接抓取该 PDF 返回 404**，故该句只能作为**方向性旁证**——说明 CVIU 的 desk-reject 主要理由是 **out of scope**，而非"不够新"——**不可逐字引用**。同期的 CVIU 164 (2017) 1–2 editorial（Girshick R.; Kokkinos I.; Laptev I.; Malik J.，DOI [10.1016/j.cviu.2017.11.006](https://doi.org/10.1016/j.cviu.2017.11.006)）亦为客座编辑部的类似说明，同样未取到正文。

### 4.5 对拒稿风险的综合判断

| 风险 | 可能性 | 依据 | 缓解 |
|---|---|---|---|
| 因"无新方法"被 desk-reject | **低** | §2 有 1998–2026 连续先例；§4.1 Aims & scope；§4.2 "(if any)" | cover letter 首段直接引 2001 专刊 + 2025/2026 三篇 DOI |
| 因"无新 protocol/metric"被 major-revision 要求补 | **中–高** | §3.2：8 篇里 6 篇自带 protocol/metric | 把 494 assertions + one-click script **升格为 "reproducible evaluation protocol"** 写进 contribution list |
| 因"场景数少 / asset 非公开"被质疑泛化性 | **中** | §3.2：先例最多 5 datasets，但都是**公开** benchmark | 强调 400 splits × 9 scenes 的统计功效；4 个 released asset 单独成表；5 个 self-trained 明示为 stress test |
| 因"CVIU 不做 3DGS QA"被判 out of scope | **低–中** | §2.4：d1 是 2026 年 3DGS 评估论文；CVIU 2024–2026 有 8 篇 "Gaussian Splatting" | 在引言里把 3DGS 只作为**被测对象**，主张落在 "certificate validity" 而非 "3DGS 质量" |
| 因 "calibration" 一词被判为相机标定 | **低但真实** | §2.3：CVIU `calibration` 命中 52 篇，多为几何标定 | 标题用 **conformal / coverage / certificate**，不用 calibration |

---

## 5. 把本文映射到先例（cover letter 可直接改写的三句）

| 你的 claim | 最强 CVIU 先例 | 可写的句式 |
|---|---|---|
| certificate 在 pruning / quantisation 后失效（−10.8 ~ −27.7 coverage points），而 appearance edits ≈ 0 | **d1** 10.1016/j.cviu.2025.104575（3DGS 输入变量 → 质量指标的统计研究）；**b6** 10.1016/j.cviu.2007.07.007（指出常用指标的失效模式） | "Following Dalal et al. (CVIU 263, 2026), who quantify how a 3DGS *input* variable affects reconstruction metrics, we quantify how an *edit* to a trained asset affects the validity of a shipped certificate." |
| certificate 不追踪 downstream task utility（4 类任务） | **b5** 10.1006/cviu.2001.0932（edge detector 排名在下游识别任务下重排）；**b4** 10.1006/cviu.2001.0940（2D 比较指标是否预测 3D 解释质量） | "The question of whether a proxy measure tracks downstream utility has a 25-year lineage in CVIU, from Stevens (84(1), 2001) and Shin et al. (84(1), 2001) to Koch et al. (191, 2020)." |
| 测量依赖 GT 预处理约定（up to 2.4×） | **b7** 10.1016/j.cviu.2019.102877（既有 depth 评价只看 global statistics → 结论随 criterion 改变）；**b6** | "As Koch et al. (CVIU 191, 2020) show for depth evaluation, protocol choices can reorder conclusions; we show they can change a certificate's measured validity by up to 2.4×." |
| repair 代价 = interval width +53–122% | **b9** 10.1016/j.cviu.2025.104337（metrics 的 "shortcomings" 与统一 setup）；**e1** 10.1016/j.cviu.2025.104498（unbiased evaluation） | "We report the repair cost explicitly, in the spirit of the 'shortcomings + unified setup' framing of Ismail-Fawaz et al. (CVIU 254, 2025)." |
| 整体定位（measurement，非 method） | **b1** 10.1006/cviu.2001.0948（整期专刊）；**a1** 10.1016/j.cviu.2017.03.007（28 算法评测，27 页） | "CVIU has treated empirical evaluation as first-class research since its 2001 special issue (84(1), pp. 1–199); we submit in that tradition." |

**建议的 contribution list 措辞**（把工程资产升格为研究贡献，这是 §3.2 的核心教训）：

1. **A measurement protocol**, not a method: 400 calibration splits × 9 scenes × 4 edit families × 4 task families.
2. **A quantified failure mode**: −10.8 to −27.7 coverage points under 30% pruning; ≈ 0 under appearance/precision edits.
3. **A decoupling result**: certificate validity does not track downstream task utility across four task families.
4. **A protocol-sensitivity result**: up to 2.4× variation from GT preprocessing convention alone.
5. **A repair cost accounting**: +53–122% interval width.
6. **A reproducible artifact**: one-click script + 494 automated assertions (cf. the unified-codebase contributions of CVIU 261 (2025) 104498 and CVIU 254 (2025) 104337).

---

## 6. 未取到清单（汇总）

| 项 | 状态 |
|---|---|
| CVIU Guide for Authors 后半部分（Writing and formatting 之后）全文 | 未取到（web_fetch 在 "Delayed publication" 处截断）；因此"全文无 novelty 要求"只能弱断言 |
| CVIU 专用 reviewer guidelines 公开文档 | 未取到 |
| CVIU 主编关于 novelty 的 editorial | 未取到 |
| 已发表的"CVIU 因 incremental / 无新方法拒稿"记录 | 未取到（中英文均无） |
| CVIU 官方 article types 列表 | 未取到 |
| CVIU 148 (2016) 1–2 客座 editorial PDF 原文 | 未取到（404）；仅有搜索索引片段 |
| article-number 时代（2019+）论文的正式页数 | 未取到（Crossref 无 page range） |
| Superpixels / Mishkin / 3DGS 等论文的**数据集数量**细节 | 部分未取到（abstract 未给；需读全文） |
| 任何 CVIU evaluation 论文的 **user study** 声明 | 未取到（8 篇摘要均未提及） |
| dedicated point-cloud / mesh / radiance-field **QA benchmark** 的 CVIU 论文 | 未取到（检索无命中） |
| `10.1016/j.cviu.2024.103967` 的 abstract | 未取到（Crossref 无 abstract；S2 429 限流） |

---

## 7. DOI / URL 索引

**Publisher 级（`[P]`）**
- CVIU Guide for Authors：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/publish/guide-for-authors>
- CVIU Vol. 84 Issue 1（2001 专刊）：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/vol/84/issue/1>
- Elsevier Highlights 政策：<https://www.elsevier.com/researcher/author/tools-and-resources/highlights>

**Metadata 级（`[M]`）** — 全部通过 `https://api.crossref.org/works/{DOI}` 与 `https://api.openalex.org/works/https://doi.org/{DOI}` 核验；OpenAlex source id = `S185008460`（4,345 works）

**Forum 级（`[F]`，不可引用）**
- <https://www.minicod.com/journals/computer-vision-and-image-understanding-9cf81d80>
- <https://muchong.com/bbs/journal.php?view=detail&jid=2010>
- <https://www.zhihu.com/question/56645254>
- <https://www.fabiao.com/sci/10773142/105.html>
