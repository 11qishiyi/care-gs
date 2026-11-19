# CVIU 投稿决策调研（Computer Vision and Image Understanding）

- 调研日期：2026-11-12（Asia/Shanghai）
- 目标期刊：Computer Vision and Image Understanding（ISSN 1077-3142 / 1090-235X，Elsevier，Academic Press  imprint）
- 用途：判断一篇「3D Gaussian Splatting / 3D 表示评测」类稿件投 CVIU 的可行性
- 证据分级约定：
  - **【官方】** = sciencedirect.com / elsevier.com / editorialmanager.com / submit.elsevier.com 页面上直接读到的文字
  - **【论文页】** = 该论文在 ScienceDirect 的文章页（摘要 / Highlights / 章节片段），属官方页面，但只是单篇论文的自述
  - **【三方】** = Crossref / OpenAlex / ACM DL / CTAN / 期刊聚合站等第三方来源
  - **未取到** = 官方页面没有该信息，或我无法在不猜测的前提下确认
- 检索手段：web_fetch 直取官方页；OpenAlex API（source S185008460）；Crossref API（journal 1077-3142）；arXiv API；web_search 定位 ScienceDirect 文章页

---

## Task 1 官方要求

### 1.1 Aims & scope（逐字引用）【官方】

来源：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/about/aims-and-scope>（2026-11-12 读取）

> The central focus of this journal is the computer analysis of pictorial information. Computer Vision and Image Understanding publishes papers covering all aspects of image analysis from the low-level, iconic processes of early vision to the high-level, symbolic processes of recognition and interpretation. A wide range of topics in the image understanding area is covered, including papers offering insights that differ from predominant views.
>
> Research Areas Include:
> Theory
> Early vision
> Data structures and representations
> Shape
> Range
> Motion
> Matching and recognition
> Architecture and languages
> Vision systems

对本次投稿的两点直接含义：

1. scope 里没有任何 "3D reconstruction / rendering / radiance field / benchmark" 字样，但 **"Data structures and representations"、"Shape"、"Range"、"Matching and recognition"** 是可以挂靠的四个词。3DGS 的卖点恰好是"表示（representation）"，这是 CVIU scope 里最合法的一条腿。
2. "papers offering insights that differ from predominant views" 是 scope 里唯一的"新颖性"措辞。它偏向"观点/洞察"，而不是"新 SOTA"。这一点和纯 method paper 的写法不同，对评测类稿件反而是利好（见 3.3）。

### 1.2 CVIU 明确接受的文章类型清单

**结论：官方没有公布文章类型清单（未取到）。** 依据：

| 可能的位置 | 是否列 article types | 证据 |
|---|---|---|
| Aims & scope 页 | 否，只列 Research Areas | 【官方】见 1.1 |
| Guide for Authors 全文 | 否。全文检索 "review article / survey / article type / benchmark / software publication" 无任何类型定义段落 | 【官方】<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/publish/guide-for-authors> |
| 期刊首页当期目录 | 只出现 "Research article"（及 "Open access" 标记） | 【官方】<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding> |

逐项判断（"是否列为可投类型"）：

| 类型 | 是否被官方列为 article type | 是否有已发表先例 | 说明 |
|---|---|---|---|
| survey | 未列出 | 有（见下） | 先例：*Indoor Synthetic Data Generation: A Systematic Review*，CVIU Vol 240, 2024, art. 103907，102 篇参考文献【论文页】<https://www.sciencedirect.com/science/article/pii/S1077314223002874> |
| benchmark | 未列出 | 我未检索到 CVIU 的纯 benchmark 论文 | 见 Task 2(b) |
| comparison | 未列出 | 未取到 | — |
| evaluation study | 未列出 | 有 1 篇（GS 相机数量统计研究，见 Task 2） | 这是最关键的先例 |
| empirical study | 未列出 | 上述同一篇可归入此类 | — |
| dataset paper | 未列出 | 有（数据集作为论文主贡献之一，如 HIMoRe、UnrealGaussianStat、ModelNet-O） | 数据集一般与 method/baseline 捆绑，而非独立 dataset paper |
| software publication | 未列出 | 未取到 | CVIU 无 SoftwareX / JOSS 式软件发表通道 |

补充：Special Issue 投稿在系统里要选形如 `VSI: ...` 的 article type（例：`VSI: FM for Pixel-level SU`、`VSI: YCVIU_MF-DISM`），这是**唯一**在官方页面上出现过的"非 Research article"类型名【官方】<https://www.sciencedirect.com/special-issue/105HQ8G6K1Z>。

### 1.3 Guide for Authors 技术规格

来源（两个域名内容一致，均 2026-11-12 读取）：
- <https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/publish/guide-for-authors>
- <https://www.elsevier.com/journals/computer-vision-and-image-understanding/1077-3142/guide-for-authors>

