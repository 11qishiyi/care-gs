# JVCIR 调研（2026-11-18）：期刊规则 + 2025–2026 近作解剖

> 依据：官方 Guide for Authors / Aims & Scope / Insights（Elsevier），OpenAlex + Crossref 全量检索
> （JVCIR ISSN 1047-3203，2025-01-01 起 530–571 条），以及 7 篇 DOI 的 ScienceDirect 原文页逐篇解剖。
> 目的：给"我们投 JVCIR 会被怎么读"提供可核查事实，而不是印象。
> 配套：`review/JVCIR_GAP_ANALYSIS_2026-11.md`（差距与改造）。

---

## 0 一句话结论

**JVCIR 的 2025–2026 是"低创新门槛 + 高完成度要求"的期刊**：它连"系统级、自己承认只有 modest improvement"
（`105015`）和"明确声明不追求 SOTA"（`104943`）的稿子都收；但它**没有一篇 3DGS 压缩**（title+abstract 检索
`splatting compression` 命中 0），压缩这条线全靠经典 G-PCC/V-PCC 编码工程撑。**这两件事合起来是我们最好的机会**：
把稿子写成"一个被命名的协议/框架 + 完整实验 + 可复现沉积"，而不是"一次测量"。

---

## 1 官方硬规则（会直接决定包装）