| 项目 | 官方要求 | 证据等级 |
|---|---|---|
| LaTeX 模板 | 原文只有一句："We encourage you use our LaTeX template when preparing a LaTeX submission." **官方页面没有点名 elsarticle，也没有版本号/class option** | 【官方】= 未取到具体模板名 |
| elsarticle 事实（三方补充） | Elsevier 官方模板包 `elsarticle` 当前 revision 289（2026-01-09）；可用 class options：`preprint`、`review`（双倍行距）、`1p/3p/5p`、`twocolumn`、`times`、`authoryear`、`final` | 【三方】<https://tug.ctan.org/macros/latex2e/contrib/elsarticle/elsarticle-template-num.tex> |
| 文件格式 | .doc/.docx 或 .tex；**不接受 PDF 作为源文件**；Word 必须单栏，**双栏只允许 LaTeX** | 【官方】 |
| 页数上限 | **未取到任何 page limit 条款**（Guide for Authors 全文无 "page limit / maximum pages / no longer than"） | 【官方】= 无限制 |
| 字数上限 | **未取到**（同上，全文无 word limit） | 【官方】= 无限制 |
| 摘要 | ≤ 250 words | 【官方】 |
| Highlights | **必须单独文件**，文件名含 "highlights"；**3–5 条 bullet**，**每条 ≤ 85 字符（含空格）** | 【官方】 |
| Graphical Abstract | **"You are encouraged to provide"→ 鼓励、非强制**；≥ 1328 px 宽、长边水平、13 cm 宽下可读；TIFF/EPS/PDF/MS Office | 【官方】 |
| Keywords | **1–7 个**；英文；尽量避免多词关键词 | 【官方】 |
| 盲审 | **single anonymized review（单盲）**；"typically sent to be reviewed by a minimum of two reviewers" | 【官方】 |
| CRediT | 通讯作者**必须**用 CRediT 标注贡献（14 个角色） | 【官方】 |
| Declaration of Competing Interest | **必须**用 Elsevier declarations tool 完成并上传 .doc/.docx | 【官方】 |
| Data availability | 适用 **Research Data Option C**：必须把研究数据存入仓库 + 投稿时给链接；不能共享时必须给理由声明，该声明会随文发表 | 【官方】 |
| Generative AI 声明 | 使用则**必须**声明，置于参考文献之前的独立小节（标题已给定）；仅用于语法/拼写检查可免 | 【官方】 |
| 参考文献风格 | 正文 **author–year**（单作者姓名、双作者两名、≥3 作者 et al. + 年）；文末按字母序（同年 a/b/c）；**投稿时不强制格式**，接收后由期刊套用 | 【官方】 |
| 具体 .bst | **未取到**（官方未点名 `elsarticle-num` / `elsarticle-harv` / `model1-num-names`）。按"author–year + 字母序"的官方描述，**推断**对应 `elsarticle-harv`；`elsarticle-num`（数字制）与指南描述不符 | 【官方】= 未取到；【推断】 |
| 其他硬性项 | 校样 2 天内返回；作者简介 ≤100 words + 证件照；Acknowledgements 必须独立成节置于参考文献前；附录 A/B 编号 Eq.(A.1) | 【官方】 |

**给写作的实操结论**：CVIU 在格式上是"宽进严出"——不限页数、不限字数、投稿不限引用格式。真正卡人的只有：单盲、250 词摘要、3–5 条 85 字符 Highlights、CRediT + COI + Data availability + GenAI 四件套。这意味着**篇幅可以长**：一篇 30 页的评测论文在格式上完全合法。

### 1.4 官方周转数据（Journal Insights）

来源：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/about/insights>（2026-11-12 读取）【官方】

| 指标 | 数值 | 备注 |
|---|---|---|
| Submission to first decision | **7 days** | 这是"送审前/首轮"的编辑决定，含 desk decision |
| Submission to decision after review | **94 days** | 即从投稿到"审稿后决定"约 3.1 个月 |
| Submission to acceptance | **201 days** | 约 6.6 个月 |
| Acceptance to online publication | **7 days** | 接收后一周上线 |
| CiteScore | **7.2** | — |
| Impact Factor | **3.6** | — |
| Acceptance rate | **未取到**（Insights 页未显示） | Elsevier 多数期刊不公开 |
| 收录 | Scopus、SCIE、SJMR、SNIP | 【官方】 |

CRITICAL 解读：**7 天首决定 vs 94 天审稿后决定**这个 13 倍差，说明 CVIU 有非常强的前置筛选（desk rejection 很快）。投稿后一周内没被拒，才进入真正的 3 个月审稿。对一篇"评测类、无新方法"的稿件，第一周就是生死线——编辑要在 7 天内判断"这篇没有新方法的东西值不值得送审"。这是本次决策最大的风险点。

### 1.5 投稿系统与 APC / OA

| 项目 | 事实 | 证据 |
|---|---|---|
| 投稿入口 | **<https://submit.elsevier.com/CVIU>**。页面原文："Use this service to submit to Computer Vision and Image Understanding. This is a new service... After you have submitted... you will manage your submission in Editorial Manager." | 【官方】<https://submit.elsevier.com/CVIU> |
| Editorial Manager 状态 | `editorialmanager.com/cviu` 可访问，标题为 Computer Vision and Image Understanding，但页面顶部红字：**"Important Message: Site under development. Do not use for live manuscript submission."** | 【官方】<https://www.editorialmanager.com/cviu/default.aspx> |
| 结论 | 投稿走 submit.elsevier.com/CVIU（新前端），EM 只用于投稿后的管理。**不要**直接把 EM 当投稿入口用 | 综合上述两条 |
| APC | **USD 2,390**（"All articles"，不含税） | 【官方】<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/publish/open-access-options> |
| 订阅模式 | 无版面费，"No publication fee charged to authors" | 【官方】Insights 页 |
| 许可 | CC BY / CC BY-NC / CC BY-NC-ND 三选一 | 【官方】同上 |
| 自存档 embargo | **24 months** | 【官方】同上 |
| 其他 | 免费 SSRN 预印本张贴；被拒可走 Article Transfer Service；每篇仅一次申诉机会 | 【官方】Guide for Authors |

### 1.6 目前开放的 Special Issues（是否适配 3DGS / 3D 表示评测）

官方全部 collection 列表：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/special-issues>【官方】

| Collection | 编辑 | 官方 "Last update" | 投稿窗口 / 截止 | 是否适配 3DGS 评测 |
|---|---|---|---|---|
| Multimedia Forensics in Practice: Detecting and Interpreting Synthetic Media (MF-DISM) | Micheletto, Gomez-Barrero, Guarnera, Orrù, Ghorbel | 2026-04-27 | 2025-12-01 开放，**2026-03-31 截止**（【三方】聚合站，article type `VSI: YCVIU_MF-DISM`）→ **已过期** | 否（deepfake/取证） |
| Foundational Models for Pixel-level Scene Understanding | Laaksonen, Wenguan Wang, Anwer, Shah, Cucchiara, Cholakkal | 2026-01-29 | 2025-02-10 开放，**2025-05-15 截止**，接收截止 2025-09-15【官方 SI 页】→ **已过期** | 否（2D/3D 分割基础模型，非重建） |
| Computer Vision for Sports and Winter Sports | Giancola, Bisagno, Cioppa, Moeslund, Gade, Dunnhofer | 2025-11-10 | 2025-06-01 开放，**2025-10-15 截止**【官方 SI 页】→ **已过期** | 边缘（若做动态 3DGS + 体育） |
| Recent Advances in Assistive Computer Vision and Robotics | Farinella, Furnari, Leo, Ragusa, Medioni, Trivedi | 2025-05-05 | 未取到 | 否 |
| Best Papers from ICVGIP 2023 | Radhakrishnan, Dhall, Reid, Mitra, Narain | 2024-11-11 | 未取到（邀稿型） | 否 |

**结论：截至 2026-11-12，CVIU 没有任何处于开放期的、与 3DGS / 3D 表示评测相关的 Special Issue。** 唯一沾边的是体育视觉（已截止 2025-10-15）。历史上有过一次高度相关但早已结束的 SI：*Large-Scale 3D Modeling of Urban Indoor or Outdoor Scenes from Images and Range Scans*（eds. Stamos, Pollefeys, Long Quan, Mordohai, Furukawa，最后更新 2017-04）——说明 3D 建模在 CVIU 有 clog 传统，但那是 9 年前。【官方】

---

## Task 2 CVIU 实际发表了什么（3DGS / NeRF / 辐射场 / 3D 重建评测，2023–2026）

### 2.1 检索方法与覆盖度（先交代可信边界）

- OpenAlex：`primary_location.source.id:S185008460`（CVIU），`from_publication_date:2023-01-01`，对 26 组关键词做 `title_and_abstract.search`（gaussian splatting / 3DGS / splatting / gaussian primitive / nerf / neural radiance / radiance field / view synthesis / neural rendering / implicit neural representation / 3D reconstruction / scene reconstruction / surface reconstruction / multi-view stereo / structure from motion / novel view / relighting / text-to-3D / 3D generation / 3D representation / mesh reconstruction / depth completion / point cloud / evaluation benchmark 3D …），去重后 110 条候选。
- Crossref：`journals/1077-3142/works?query.bibliographic=...`，交叉验证 "Gaussian splatting" 命中 6 篇 CVIU 论文（与 OpenAlex 一致）。
- CVIU 该刊 2023-01 起 OpenAlex 总发文量约 4300（全刊历史 4345），命中率符合"3D 重建是小众方向"的预期。
- **覆盖度声明**：我只能保证"标题/摘要命中上述关键词"的论文被覆盖。如果某篇 3DGS 论文摘要没写 "Gaussian Splatting" 字样（例如只写 "splatting"），理论上有漏网可能；但 Crossref 二次交叉未发现额外条目。