| 项 | 事实 | 出处 |
|---|---|---|
| 体裁 | 官方只列 **Regular papers / research reports / short communications**；**无页数/字数上限**；survey 实际会发（Vol.86 标注 "Review article"） | [Guide for Authors](https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/publish/guide-for-authors) |
| 摘要 | **≤250 词**，须独立可读 | 同上 |
| Highlights | **强制**，**3–5 条、每条 ≤85 字符（含空格）**，单独文件、文件名含 "highlights" | 同上 |
| 关键词 | **1–7 个** | 同上 |
| Graphical abstract | **鼓励不强制**；≥1328 px 宽，13 cm 宽可读 | 同上 |
| CRediT | **强制**（14 类角色） | 同上 |
| 利益冲突 | **强制**，用 Elsevier 声明工具生成 `.doc/.docx` 上传 | 同上 |
| 数据可用性 | **Option C 强制**：必须**存入公共仓库并在投稿时给出链接**；不能共享须写明理由。Elsevier 明确把 **software/code/models/algorithms** 算作 research data | [Research data guidelines](https://www.elsevier.com/researcher/author/tools-and-resources/research-data/data-guidelines) |
| 生成式 AI | 若使用，须在参考文献前单列一节声明；AI 不得作作者、不得生成/修改实验图像 | Guide |
| 源文件 | `.tex`（双栏仅 LaTeX）或单栏 Word；**PDF 不算 source file**；官方给 LaTeX 模板（未点名 `elsarticle`，但实际通行） | Guide |
| 参考文献 | 投稿时"不限严格格式"，只要一致；**最终为按引用顺序的方括号数字**、LTWA 缩写 | Guide |
| 图 | 单独文件；照片 **300 dpi**（单栏 ≥1063 px / 整页 ≥2244 px）；线稿 **1000 dpi**；**禁止多面板合成一个文件**（有意对比图除外）；CVD 可辨 | Guide |
| 评审 | **单盲（single anonymized）**，≥2 位审稿人 → **正文保留作者信息，不需要匿名化** | Guide |
| 周期 | 首决中位 **15 天**；审后决定中位 **98 天**；接受到线中位 **215 天**；接受→上线 9 天 | [Insights](https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/about/insights) |
| APC | 混合；OA **USD 2,660**（不含税），订阅路线 **0 费用**（金色 OA 占比仅 6.67%） | [OA options](https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/publish/open-access-options) |
| 当前 special issue | **无 3DGS/压缩/质量相关在征**；唯一在册的 ChinaMM2026 已于 2026-09-30 截止且仅限邀请 | [Special issues](https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/special-issues) |

**Scope 里对我们最值钱的两条原文**（Aims & Scope）：`RGB-D and 3D processing`、**`Visual data reduction and compression`**。
把"3DGS 资产的码率降低 + 保证"写进这两条里，是 scope 上最省力的落点。

**Desk rejection 的证据面**（无官方成文标准，按作者报告分级）：

| 证据 | 读法 |
|---|---|
| 传统 SLAM 稿 **3 天**被拒，建议改投 IF 7 的深度学习刊（LetPub 2026-06-12） | **无学习/表示框架的经典管线会 out-of-scope** |
| "<1 天"、"with editor 3 周未送审直接拒"多例 | 15 天首决中位数 = **大部分稿子死在 triage** |
| EiC 在修回后拒稿，理由 **"innovation points were not enough"**、编辑部"没有精力审这么多"（Peeref） | **"创新点不够"是明示拒因，且可以发生在很晚** |

结论：**首屏（标题+摘要+Fig.1）必须让"新东西是什么"一眼可见**；我们是 DL + 3DGS + 压缩，scope 不构成风险，
"看起来不像方法"才是风险。

---

## 2 2025–2026 近作解剖（33 篇，7 篇逐篇读）

### 2.1 3DGS 这一支：6 篇，全部是"模块增量"

| 论文 | DOI | 做什么 | 规模 | 贡献句式 |
|---|---|---|---|---|
| KF-GS: Kalman filter-guided GS（动态） | `10.1016/j.jvcir.2026.104815` | 卡尔曼滤波融合形变 MLP 观测与局部线性预测（只作用在控制点） | D-NeRF / HyperNeRF / NeRF-DS 三个数据集 | "we introduce … to alleviate …" |
| RDS-GS: 可靠性引导致密化 + 层级语义监督 | `10.1016/j.jvcir.2026.104978` | 观测支撑权重抑制弱观测 + 尺度锚约束新生高斯；粗/中/细语义特征辅助损失 | **Mip-NeRF360 全量 + T&T 2 + DB 2 + OMMO 8** | 同上；53 refs |
| 少样本 3DGS 的深度误差点优化 | `10.1016/j.jvcir.2025.104682` | 单目深度先验 + 深度误差图挑"几何错的"高斯再致密化 | **1 个数据集**（NeRF-LLFF，k=3/4/5） | 唯一基线 DRGS，+0.53 dB / +0.021 SSIM |
| 3DGS 增强 VGGT + 伪 GT | `10.1016/j.jvcir.2026.104943` | 给 VGGT 加 3DGS 头做区域级重建损失；公开数据伪 GT 管线 | DL3DV + Depth Anything V1 | **明确声明"不为 SOTA，只为公平可比"** |
| 手电筒增强的 3DGS 逆渲染 | `10.1016/j.jvcir.2026.104996` | 新输入模态（闪光照片）→ 材质/光照解耦正则 | 4 个物体 + 真实拍摄 | 无 PSNR 表，卖点是"一张闪光图就有效" |
| LiDAR-惯性-视觉大规模 3DGS | `10.1016/j.jvcir.2026.105015` | 系统级：LIW 建图 + 全局配准 + BA + 混合光度/深度损失 | 自建 UAV 平台 | 自认 "systems-level"、"modest improvements"，且承认 LiDAR 初始化单独用会掉 PSNR |

**结构公约数**（7 篇全部命中）：Highlights（4–5 条）→ 摘要（150–220 词）→ 引言末尾**编号贡献列表** →
Related work → Method（**Fig.1 = 管线/框架图**）→ 实验设置（**Datasets / Metrics / Baselines 分小标题**）→
**Limitations and future work** → Conclusion → CRediT → 利益冲突（+ 越来越常见的 GenAI 声明）。
参考文献 **32–60 条**。**无一篇有收敛性/界/证明**，全部数学只是 3DGS 预备公式块。
**运行时间/内存只在"速度本身是卖点"时才报**（`104815` 渲染速度、`104913`/`104610` 编码时间）。

### 2.2 压缩这一支：全是经典点云编码，**没有 3DGS 压缩**

| 论文 | DOI | 做什么 | 数字 |
|---|---|---|---|
| RAHT 改进的 G-PCC 帧间预测 | `10.1016/j.jvcir.2026.104966` | 在 RAHT 系数上做帧间预测 | BD-rate vs G-PCC 锚点 |
| 轻量 MLP 快速 MTT 划分（V-PCC） | `10.1016/j.jvcir.2026.104913` | 四个小网络替代 VVC 穷举 RDO | **−39.7 % 编码时间 @ +0.27 % D1 BD-rate** |
| 纹理感知快速模式决策 + 复杂度分配 | `10.1016/j.jvcir.2025.104610` | CU 提前终止阈值 | **−33.89 / −44.59 % 复杂度 @ +1 / +1.6 % 码率** |
| MJND-CPC：彩色点云多模态 JND | `10.1016/j.jvcir.2026.105027` | 2D+3D 多模态 JND 预测 V-PCC 几何/属性 QP | **QP 误差 7.76、省 89.12 % 码率**（有主观实验、有代码） |
| MDLPCC：错位感知 LiDAR 动态压缩 | `10.1016/j.jvcir.2025.104481` | 全局变换 + 时空混合结构处理错位 | RD 曲线 |

**检索事实**：OpenAlex 对 2025+ 全量做 `title_and_abstract.search`，`splatting` 命中 **6**（全部 ≥2025-10），
**`splatting compression` 命中 0**。→ **3DGS 压缩在 JVCIR 是空位**。
注意风险的另一面：因为空位，审稿人很可能从 `105027` 的 related work 里把 HAC/PCGS/PCCRender 这些
TPAMI/TMM/TVCG 2026 的 3DGS 压缩工作拉来当参照。

### 2.3 非"提模块"的先例：有，但都要带一个**被命名的交付物**

| 类型 | 例子 | 关键形态 |
|---|---|---|
| **综述 + 协议 + 复评**（最像我们要走的路） | `10.1016/j.jvcir.2026.104912` "An information-flow analysis protocol for deep infrared–visible image fusion: Review and module-aware empirical evaluation" | 明写"目标不是定义通用 benchmark，而是让证据条件透明"；PRISMA 式语料流程（2026-03 截止）；定义 **3+6 功能角色**；在固定诊断设置下**重跑模块** |
| 纯比较研究 | `10.1016/j.jvcir.2026.104950` 表征编码器比较 | 不提出生成器，只比较 |
| 数据集 / benchmark | `104513`(ALR-Video)、`104890`(IITMandi_S2F)、`104963`(HDUCap)、`104947`(Lumi-GANomaly) | 数据集与模型并列贡献 |
| 免训练系统 | `10.1016/j.jvcir.2026.104727` eGoRG | 质量/时间权衡研究 |

**判定：JVCIR 收"测量类"，但只收带命名交付物（协议/数据集/评测套件）的形态；没有任何一篇是"我们测了 X 并报告统计"。**
→ 我们已有的 CAV 审计器 + 包络 + 发行配方 + 沉积包，正好可以包成 `104912` 那种"协议 + 角色分类 + 可复现复评"。

---

## 3 这七条事实直接改写我们的投稿策略

1. **scope 用它们的词**：`visual data reduction and compression` + `RGB-D and 3D processing`；标题里保留
   "3D Gaussian Splatting"，摘要第一句给出"新东西是什么"，不要用问句标题。
2. **必须有一个被命名的东西**：命名协议（审计协议）+ 命名算法（分配器）+ 命名容器。三者都已有实体，
   只差命名与算法框。
3. **Fig.1 必须是框架图**，不是结果图；这是 7/7 的公约数。
4. **实验节必须分 Datasets / Metrics / Baselines 三个小标题**，且 **PSNR+SSIM+LPIPS 三件套齐全**
   （我们的 `m5_rd_v2` 已有 8 资产 × 20 变体的三件套，之前只在附录用，属于浪费）。
5. **Limitations 单独成节**（我们已有，但要按"未来工作"口吻重写，不要写成自我否定）。
6. **数据可用性 Option C 是硬门槛**：必须给仓库 DOI，不能写"需要向作者索取"。这是当前投稿包唯一的结构性缺口。
7. **引它们自己的 3DGS 簇**（`104682`/`104815`/`104978`/`104475`/`105015`）：这批稿子互相引用成闭环，
   审稿人大概率来自这个簇；不引等于自断信号。（不是刷引用，是 positioning。）