### 2.2 已核实的论文表

说明：Year/Vol 用 Crossref/OpenAlex 的 volume + article number；"Type" 是我按摘要/Highlights 判定的；标 **未取到** 的格子表示官方页面（摘要 + 章节片段）没有给该数字，我不猜。

| # | Title | Year / Vol / Art. | Type | 数据集 / 场景数 | 新方法? | 新数据集? | 一句话贡献 | 参考文献数 | DOI |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Gaussian Splatting with NeRF-based color and opacity (VDGS) | 2024 / v251 / 104273 | method | Mip-NeRF360、Tanks&Temples、Deep Blending、Synthetic-NeRF（4 个基准族；逐族场景数未取到） | 是 | 否 | 用 NeRF 式的视角相关颜色/不透明度替代球谐，提升 GS 外观拟合 | 49【三方】 | 10.1016/j.cviu.2024.104273 |
| 2 | NeRFtrinsic Four: An end-to-end trainable NeRF jointly optimizing diverse intrinsic and extrinsic camera parameters | 2024 / v249 / 104206 | method | 未取到 | 是 | 否 | NeRF 与相机内外参端到端联合自标定 | 43【三方】 | 10.1016/j.cviu.2024.104206 |
| 3 | Hexagonal mesh-based neural rendering for real-time rendering and fast reconstruction | 2025 / v255 / 104335 | method | 未取到 | 是 | 否 | 六边形网格 + 可微渲染，只在与射线交点采样，实现实时渲染与快速表面重建 | 92【三方】 | 10.1016/j.cviu.2025.104335 |
| 4 | GASP: Gaussian Splatting for physics-based simulations | 2026 / v265 / 104699 | method | "a diverse range of benchmark datasets designed for 3D object rendering"（数量未取到） | 是 | 否 | flat Gaussians + 黑盒物理引擎，Gaussian grouping 做层次化仿真 | 29【三方】 | 10.1016/j.cviu.2026.104699 |
| 5 | HGAvatar: One-shot high-quality 3D Gaussian head avatar | 2026 / v265 / 104660 | method | 公开数据（Gafni 2021 / Gao 2022 系）；每角色 2,200–2,800 帧训练 + 500 帧测试；512×512、25 FPS | 是 | 否 | one-shot 高斯头部 avatar，DOM 模块优化面部纹理细节 | 53【三方】 | 10.1016/j.cviu.2026.104660 |
| 6 | Evaluating the effect of image quantity on Gaussian Splatting: A statistical perspective | 2026 / v263 / 104575 | **evaluation / empirical（无新方法）** | **3 个 Unreal Engine 合成场景（UnrealGaussianStat）+ mip-NeRF 360 的 7 个真实场景**；相机数 1→100+ | **否** | **是**（UnrealGaussianStat，Data availability: on request） | 相机数量对 GS 指标的统计建模：>100 台后指标饱和，给出非线性回归函数 | 20【三方】 | 10.1016/j.cviu.2025.104575 |
| 7 | FSA-GS: Fine-Structure-Aware Gaussian Splatting for sparse-view novel view synthesis | 2026 / v271 / 104892 | method | **3 个基准**：LLFF（3/6/9 训练视角）、Mip-NeRF360（12/24）、Blender（8）；设置对齐 DropGaussian | 是 | 否 | FSAR/FSAS 结构感知致密化 + GLOD-D dropout，治稀疏视角过拟合 | 41【三方】 | 10.1016/j.cviu.2026.104892 |
| 8 | Efficient semantic segmentation for 3D Gaussian Splatting via confidence-based label assignment | 2026 / v273 / 104943 | method | **ScanNet**（主要）；对比实验含其他数据集（未逐一确认） | 是 | 否 | 用 2D 预测置信度做 2D→3D 标签分配，兼顾精度与运行时 | 53【三方】 | 10.1016/j.cviu.2026.104943 |
| 9 | WinGS: Windowed Gaussian Splatting for long-sequence multi-view hand interaction reconstruction | 2026 / v273 / 104968 | **method + dataset** | **HIMoRe：6 个手部交互场景，24 台同步相机，1080p/60 FPS，每段 5–12 min** | 是（baseline） | **是（HIMoRe）** | 滑窗分段训练 4DGS 并做光度一致性混合，替代单体全局 4D 模型 | 67【三方】 | 10.1016/j.cviu.2026.104968 |
| 10 | HL-SLAM: Hybrid optimization and loop scene correction for NeRF-SLAM | 2026 / v269 / 104808 | method | 未取到（参考文献含 ScanNet） | 是 | 否 | NeRF-SLAM 的混合优化 + 回环场景校正 | 46【三方】 | 10.1016/j.cviu.2026.104808 |
| 11 | IWC-DiF: Learning a generalizable NeRF by incremental weight consolidation of dictionary fields | 2026 / v270 / 104855 | method | 未取到 | 是 | 否 | 不确定性引导的增量权重整合，缓解 generalizable NeRF 灾难性遗忘 | 47【三方】 | 10.1016/j.cviu.2026.104855 |
| 12 | LiveNeRF: Efficient face replacement through Neural Radiance Fields integration | 2026 / v270 / 104856 | method | 未取到 | 是 | 否 | NeRF 融合做高效人脸替换 | 51【三方】 | 10.1016/j.cviu.2026.104856 |
| 13 | SAFIR: Spatially-aware Activation Function for Implicit Neural Representations | 2026 / v268 / 104754 | method（INR 组件） | 未取到 | 是 | 否 | 为隐式神经表示设计空间感知激活函数 | 未取到 | 10.1016/j.cviu.2026.104754 |
| 14 | Time-archival camera virtualization for sports and visual performances | 2026 / v267 / 104714 | method / system | 体育多视角同步相机阵列（数量未取到） | 是 | 否 | 逐帧独立优化的动态辐射场，为体育转播生成虚拟相机 | 110【三方】 | 10.1016/j.cviu.2026.104714 |
| 15 | 3D scene reconstruction from a limited number of viewpoints | 2026 / v268 / 104775 | 未取到（标题指向少视角重建，method 或 evaluation） | 未取到 | 未取到 | 未取到 | 少视角 3D 场景重建 | 54【三方】 | 10.1016/j.cviu.2026.104775 |
| 16 | Indoor Synthetic Data Generation: A Systematic Review | 2024 / v240 / 103907 | **survey（系统综述）** | N/A（综述） | 否 | 否 | 室内合成数据生成 + 域随机化的系统文献综述（检测/6D 位姿/语义） | 102【三方】 | 10.1016/j.cviu.2023.103907 |

边界样本（标题命中关键词、但不属于"辐射场重建"主线，不计入上表）：*eMotion-GAN*（v262, 104555，2D GAN 正面化）、*Towards 4D human video stylization*（v262, 104532）、*Continuous conditional video synthesis by neural processes*（v259, 104387）、*S2DNet*（v259, 104444，去雨）、*Improving the planarity and sharpness of monocularly estimated depth images using the Phong reflection model*（v233, 103726，深度图后处理）。

### 2.3 回答三个问题

**(a) CVIU 的 3DGS 论文通常评测多少场景？**

分层看：

| 论文类型 | 数据集族数 | 场景数量级 | 实例 |
|---|---|---|---|
| 纯 method（3DGS/NVS） | **3 个基准族**是事实标准 | 若按标准协议展开 ≈ 8（LLFF）+ 9（Mip-NeRF360）+ 8（Blender）≈ **25 个场景**（协议场景数为领域常识，未逐篇核对论文表格） | FSA-GS（#7）明确写 LLFF / Mip-NeRF360 / Blender |
| 面向下游任务（分割/SLAM/头像） | 1–2 个 | 1 个主数据集 + 若干辅助 | #8 只用 ScanNet 为主；#5 用 2 组公开人脸视频 |
| 纯评测 | 1 个自建 + 1 个公共 | **3 + 7 = 10 个场景** | #6（UnrealGaussianStat 3 场景 + mip-NeRF 360 7 场景） |

一句话：**CVIU 的 3DGS method 论文以"3 个标准基准"为门槛，不要求大规模场景扫描；纯评测论文的先例只有 10 个场景（其中 7 个是公共基准）。** 这比 TPAMI/IJCV 的期望低，也比 3DV/CVPR 的 benchmark track 低。

**(b) CVIU 是否发过"既无新方法、又无新数据集"的论文？**

- **在 3DGS/辐射场这条线上：未发现（= 没有先例）。**
- 最接近的先例是 #6（Evaluating the effect of image quantity on Gaussian Splatting, v263, 104575）：**无新方法**（直接调 3DGS 原版 + R 语言 nls 回归）、**但建了新数据集 UnrealGaussianStat**（3 个 UE 场景 + 半球均匀/随机采样相机布局生成器），并且把 Data availability 写成 "Data will be made available on request"。
- 它的对照价值极高：**全文只有 20 篇参考文献**，没有 SOTA 对比表，没有新模块，靠"统计回归 + 一条可操作结论（>100 台相机后指标饱和）"过审。
- 另一类先例是 #16（系统综述，102 refs，无方法无数据集）——但综述是"文献级"贡献，不是"实验级"评测。

**结论**：想在 CVIU 发"纯评测"，**必须至少交付一个可复用的数据集（哪怕是合成的）**；否则这条线上没有先例可援引。这直接决定投稿策略：把 UnrealGaussianStat 那篇论文当模板抄结构，而不是把一篇"我们跑了 12 个场景的对比实验"投过去。

**(c) 它们通常多少页？**

- **未取到**：CVIU 在 **2019 年内**由"页码区间"切换为 **6 位 article number**（2019 年两种格式并存：v184 仍是 `31-44`，v188 已是 `102799`；**2020 年起全部为 article number**，如 `102920`、`103062`），此后官方**不再公布页码范围**。这一条我用 Crossref 逐年抽样核实过（2019/2020/2021 各 5 条）。Crossref 的 `page` 字段与 article number 完全相同（例：104575 的 page = "104575"），OpenAlex 的 `biblio.first_page` 同样如此。
- 可验证的替代量（全部为 Crossref 一手数据）：

| 论文 | 参考文献数 | 备注 |
|---|---|---|
| #6 纯评测 | **20** | 最短 |
| #4 GASP | 29 | — |
| #7 FSA-GS | 41 | — |
| #2 NeRFtrinsic Four | 43 | — |
| #10 HL-SLAM | 46 | — |
| #11 IWC-DiF | 47 | — |
| #1 VDGS | 49 | — |
| #12 LiveNeRF | 51 | — |
| #5 HGAvatar / #8 语义分割 | 53 / 53 | — |
| #15 少视角重建 | 54 | — |
| #9 WinGS | 67 | — |
| #3 六边形网格 | 92 | — |
| #14 体育相机虚拟化 | 110 | — |
| #16 综述 | 102 | — |

- 侧面证据（第三方，仅作量级参考）：ACM DL 对 CVIU 整期的著录显示单期约 **407–445 页**（如 Vol 265 "445 pages"、Vol 268 "407 pages"、Vol 269 "422 pages"）。这是**整期**页数，不是单篇。【三方】<https://dl.acm.org/doi/10.1016/j.cviu.2026.104660>
- 结合 1.3（官方无页数上限）+ 参考文献分布：CVIU 的 3DGS 论文实际是"**20–110 篇参考文献、单篇 15–30 页当量**"的量级，**没有硬页数约束**。写 25–30 页不会被格式拦下。

---

## Task 3 审稿人 / 编辑预期画像

### 3.1 编辑团队（官方 editorial board 页，2026-11-12）

来源：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/about/editorial-board>【官方】

| 角色 | 姓名 | 机构 | 标注领域 |
|---|---|---|---|
| Co-Editor-in-Chief | **Hedvig Kjellström** | KTH Royal Institute of Technology, Stockholm | 未标注（页面只有机构） |
| Co-Editor-in-Chief | **Niculae Sebe, PhD** | University of Trento, DISI, Italy | 未标注 |
| Associate EiC | **Juergen Gall** | University of Bonn | 未标注 |
| Associate EiC | **Yingli Tian** | The City College of New York | 未标注 |
| Associate EiC | **Guoying Zhao** | University of Oulu | 未标注 |

规模：**71 名编辑/编委，17 个国家/地区**；美国 27、中国 7、意大利 7、德国 6、法国 5、荷兰 3、芬兰 2、日本 2、韩国 2、瑞典 2、英国 2，其余 1 人国家若干。性别自报：男 68%、女 28%、不愿披露 5%（仅 56.3% 的人作答）。【官方】

### 3.2 与 3D / 渲染 / 不确定性相关的编委（这是审稿人池）

从官方 board 页的"自报关键词"里筛出的相关者：

| 姓名 | 机构 | 官方自报关键词 | 与本次投稿的相关度 |
|---|---|---|---|
| **Jingyi Yu** | University of Delaware | "Sensors and Early Vision, Computational Photography, **Image-based Modeling and Rendering**" | **最高**。image-based rendering 正是 3DGS 的祖谱 |
| **Federica Arrigoni** | Politecnico di Milano | Computer Vision, **Multiple View Geometry** | 高（相机位姿/几何一致性） |
| **Mohamed Daoudi** | IMT Nord Europe | Shape analysis, **3D face modeling**, 3D human body shape | 高（3D 形状评测） |
| **Gyeongsik Moon** | DGIST | **3d hands and body**, computer vision | 高（若做手/人体 4D） |
| **Dan Xu** | HKUST | 未标注 | 中高（3D 重建/生成方向活跃） |
| **Jianwen Xie** | Akool AI Research Lab | Generative Model, **3D Point Cloud**, Point Cloud Generation, Texture Synthesis | 中（点云/生成式表示） |
| **Arjan Kuijper** | Fraunhofer IGD | Visual Computing, Pattern Recognition, **Computer Graphics** | 中（图形学视角） |
| **Ioannis Stamos** | CUNY | 未标注；但他是 2017 年 CVIU "Large-Scale 3D Modeling of Urban Indoor or Outdoor Scenes" SI 的主编 | 中高（3D 建模传统） |
| **Umar Iqbal** | NVIDIA | **Avatars**, Pose estimation | 中（若做 avatar） |
| **Radu Timofte** | University of Würzburg | Learned compression, Computational photography, Super-Resolution | 中（benchmark/challenge 文化出身） |
| **Ribana Roscher** | University of Bonn | **explainable ML, data-centric machine learning** | 中（"data-centric" 是评测类稿件最友好的标签） |

**关于 "uncertainty" 专家**：官方 board 页**没有任何一位**把 uncertainty / probabilistic / Bayesian 写进自报关键词 → **未取到** CVIU 编委层面的不确定性方向负责人。若稿件主打"不确定性建模"，在 CVIU 找不到对口编辑的概率偏高（这会影响送审人选，进而影响评审口味）。

**结构性观察**：CVIU 编委里 3D/渲染方向的人不少，但**没有一位的自报关键词包含 Gaussian Splatting / radiance field / novel view synthesis**。也就是说，3DGS 稿件几乎必然落在"Multiple View Geometry / image-based rendering / 3D shape"这几位手里，或者被分给非 3D 的 AE。这与"3DGS 是 CVIU 的边缘新兴方向"的判断一致。

### 3.3 有没有"如何在本刊发表 / 为什么被拒"的编辑部署文？

- **未取到。** 我用 Crossref 对 CVIU（ISSN 1077-3142）2015-01-01 起的所有条目做 `query.title=editorial`，命中只有：
  - *Editorial*，Vol 141（2015），DOI 10.1016/j.cviu.2015.10.011
  - *Editorial*，Vol 145（2016），DOI 10.1016/j.cviu.2016.02.010
  - *GUEST EDITORIAL*，Vol 173（2018），DOI 10.1016/j.cviu.2018.11.006
  - 以及每卷重复出现的 *Editorial Board* 条目（2015–2026 共 15+ 条）
  - **没有任何 "state of the journal"、"how to get published in CVIU"、"why papers get rejected" 类文章。** 我未逐篇打开那 3 篇 Editorial 正文（可能是 SI 序言），其内容：**未取到**。
- 官方唯一成文的评审流程描述在 Guide for Authors 的 Peer review 小节："initially assessed by our editors. If your submission is deemed suitable, it will typically be sent to be reviewed by a minimum of two reviewers... **Our editors decide** whether to accept or reject your article."【官方】
- 拒稿相关的可操作信息只有两条官方文本：
  1. Aims & scope："papers offering insights that differ from predominant views"——反过来读，**"与主流视角无差异"是 scope 层面的拒稿理由**。
  2. 7 天首决定（1.4）——**desk rejection 是主要淘汰机制**。

### 3.4 CVIU 有没有 Software / Reproducibility / Benchmark track？

**没有。** 三条独立证据：

1. 官方 Special Issues / Article Collections 全量列表（1.6）里，**没有任何** benchmark、reproducibility、software、dataset track 或 collection。【官方】
2. Guide for Authors 全文没有 "benchmark track"、"software paper"、"reproducibility track" 之类通道；唯一与可复现相关的是 **Research Data Option C**（数据必须 deposit）和"鼓励引用 software/dataset 并给出 `[software]` / `[dataset]` 参考文献格式"。【官方】
3. 期刊首页当期目录的所有条目都只标 "Research article"。【官方】

替代路径：CVIU 的 benchmark 类工作只能以 **regular Research article** 或 **VSI（special issue）article type** 投递。若稿件核心是"评测协议 + 数据集"，形式上必须包装成 research article（有 contribution list、有 method 章节名），不能指望有专门的 benchmark 通道。

---

## 4 对本次投稿的直接判断（把上面的证据压成结论）

1. **格式上零障碍**：无页数/字数上限、投稿不限引用格式、单盲（不用匿名化）、Graphical Abstract 非必需。真正的硬约束只有 250 词摘要、3–5×85 字符 Highlights、CRediT+COI+Data availability+GenAI 四件套。
2. **时间成本可预测**：7 天首决定 → 94 天审稿后决定 → 201 天接收 → 7 天上线。也就是说，**最坏情况约 6.6 个月**。如果一周内没被 desk reject，就进入约 3 个月的等待期。
3. **最大风险是"7 天 desk rejection"**：CVIU 没有 benchmark/software 通道，编辑在 7 天内要判断一篇无新方法的稿件是否符合 "insights that differ from predominant views"。**摘要和 Highlights 必须在前 85 个字符里就把"非主流洞察"说出来**，否则熬不过第一周。
4. **有先例，但先例带了数据集**：唯一的纯评测先例（v263, 104575）无新方法、20 篇参考文献，但交付了 UnrealGaussianStat 数据集，且结论可操作（>100 相机后饱和）。**"无新方法 + 无新数据集"在 CVIU 这条线上没有先例。**
5. **场景规模门槛不高**：3DGS method 论文的事实标准是 3 个基准族（LLFF/Mip-NeRF360/Blender），下游任务论文常只用 1 个主数据集；纯评测先例只有 3+7=10 个场景。
6. **找不到"不确定性"对口编辑**：71 名编委中无人自报 uncertainty 关键词。若稿件主打不确定性，送审匹配度是真实风险。
7. **Special Issue 没有快车道**：截至 2026-11-12 无开放的 3DGS/3D 评测 SI，只能走 regular submission。

---

## 5 证据 URL 清单

官方（sciencedirect.com / elsevier.com / elsevier 投稿域）：

- Aims & scope：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/about/aims-and-scope>
- Guide for Authors：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/publish/guide-for-authors>
- Guide for Authors（elsevier.com 镜像）：<https://www.elsevier.com/journals/computer-vision-and-image-understanding/1077-3142/guide-for-authors>
- Journal Insights（周转/指标）：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/about/insights>
- Open access / APC：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/publish/open-access-options>
- Editorial board：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/about/editorial-board>
- Special issues 全量列表：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/special-issues>
- SI 示例（含 Timeline 字段）：<https://www.sciencedirect.com/special-issue/105HQ8G6K1Z>
- 投稿入口：<https://submit.elsevier.com/CVIU>
- Editorial Manager（"Site under development"）：<https://www.editorialmanager.com/cviu/default.aspx>
- 期刊首页（"Research article" 标签 + 周转数字）：<https://www.sciencedirect.com/journal/computer-vision-and-image-understanding>

论文页（ScienceDirect，摘要/Highlights/章节片段）：

- 104575 纯评测：<https://www.sciencedirect.com/science/article/abs/pii/S107731422500298X>
- 104892 FSA-GS：<https://www.sciencedirect.com/science/article/abs/pii/S1077314226002596>
- 104968 WinGS（HIMoRe）：<https://www.sciencedirect.com/science/article/abs/pii/S1077314226003358>
- 104660 HGAvatar：<https://www.sciencedirect.com/science/article/abs/pii/S1077314226000275>
- 104943 3DGS 语义分割：<https://www.sciencedirect.com/science/article/pii/S1077314226003103>
- 104699 GASP：<https://www.sciencedirect.com/science/article/abs/pii/S1077314226000664>
- 104714 体育相机虚拟化：<https://www.sciencedirect.com/science/article/abs/pii/S1077314226000810>
- 103907 系统综述：<https://www.sciencedirect.com/science/article/pii/S1077314223002874>
- 104855 IWC-DiF：<https://www.sciencedirect.com/science/article/abs/pii/S1077314226002225>
- 104335 六边形网格神经渲染：<https://www.sciencedirect.com/science/article/abs/pii/S107731422500058X>

第三方：

- OpenAlex source S185008460：<https://api.openalex.org/sources?filter=issn:1077-3142>
- Crossref journal 1077-3142：<https://api.crossref.org/journals/1077-3142/works>
- elsarticle 模板（rev 289, 2026-01-09，class options）：<https://tug.ctan.org/macros/latex2e/contrib/elsarticle/elsarticle-template-num.tex>
- elsarticle harv 模板：<http://mirrors.mit.edu/CTAN/macros/latex/contrib/elsarticle/elsarticle-template-harv.tex>
- MF-DISM 投稿窗口（聚合站）：<https://ftp.neuhaus.cn/journal/178?lang=es>
- ACM DL 整期页数：<https://dl.acm.org/doi/10.1016/j.cviu.2026.104660>

---

## 6 "未取到"清单（明确不猜的项）

| 项 | 状态 | 原因 |
|---|---|---|
| CVIU 官方 article type 清单 | 未取到 | Guide for Authors / scope 页 / 目录均未列；只有 `VSI: ...` 出现在 SI 页 |
| CVIU 官方指定的 .bst 文件名 | 未取到 | 指南只描述 author–year 风格，未点名 `elsarticle-num/harv/model1-num-names` |
| CVIU 官方 LaTeX 模板名与版本 | 未取到 | 指南只写 "our LaTeX template"，无链接文字、无版本号 |
| 页数 / 字数上限 | 未取到（= 不存在限制） | 全文检索无相关条款 |
| Acceptance rate | 未取到 | Insights 页未显示 |
| 单篇论文页码 | 未取到 | 2021 起改用 article number，官方不公布页码范围 |
| 3 篇 Editorial（2015/2016/2018）正文 | 未取到 | 未打开正文，无法确认是否为"办刊方针"类文章 |
| 编委中的 uncertainty 专家 | 未取到 | 71 人自报关键词无 uncertainty/probabilistic/Bayesian |
| 104206 / 104335 / 104754 / 104808 / 104855 / 104856 / 104714 / 104775 的具体数据集与场景数 | 未取到 | 这些篇的摘要未提数据集，章节片段未覆盖实验节 |
| 104775 "3D scene reconstruction from a limited number of viewpoints" 的类型判定 | 未取到 | 仅凭标题无法区分 method / evaluation |
