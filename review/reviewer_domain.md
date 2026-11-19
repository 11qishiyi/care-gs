# 审稿意见（domain reviewer：3D reconstruction / neural rendering / trustworthy ML）

**审稿对象**：`submission/main.tex`（8 页 TMLR 投稿版，`main.pdf` 8 页，`main.log` 佐证）
**时间**：2026-11-09｜只审阅，不修改论文与代码
**核对原则**：所有对 AURA 及其它文献的断言均指到原文行号；不能核实的写"未核实"。

## 0. 一句话判定

**Reject（当前版本），但可重投且值得重投。** 方法学（400 次划分 + 配对区间）是这篇稿子最硬的部分，但
**主卖点的数字用错了分母**（B1），而且主线选在了对 conformal 读者近乎同义反复的方向上（B2）。
这两件事都可以在不重跑主实验的前提下修掉；修掉之后这是一篇 TMLR 该收的 measurement study。

---

## 1. TMLR 第二条标准（audience interest + clarity）下的判定

TMLR 只有两条标准（[acceptance-criteria](https://jmlr.org/tmlr/acceptance-criteria.html)）：
criterion 1 = 主张是否被准确且令人信服的证据支持；criterion 2 = TMLR 读者里是否有人会对这些发现感兴趣、
以及论文是否把它讲清楚了。**明确写了不以"新方法/新 SOTA/novelty"为拒稿理由**，这一点对本文有利——
本文本来就不是方法论文。所以本文的死活不取决于"新颖性"，取决于**读起来有没有意思**（criterion 2）
和**数字站不站得住**（criterion 1）。

**结论：criterion 2 目前是 borderline fail（不是因 clarity，而是因 interest）；criterion 1 目前是 fail（见 B1）。**

**值不值得读**：值得。**值得读的是这一句**（目前它在 §3.4 里，藏在第三个卖点后面）：

> 一个覆盖率只掉 4.6 个百分点的资产，重定位命中率掉了 16.8 个百分点。

**但这一句现在不能原样读**，因为 4.6 是体素粒度、16.8 是图像块粒度（B1），同粒度下是 10.9 对 16.8。
真正的、可以挺着胸说出来的那一句应该是：

> 修复一份证书，数据上几乎免费（2 个留出视角），信息上极其昂贵（阈值放宽 26–71%，且永久不回收）。

这句话（i）不是同义反复，（ii）不需要 12.1× 那个脆弱的倍数，（iii）现在的 Table `tab:rules` 已经
把它测出来了，只是作者把它当成"规则 (a) 的代价"而不是"本文的发现"。

**Clarity 上的具体扣分**（都会在第一轮被点名，且都是 10 分钟能改的）：

| 问题 | 位置 | 说明 |
|---|---|---|
| 贯穿全文没有一处写明工作分辨率 | §2 全节 | 渲染在 `factor=4`（1/4 分辨率，见 `many_splits.py:52`），但正文从未说。于是"+24 px 搜索窗""tolerance 2 px""32×32 patch"全部不可解释 |
| 符号约定自相矛盾 | Table `tab:main` 用 `−10.9`，Table `tab:rules`b 用 `+10.9` | 同一物理量（不透明度剪 30% 的覆盖率降幅）在两张表里符号相反 |
| 表/图混用"降幅"与"覆盖率" | `fig1` y 轴写 `coverage change (pp)`，`fig9` y 轴写 `drop after pruning 30% (pp)`（正值） | 与正文的负号不一致 |
| 孤立的星号 | `main.tex:201` `$-2.0^{\ast}$` | 全文没有任何表注解释这个 `*`（markdown 版有"显存溢出"的脚注，tex 版丢了） |
| Table `tab:rules` 的 caption 引用了不存在的列 | `main.tex:279` "at $n=$ all" | 表里没有 `n=all` 列（markdown 版有，tex 版删了但 caption 没改） |
| matplotlib 默认风格 + 图内标题重复 caption | `fig1_edit_families.png`、`fig9_task_vs_cert.png` | 两图都在图内自带标题（"Geometry edits hurt 10-19 pp…"、"The certificate understates the damage"），与 caption 冗余；`fig1` 后半段（SH 8-bit = 0）在视觉上是一片空白 |

---

## 2. 新颖性 / 定位的致命问题

### B1 [BLOCKER] 主卖点的分子与分母用了**不同的统计粒度**：1.9–12.1× 是粒度产物

这是我在全文找到的唯一一个**可以被审稿人在 10 分钟内独立复算出来的、指向数字本身的**问题，
而且它落在摘要第二句和贡献列表第 2 条上。它的严重度高于所有"新颖性"问题。

**证据链（全部可复算，无需 GPU）**：

1. 主表 Table `tab:main` 的覆盖率降幅（剪到 30%）= −10.9 / −18.6 / −12.8 / −11.7 pp。
   其计量单位是**逐像素**残差：`many_splits.py:88` `q = cq(r_clean[Ci].reshape(-1), α)`，
   `:89` 覆盖率 = `(r_clean[Vi].reshape(-1) <= q).mean()`。→ 分母是 pixel-level coverage。
2. Table `tab:downstream` 的 "Certificate drop" 列 = −4.6 / −6.1 / −2.6 / −6.1 pp。
   逐位对应 `research/results_v60/vt_flowers.json` 的 `voxel_prune30_drop_mean`
   = 0.046061 / 0.061447 / 0.026075 / 0.061433，字段名就叫 **voxel**。→ 分母是 voxel-level coverage。
   生成脚本 `voxel_and_task.py:5-7` 的 docstring 自己写着"per-voxel max-residual tables"。
3. 论文自己的附录 C.3（`main.tex:466-470`）明说：把区域从 64×64 图像块换成体素，"reduces its magnitude 3–4×
   （−2.6 to −6.1 points）"——**附录里这两个数与 Table 3 的 "Certificate drop" 是同一批数。**
   也就是说，论文自己记录了"换一种区域定义，灵敏度摆动 3–4 倍"，而 Table 3 恰好选了**最不敏感**的那一种当分母。
   主表的计量单位是逐像素（`many_splits.py:88-89`），与体素定义下的降幅同样差 2.4–4.2 倍。
4. 图 `fig9_task_vs_cert.png` 的图例是诚实的：`certificate coverage (3D voxel)`。
   **但 tex 正文、Table 3 列头、摘要全部丢掉了 "voxel" 这个限定词。**

**后果（复算）**：

| 场景 | 任务降幅 | 证书降幅（Table 3，体素） | 论文报的倍数 | 证书降幅（Table 2，像素） | **同粒度倍数** |
|---|---:|---:|---:|---:|---:|
| flowers  | 16.8 | 4.6 | 3.7× | 10.9 | **1.54×** |
| bicycle  | 21.6 | 6.1 | 3.5× | 18.6 | **1.16×** |
| treehill | 31.7 | 2.6 | **12.1×** | 12.8 | **2.47×** |
| stump    | 11.9 | 6.1 | 1.9× | 11.7 | **1.02×** |

也就是说：**用论文自己的主指标算，倍数从 1.9–12.1× 塌到 1.02–2.47×，而且 stump 上是 1.02×
——证书降幅与任务降幅几乎相等，"低估"在那一格不存在。**

**为什么这是 criterion 1 的失败，而不是一个措辞问题**：
摘要原文是 "an asset whose coverage drops by 4.6 points loses 16.8 points of patch re-localisation accuracy"，
而同一个资产（flowers，剪 30%）在同一篇论文的 Table 2 里 coverage 掉的是 **10.9**。
读者无法同时相信这两个 4.6 和 10.9 是"the coverage drop"。
更糟的是：Table 1（claims 表）把 "the gap disappears once the task threshold is varied" 写成自己的反驳条件
——审稿人只要问一句"那换个粒度呢"，反驳条件就命中了，而这个实验的数字**作者手上已经全部有了**。

**修法（不改任何测量，2 小时）**：
1. Table 3 的列头改为 `Certificate drop (voxel)`，并在 caption 里一句话交代粒度；
2. 加一列 `Certificate drop (pixel)`，把上表右列填进去；
3. 摘要改为**给区间而不是给上界**：`1.0×–12.1× depending on the region granularity`，
   并把"方向一致、幅度依赖粒度"作为**正面主张**说出来（这恰恰是本文最可信的部分：
   它证明了"覆盖率不是可用性的充分统计量"这件事是稳健的，而"倍数是多少"不是）。
4. **同时补上任务侧的不确定性**（现在完全没有）：`vt_*.json` 里体素降幅的 95% 区间是
   flowers [1.8,10.4] / bicycle [1.9,11.7] / treehill [1.7,4.1] / stump [3.3,10.0]，
   而任务降幅是单点估计（10 patch/视角，无区间）。分母区间跨 2–5 倍，所以"12.1×"的可信区间大约是
   [7.7,19.2]，"1.9×"的可信区间大约是 [1.2,3.6]。**报单点倍数而不报区间，在 TMLR 的 criterion 1 下不可辩护。**

**附加发现（同一节的方法学问题）**：任务侧**不是配对设计**。`voxel_and_task.py:145-154` 里
`rng` 在 `clean → prune50 → prune30` 三个变体间连续消耗，所以三个变体用的是**不同的 patch 集合**；
而证书侧是 400 次配对划分。这解释了为什么任务侧只有点估计，也是修起来最便宜的一条（固定 patch 集重跑，约 10 分钟 GPU）。

### B2 [BLOCKER] 以"失效"为主线，会让懂 conformal 的审稿人 30 秒内写下 "unsurprising"

**判断：会，而且是大概率。** 理由不是"别人做过"，而是**逻辑结构**：

- split-conformal 的 coverage 保证以 exchangeability 为前提（本文自己在 `main.tex:129` 引 `vovk2005,lei2018` 时写了 "under exchangeability"）。
- 剪枝改变了模型的残差分布 ⇒ calibration 与 deployment 不再 exchangeable ⇒ 保证失效。
- 所以"几何编辑使保形证书失效"是**前提的直接推论**，不是发现。审稿人的内心独白会是：
  "你们把一个 assumption 拿掉，然后报告 assumption 不成立了。这在 conformal 里叫 caveat，不叫 result。"

更麻烦的是，这个 caveat 已经有**定量的理论**：Barber, Candès, Ramdas & Tibshirani,
*Conformal prediction beyond exchangeability*, **Annals of Statistics 51(2):816–845, 2023**
（[arXiv:2202.13415](https://arxiv.org/abs/2202.13415)）给出了 coverage gap 以 calibration/test 分布间
差异度量为上界的结论；Tibshirani et al. 2019（**已经在 bib 里**，`main.tex:414`，但正文从未引用）给出
covariate shift 下的加权保形方案。一个 conformal 审稿人会立刻问三连：
**"你们算过那个 bound 吗？试过 weighted CP 吗？试过 ACI（Gibbs & Candès 2021）吗？"**
本文三个都没做，而且连这三条线都没引。

而且——**AURA 自己已经写过了**（见 M1）：`aura.txt:1275-1280` 明确说证书"assumes the calibration and
streamed carriers are exchangeable … and a distribution shift can violate it — cross-scene deployment
therefore needs a small local conformal set per scene"，并说测试集里有一个"the bound honestly fails"的例子；
`:1327-1336` 给出"keep a small per-scene conformal set to restore the distribution-free certificate"的
"honest deployment recipe"。**这几乎就是本文的规则 (a)。** 所以"失效"这条线既在同义反复上站不住，
在优先权上也不干净。

#### 替代主线（3 条，按我推荐的顺序）

**主线 A（推荐）：valid ≠ useful —— 修复一份证书，数据上免费，信息上昂贵。**

- 立论：证书失效不值得写；**恢复有效性的代价结构**值得写。2 个留出视角就能把 coverage 拉回名义值，
  但 q 永久变宽 26–71%，且这个损失不能靠多加视角换回来（Table `tab:rules`a 里 n=2→n=8，coverage 在 0.88–0.97
  之间震荡，q 的增长不回收）。于是"coverage = 1−α"根本不是一个可用的验收标准：
  **两份都满足名义覆盖率的证书，信息量可以差 71%。**
- 已有数字就够：Table 2（降幅）、Table 5a（n=2/4/6/8 的修复曲线 + q growth 26/43/54/71%）、Table 3（三级梯度）。
- 需要补什么：（i）**绝对 q 值**（现在全文只报相对增长，读者无法判断 26–71% 是 0.09→0.14 还是 0.9→1.4）——
  数据已存，只需打印；（ii）把"修复曲线"从一条规则升级成一张 **Pareto 图**（横轴 calibration views，
  纵轴 q/q_fresh，每条线一个场景）——这是本文唯一一张能一眼看懂"权衡"的图，现在没有；
  （iii）一句话的理论锚点：用 Barber 2023 的 bound 说明"有效但更宽"是**结构性**的，不是实现缺陷。
- 风险：审稿人可能说"标定数据越多区间越窄，这不是常识吗"。**必须靠不对称性顶回去**：
  常识是"多数据→更窄"，本文的是"**极少数据→恢复有效性，但再多的数据也不恢复精度**"，
  而且这个不对称在 4 个场景上一致。这段话要写在摘要第一句里，否则这条线也会被读成常识。

**主线 B：coverage 不是资产可用性的充分统计量。**

- 立论：一份**仍然有效**的证书可以已经没用了。最锋利的证据不是 12.1×，而是 §3.2 的三级梯度：
  SH 8-bit 量化下 coverage 变化**精确为 0.00**（4 场景、400 次划分），而剪枝下掉 10.9–18.6——
  同一个"覆盖率"指标，对一类编辑完全不敏感、对另一类高度敏感，因此它不能作为资产的验收统计量。
- 已有数字：Table 2、Table 3、附录 C.3（粒度敏感性）、下游任务（作为"敏感性证据"而非"倍数"）。
- 需要补什么：（i）**同粒度重算倍数**（B1 的修法，离线可做）；（ii）**变任务阈值**（Table 1 自己写的反驳条件，
  必须做：peak ≥ 0.5/0.6/0.7 三档），（iii）如果可能，加**第二个下游任务**做一个"这种脱耦不是孤例"的格子。
- 风险：**"proxy 不预测下游"这条一般性论点已有先例**（作者自己的检索里就有 Lacuna 的
  *Why Proxy Metrics Fail Downstream Geometric Tasks*，见 `NOVELTY_AUDIT_2026-11.md:71-80`），
  而本文正文 `main.tex:375-378` 讨论这一段时**一个引用都没有**。这条线必须先把先例引清楚，
  否则会被判"重复发现 + 不引先例"。

**主线 C：编辑后证书的三级鲁棒性阶梯（decision table）。**

- 立论：把"什么编辑毁掉证书"做成一张可直接用的判据表，并给出**可预测的机制**：
  coverage 损失由扰动幅度相对 q 的大小决定（SH 量化扰动 3.4–4.1e-4，比残差低三个数量级 ⇒ 0.00；
  几何编辑直接改写支撑集 ⇒ 10.9–18.6）。
- 已有数字：Table 3 全部。
- 需要补什么：**扩编辑种类**（merging、fp16 位置/尺度、anchor VQ），才能叫"taxonomy"而不是"三个点"；
  并且要验证那条机制**能预测**没测过的编辑（否则只是事后解释）。
- 风险：需要新测量，工作量最大；但一旦"扰动幅度/q 能预测 coverage 损失"成立，这是一条真正的**定量规律**，
  比现在任何一条主张都更强。**建议作为 A 的第二幕，而不是主幕。**

**我的建议**：以 **A 为主幕**（摘要第一句讲不对称代价），**C 作为第二幕**（三级阶梯 + 机制），
**B 降级为第三幕**（并且用同粒度的 1.0–2.5× 而不是 12.1×）。B1 的修法本身就是 B 幕的前提。

### M1 [MAJOR] §4 对 AURA 的每条断言逐条核对

核对底本：`_ags_tmp/aura.txt`（2177 行，AURA 全文解析）。

| # | 论文 §4 的断言 | 核对结果 | 证据（aura.txt 行号） |
|---|---|---|---|
| 1 | "four scenes of 107k–130k carriers" | **属实** | L480 `129,531`（Truck）、L485/L489 `120,000`（Garden/Kitchen）、L494 `106,809`（Room）；即 106,809–129,531 |
| 2 | "24–35 held-out label views" | **属实**（可推导） | L521 "Every eighth view is held out"；训练视角 L481 `219`、L486 `161`、L490 `244` ⇒ 留出 ≈ 219/7≈31、161/7≈23、244/7≈35，与 24–35 一致；L500 "observed in ≥3 held-out views" 佐证多视角标注 |
| 3 | "selection AUC of 0.58–0.72 against 0.37–0.53 for opacity" | **属实（数值精确）** | L861-864 校准置信度 `0.581/0.605/0.629/0.720`；L880-884 opacity `0.367/0.450/0.458/0.534`。注意 AURA 的 "AUC" 不是 ROC-AUC，而是 budget-averaged mean retained reliability（L895-896 表注自述），论文承接其术语，可接受但建议加半句说明 |
| 4 | "attaches an **isotonic-calibrated per-carrier reliability**" | **属实** | L14-15 "isotonic (PAVA) calibration of an export-time feature"；L119-122 贡献 2 |
| 5 | "extended into a **certified level-of-detail ladder with a family-wise bound**" | **属实** | L26-29 "certified level-of-detail ladder … family-wise bound … all 16 bounds hold"；L1269-1271 Bonferroni α′=α/3 |
| 6 | "**it evaluates no downstream task**" | **不实** | L86 `RQ3 (downstream value)`；L128 贡献 4 `A downstream selection-quality evaluation`；L591 `used downstream`；L1671 `every downstream consumer of the asset`。AURA 有一个以 "downstream" 为名的研究问题与贡献条目 |
| 7 | "We verified that the words **edit, re-certify and invalidate** do not occur in that paper" | **字面属实，实质上误导** | 我复核：`\bedit`/`re-certif`/`invalidat` 全文 **0 命中**（`credit` 里的 "edit" 子串是假命中）。但概念以别的词写足了：L1275-1280 "assumes … exchangeable … a distribution shift **can violate it** — cross-scene deployment therefore needs a small local conformal set per scene"，且 L1279-1280 自陈有一个 "the bound honestly fails" 的反例；L1327-1336 "The certificate stays valid … keep a small per-scene conformal set to **restore** the distribution-free certificate"，自称 "honest deployment recipe"。**即 AURA 已经写了这条 assumption、已经指出它会破、已经给出重签处方。** 另外 `exchangeab` 5 次、`violat` 5 次、`restore` 2 次 |
| 8 | §4 的定位句："AURA certifies a pruning that follows its own threshold … we ask what happens when the asset leaves that ladder" | **半属实，偏有利于自己** | L8 "downstream **pruning**, streaming, and level-of-detail decisions consume as if it meant something"；L46-48 "pruned to fit a **memory budget** … culled before a viewer sees them" —— AURA 的动机本来就包含"消费者按自己的内存预算剪枝"。真正干净的分界不是"他们只管自己的阶梯"，而是"**AURA 的证书是对保留集风险的一个 bound，参数化在它自己的阈值上；它没有把资产当作签发后会改变身份的物件**" |

**关于第 7 条的论证方式（这一点比事实错误更伤）**：
"We verified that the words *edit*, *re-certify* and *invalidate* do not occur in that paper" 是**字符串论证**。
它传递的潜台词是"我们找不到别的方法说明自己不同，所以数了数词"。TMLR 的审稿人（尤其如果抽到做 conformal 的）
会做两件事：（a）读 AURA 的相关段落，发现 `restore the certificate` / `distribution shift can violate it`；
（b）把这条写进 review，措辞会是 "the authors' novelty argument rests on a word count, and the concept is present
under different terminology"。**这是把一次可以正面陈述的分界，变成了一次诚信质询。**

**替代写法（可直接用）**：

> AURA [Attri 2026] issues a split-conformal bound on the mean unreliability of the retained carrier set under its
> own threshold, and extends it to a level-of-detail ladder with a family-wise correction. It is explicit that
> the bound requires exchangeability between the calibration and the streamed carriers, and that a distribution
> shift can violate it; its remedy is a per-scene conformal set, i.e. re-derive the bound for the same asset in a
> new scene. We ask a question that this framing does not parameterise: the asset has been **rewritten** — pruned,
> re-quantised, reduced in SH degree — and the certificate that ships with it describes a model that no longer
> exists. We measure what that costs in coverage, and, separately, whether coverage is the right quantity to have
> been measuring at all.

这样写：不数词、不否认、把 AURA 的 caveat 变成自己的问题来源，并且**主动把"他们已有 per-scene 重签"说出来**——
审稿人会认为作者读透了这篇文献，而不是在躲它。

### M2 [MAJOR] 相关工作的四个缺口；哪些必须补、哪些补了会削弱自己

现状：全文 12 条 bib，11 条被引用，**1 条从未被引用**（`tibshirani2019`，`main.tex:414` 定义、正文 0 次引用）。
References 之少本身不是问题，问题在**缺口正好压在本文的两条主线上**。

| 缺口 | 状态 | 我的判定 |
|---|---|---|
| **Conformal under distribution shift / beyond exchangeability**：Barber et al. 2023（Annals 51(2):816–845）、Tibshirani et al. 2019（**已在 bib 里但没用**）、Gibbs & Candès 2021（ACI） | 全缺 | **必须补。** 这是本文现象的理论归属；不补 = 承认自己没读自己领域的核心文献。补了**不会**削弱自己，反而提供"实测幅度 vs 理论上界"的新卖点 |
| **Proxy metric vs downstream task**：Lacuna 的 *Why Proxy Metrics Fail Downstream Geometric Tasks*（作者自己的检索已找到，`NOVELTY_AUDIT_2026-11.md:71-80`） | 缺，且 `main.tex:375-378` 那段**零引用** | **必须补。** 现文写"That a component-level proxy need not predict downstream performance is well known across computer vision"——一句断言扫过整个 CV 文献却一个引用都不给，这是审稿人最容易抓的空手道。补 Lacuna 并写明"它是产业研究笔记、无 3DGS 定量结果" |
| **Model cards / datasheets / provenance**（Mitchell et al. 2019；Gebru et al. 2021；model-passing / model-debt） | 全缺 | **补 1–2 条，不要多。** 本文的框架（一份随资产流传、在流转中过期的东西）就是 model card 的统计学表亲。补两条能立刻把"这是个 3DGS 小问题"抬成"这是文档/溯源问题的一个可测量实例"。**但不要展开成"我们是 model card for 3DGS"**——那会把自己的贡献说小，并且引入一个本文没有处理的文献体（版本管理、审计链）。 |
| **Certified / guaranteed compression 与 3DGS 压缩线的交界**（HAC、CompGS、anchor-based 量化的实际位宽） | 部分（LightGaussian/EAGLES/PUP 有，但只用作"报 PSNR") | **补一条即可，但必须补——因为它直接决定 M3 的风险。** 现文把"precision edit = SH 8-bit"当成量化的全部，而 3DGS 压缩的真实字节预算主要在位置/旋转/尺度/anchor 上。补了之后必须**主动缩小规则 (c) 的适用范围**（见 M3） |
| 3DGS 不确定性/校准线（VarSplat、Magic Moments、PUGS 等） | 缺 | **不要补。** 补了会打开"你们的不确定度 vs 他们的不确定度"这条本文没打的仗，而且作者自己的负面结果 N1/N2（`APPENDIX_negative_results.md:8-44`）证明这条路他们走不通。**明确选择不打这场仗。** |

另外：`main.tex:55-56` "the principle that a guarantee is bound to its assumptions is well known in the assurance
literature" —— 也是一个引用都没有的"well known"句。要么引（作者检索里就有 *Assumption-Bound Certificate Leases*、
*Evidence-Centric Certification Maintenance*），要么删掉这半句。**零引用的"well known"在审稿人眼里等于"我编的"。**

### M3 [MAJOR] 规则 (c) 从 "SH-only 8-bit" 外推到 "quantisation" 是越界

摘要原句：`do not re-certify after quantisation`。§3.5(c)：`Quantisation leaves both the coverage and the
interval width unchanged … so a certificate that is valid before an 8-bit SH quantisation stays valid after it`。
但实验做的是 `SH 8-bit`（Table `tab:families` 第 3 行，注明 "precision (bit width)"），**只量化 SH 系数**。
而 3DGS 的真实存储/传输预算里，主导项是位置、旋转、尺度（以及 anchor/VQ），量化这些是**几何扰动**，
按本文自己的机制论证（Table 3 的三级梯度）应当落在"几何"一档。

**后果**：一条本应写成"SH 系数量化对覆盖率无影响，因为扰动比残差低三个数量级"的**有条件的机制结论**，
被写成了"量化不必重签"的**普适规则**，还被放进摘要。做 3DGS 压缩的审稿人（TMLR 大概率抽到）会立刻举反例：
"我量化 anchor 位置，你们的规则就错了。"

**修法**：把规则 (c) 改成机制陈述 + 边界：
`an edit that perturbs the residual far below q is exactly free — 8-bit SH coefficients, whose mean perturbation is
3.4–4.1×10⁻⁴ against a residual three orders of magnitude larger, cost 0.00 points on four scenes and 400 splits.
Quantisation that moves positions or scales is geometric and must be treated as such.`

### M4 [MAJOR] 摘要与正文的三处事实性不一致（复算过，都不是笔误级别）

1. **"with 400 random calibration/deployment splits per scene"**（`main.tex:27-28`）——只有 4 个 released 场景有 400 次划分；
   5 个自训场景是单点估计（Table `tab:main` 的 caption 自己写了 "The five self-trained scenes are single-split estimates"）。
   读者 30 秒能对上，**这是摘要级过度声明**。（注：作者自己的内部评审 `PAPER_REVIEW_expert_team.md:24-32` 已把这条列为 P0/M1，但 tex 版没改。）
2. **"the five self-trained models drop only 6.7 to −0.7 points"**（`main.tex:185`）——符号与顺序都错了。
   实测是 **−6.7 … +0.7**（counter 是 **+0.7**，见 Table `tab:main` 与 `PAPER_certificate_invalid.md:82`）。
   同一句前半句说"Eight of the nine scenes are negative"，后半句给一个 −0.7 的下界，两处互相矛盾。
3. **`main.tex:316` 的 "no post-hoc correction avoids both"**，以及 `:339-341` "A stale certificate is therefore
   *not* detectable from the calibration set alone" —— 这两句是从**一个**负面结果（标定集自检，§3.5）推出来的，
   但"no post-hoc correction"是全称否定。作者既没试 weighted CP（Tibshirani 2019，**就在 bib 里**），
   也没试 ACI。**一个全称否定 + 两个没做的实验 = 审稿人最喜欢的靶子。** 把 "no post-hoc correction" 改成
   "the label-free self-check we could construct does not work, and the weighted/adaptive conformal remedies we did
   not test are the obvious next attempt" —— 或者干脆去做加权 CP（见 §5 第 4 条），把这句话变成一个正面结果。

### M5 [MAJOR] 缺 PSNR/SSIM，且工作点（11–20 dB）没有交代——外部效度的地基是空的

- 全文**没有任何一张图像质量表**（无 PSNR/SSIM/LPIPS 数值表）。资产质量只以括号描述出现：
  released "16–20 dB"、self-trained "11–16 dB"（`main.tex:119-122`）。
- 3DGS 在 Mip-NeRF 360 上的常规量级是 25–27 dB（全分辨率、30k 步）。**16–20 dB（40k 步 checkpoint）
  与 11–16 dB（6k 步）都显著低于常规**，而论文既没写工作分辨率（实为 1/4，`many_splits.py:52 factor=4`），
  也没解释这个差距（`normalize_exposure` 的存在暗示存在曝光/色彩空间不匹配）。
- **为什么这是 reviewer 的必问项**：本文的每一个数字都是**残差的分位数**。残差的绝对尺度决定了
  q 落在 [0,1] 的哪里、决定了"扰动比残差低三个数量级"这类论证、也决定了 SH 量化为什么恰好为 0.00。
  如果残差尺度是被曝光失配抬上去的，那么**场景内部的配对降幅仍然成立**（这点可以辩护），
  但**跨资产的绝对量级与"1.9–12.1×"能不能外推到可部署资产（25 dB）就完全不成立**。
- **修法（离线可做）**：加一张 3 行的资产表（场景 / 基元数 / 视角数 / 分辨率 / PSNR / SSIM / 平均残差 / q），
  并加一句解释残差尺度的来源。这张表同时解决"缺绝对 q"的问题（B2 主线 A 也需要它）。

### MINOR / NIT

- **MINOR** `tibshirani2019` 引而不用（bib 有、正文 0 次）。要么用（M2 里正好该用），要么删。审稿人查 bib 一致性是常规动作。
- **MINOR** PUP 的会议写错了：`main.tex:410` 写 `\emph{ICCV}, 2025`，实际是 **CVPR 2025, pp. 5949–5958**
  （[CVF Open Access](https://openaccess.thecvf.com/content/CVPR2025/html/Hanson_PUP_3D-GS_Principled_Uncertainty_Pruning_for_3D_Gaussian_Splatting_CVPR_2025_paper.html)、[dblp](https://dblp.org/pid/156/7723-2.html)）。
- **MINOR** §2 "Coverage is a **view-level** quantity: the effective sample size is the number of views (16–25),
  not the number of pixels"（`main.tex:132-133`）——**表述不准**。实际上 q 是**逐像素**池化残差上的顺序统计量
  （`many_splits.py:88` `reshape(-1)`），coverage 也是逐像素命中率。作者想说的是"coverage 估计量的**方差**由视角数决定"，
  这句话是对的、也是本文统计上最好的一个决定；但按现在的写法，一个 conformal 审稿人会读成
  "作者以为保形分位数的 n 是视角数"，从而怀疑作者对方法的理解。**改写成一句精确的话：q 是逐像素的 split-conformal
  分位数；由于同一视角内像素强相关，其抽样波动由视角数决定，因此我们在视角层面做 400 次划分。**
- **MINOR** Table 1（claims / evidence / would-be-refuted-if）建议**删掉或压成 3 行**。它是典型的防御性写作产物
  （把论文写成一份自我审计报告），而且它把 "the gap disappears once the task threshold is varied" 写成自己的反驳条件
  ——**那是一个本文没做的实验**（B1/M2 都指到这）。给审稿人一张"你可以这样推翻我"的清单，等于替反方写好了论证。
  `anti-defensive-writing` 的自查第一条正是"这句话是否无意中扩大了本文需要承担的责任"。
- **NIT** `main.tex:201` 的 `*` 无表注；Table 3 的 SH 行有的带区间（`\small[−1.5,−0.6]`）有的不带（flowers），格式不统一。
- **NIT** `main.tex:311-313` "2–4 held-out views restore coverage to near nominal"——treehill 在 n=2 时是 **0.971**，
  比名义 0.90 高 7 个点，这是**过覆盖**（区间更宽），不是 "near nominal"。这句话应当把过覆盖讲成"代价"的第二种形态。
- **NIT** 图 1 的 SH 8-bit 一组在视觉上完全不可见（值为 0），建议改成对数轴或直接删掉这一组、只用正文数字。
- **NIT** 论文声称 "Code, per-scene result files and the check suite are provided as anonymised supplementary material"
  （`main.tex:356-357`），但 `submission/` 目录里**没有**补充材料包（只有 `tmlr.zip` 模板）。投稿前必须打包（清单见 `TMLR_SUBMISSION_CHECKLIST.md` 第四节）。

---

## 3. "to our knowledge, the first such comparison for 3DGS" 可辩护吗？

**部分可辩护，但现在的写法不可辩护**，原因是有两个必须处理的对象，而论文一个都没处理：

1. **Lacuna 的 proxy-metrics 笔记**：给出了一般的"组件代理指标 ≠ 下游任务"论证。本文的说法是
   "the first such **comparison for 3DGS**" —— 限定在 3DGS，字面上不被它否掉。
   但现在的正文连它都不引，于是这个"first"在一个已经被一般性讨论过的论点上做局部优先权，很脆。
2. **AURA 的 RQ3（"downstream value"，`aura.txt:86`）**：它确实做了一个下游评估（selection quality）。
   本文的 "first such comparison" 若被理解成"第一个做下游评估的 3DGS 证书工作"，**直接不实**。

**可辩护的表述**（建议替换 TMLR 版贡献列表第 2 条）：

> We are not aware of a published measurement that pairs a coverage-type certificate for a 3DGS asset with an
> **externally defined** downstream task — one whose success is not itself a function of the certificate's
> calibration residuals. AURA evaluates downstream **selection quality**, but the quantity it reports is the
> retained reliability, i.e. the very statistic the certificate bounds.

同时把 `first` 从摘要与贡献列表里降级为 Related Work 里一个带 "we are not aware of" 的句子——
TMLR 明说不以 novelty 为接收标准，**priority claim 在 TMLR 是纯负债：收益极小而攻击面极大。**
作者自己的检索报告（`NOVELTY_AUDIT_2026-11.md:123-124`）已经得出同一个结论（"不能声称首次"），只是没落到 tex 里。

---

## 4. 可发表价值提炼

**这篇文章最值得发表的发现（3–5 句）**：

一份 3DGS 质量证书被编辑之后，恢复它的**有效性**几乎不需要成本，恢复它的**信息量**则完全做不到：
两个留出视角就能把覆盖率拉回名义值，但证书承诺的误差阈值 q 会比签发时永久宽 26–71%，
而且这个损失不随标定数据增加而回收。这意味着"coverage = 1−α"根本不是一个可用的验收标准——
两份都满足名义覆盖率的证书，信息量可以差一个整数倍，而没有任何一个数字把这件事告诉消费者。
本文用 400 次随机划分的配对设计在 9 个场景上量出了这个不对称，
并且顺带证明了一件更不舒服的事：**看起来唯一的免标签补救（用标定集自检）在数学上不可能工作**，
因为 q 就是那批残差的分位数，再拿这批残差去数覆盖率，按定义就是 1−α。
因此流程结论是硬的、且与现有工具的产物无关：**证书必须在编辑之后签发，签发时刻的资产是唯一被保证的资产。**

**摘要应该怎么重写**（第一句就要出现问题和贡献，不要从"3DGS 很方便部署"起手）：

> A quality certificate that ships with a 3D Gaussian Splatting asset is a promise about one model at one moment,
> and the moment passes: assets are pruned, quantised and re-exported by whoever receives them.
> We measure what it costs to keep the promise. Across nine scenes and 400 random calibration/deployment splits per
> released checkpoint, the interesting cost is not validity but precision: **two held-out views are enough to restore
> nominal coverage after a 30% prune, and no number of views restores the width** — the certified error threshold
> stays 26–71% larger than it was at issuance, so a certificate that is perfectly valid can be materially less useful
> than the one it replaced. We also show that the obvious label-free way to detect a stale certificate cannot work:
> re-running calibration returns 1−α by construction, while the true deployment coverage is 0.768–0.864.

**引言的第一段应该怎么起**（替换现在从 compression 文献起手的开头）：

> The question worth asking about a certificate is not whether it survives an edit — a guarantee is only as good as
> its assumptions, and pruning is designed to break the exchangeability that a distribution-free guarantee needs.
> The question is what it costs to make it true again, and whether the repaired certificate still tells a consumer
> anything they can act on. We measure both, and the two answers point in opposite directions.

**为什么这样改**：这两段把"失效"从**结论**降级为**前提**（一句带过、不辩护），把版面全部让给
"有效性可修复 / 精度不可修复"这个**不显然、且本文唯一测过的**不对称。同时摘要不再出现 12.1×，
把 B1 的攻击面从摘要里拿走。**这正是 `anti-defensive-writing` 的第 5、6 条：故事服务于最强证据，
而不是忠于最初的设想。**

---

## 5. 如果由我写 rebuttal / revision plan（按"每单位工作量降低的拒稿概率"排序）

| # | 动作 | 工作量 | 降低拒稿概率 | 类型 |
|---|---|---|---|---|
| 1 | **修 B1**：Table `tab:downstream` 列头加 `(voxel)`、加一列 pixel 粒度、摘要把 1.9–12.1× 改成 `1.0–12.1× depending on granularity`、并给两个粒度的区间；补任务侧的配对设计与区间 | ~半天 + 10 分钟 GPU | **极高**（这是唯一能被审稿人独立复算出来的、指向摘要第二句的错误） | `[离线可改]`（重算）+ `[需要新测量]`（配对重跑任务侧） |
| 2 | **换主线**：标题/摘要/贡献列表从"失效"改为"修复的不对称代价"；"失效"降为一句前提；Table 1 删掉或压到 3 行 | 1 天，纯写作 | **高**（决定 criterion 2 的 interest；也顺手消掉"unsurprising"） | `[离线可改]` |
| 3 | **重写 §4 + Related Work**：删掉"数三个词"的论证，改用 M1 的替代写法；补 Barber 2023 / Tibshirani 2019 / Gibbs-Candès / Lacuna / model cards 2 条 / 3DGS 量化位宽 1 条；修 PUP 的会议名；"evaluates no downstream task" 改成精确表述；修 M4 的三处不一致 | 1 天，纯写作 | **高**（把一次诚信质询换成一个"他们读透了文献"的印象；同时清掉摘要级过度声明） | `[离线可改]` |
| 4 | **做两个"本文自己列的、但没做"的实验**：(a) 变任务阈值（peak ≥ 0.5/0.6/0.7）与 patch size；(b) **加权保形 / ACI** 用附录 B.1 里已有的两个免标签难度协变量（渲染逃逸质量、渲染梯度）当权重。若 (b) 失败，就把 "no post-hoc correction avoids both" 从全称否定变成**有实验支撑的**窄结论；若 (b) 成功，本文就从"测量"升级为"测量 + 部分修复方案" | ~1–2 天 GPU（残差已存，主要开销在重渲染少量配置） | **中高**（(a) 直接消掉 Table 1 自己写的反驳条件；(b) 消掉"你们没试过标准补救"这个必问项） | `[需要新测量]` |
| 5 | **补资产质量表**：场景/基元/视角/分辨率/PSNR/SSIM/平均残差/q，并解释 11–20 dB 与残差尺度的来源；同时满足"缺绝对 q"和 M5 | ~半天（渲染已跑过，可能已有数据） | **中**（外部效度的地基；也让"26–71% 变宽"这句话有物理含义） | `[需要新测量]`（少量）/ `[离线可改]`（若 PSNR 已存） |

**不做的**：不要补第二个下游任务、不要扩展到更多场景、不要做方法创新（作者的 10 个负面结果
`APPENDIX_negative_results.md` 已经证明那条路走不通，而且 TMLR 不要求 novelty）。
**每一份额外实验预算都应该花在"把已有数字讲对"上，而不是"增加数字"上。**

---

## 6. 判定

### 现在：**Reject**

- **criterion 1（主张是否被证据支持）fail**：摘要第二句与贡献列表第 2 条的核心数字（1.9–12.1×）
  在论文自己的主指标下是 1.02–2.47×，且其中一格（stump）"低估"实质上不存在（B1）。
  这不是修辞问题——Table 2 与 Table 3 对同一资产给出两个都叫 "coverage drop" 的不同数字（10.9 vs 4.6），
  而论文没有一处解释它们为什么不同。
- **criterion 2（interest）borderline fail**：主线选在 assumption-violation 上，对目标读者是同义反复；
  真正不显然的那句话（有效可修、精度不可修）被埋在第三条规则里。
- 另有两处会被独立发现的事实性问题：AURA "evaluates no downstream task" 不实（M1-6），
  摘要"每场景 400 次划分"对 5/9 场景不成立（M4-1）。

### 改到什么程度我会 accept

**我会接受一份满足以下 5 条的版本**（都不需要新方法、不需要新场景、不需要和 SOTA 比）：

1. **摘要与 Table 3 的粒度一致**，倍数以区间报告，且至少在一个粒度上给出与主表同口径的比较（B1）；
2. **摘要第一句讲"有效性 vs 精度"的不对称**，而不是讲证书会失效（B2 主线 A）；
   我能从摘要里读到"2 个视角恢复覆盖率 / q 永久宽 26–71%"这个具体的不对称；
3. **§4 不再用字符串论证**，并正确陈述 AURA 的 exchangeability caveat 与 per-scene 重签处方；
   `evaluates no downstream task` 改成可辩护的表述；`first` 降级为 "we are not aware of"（M1、§3）；
4. **补上 conformal-under-shift 的文献（至少 Barber 2023 + 用上已有的 Tibshirani 2019）、
   补上 proxy-metric 先例（Lacuna）、修掉 M4 的三处不一致与 M5 的资产表**（M2、M4、M5）；
5. **规则 (c) 收窄到"扰动远低于 q 的编辑"**，不再从 SH-only 外推到 quantisation（M3）。

满足 1–4 我会给 **accept**；只满足 1–2 会给 **reject but encourage resubmission**，
并在意见里明确"这个测量本身值得发表，问题是它现在被讲成了另一个故事"。

---

## 附录 A：核对记录（可复现）

**AURA 关键词命中（`_ags_tmp/aura.txt`，2177 行，大小写不敏感）**

| 查询 | 命中数 | 位置 |
|---|---:|---|
| `\bedit` / `edits` / `editing` / `edited` | **0** | — |
| `re-certif` / `recertif` / `invalidat` / `revoke` / `stale` / `expire` / `obsolet` | **0** | — |
| `credit`（"edit" 子串的唯一来源） | 2 | L386, L387（"under-credit"，与编辑无关） |
| `downstream` | 4 | L8（downstream pruning decisions）、**L86（RQ3 downstream value）**、**L128（downstream selection-quality evaluation）**、L591、L1671 |
| `exchangeab` | 5 | 含 **L1275-1276**（"assumes … exchangeable"） |
| `violat` | 5 | 含 **L1277**（"a distribution shift can violate it"）、L1279-1280（"the bound honestly fails"） |
| `restore` | 2 | 含 **L1335-1336**（"keep a small per-scene conformal set to **restore** the distribution-free certificate"） |
| `recalibrat` / `quantiz` / `tamper` | 0 | — |

**AURA 表格数值（Table 5，L855-899）**：calibrated `0.581/0.605/0.629/0.720`；oracle `0.601/0.619/0.633/0.729`；
raw heuristic `0.426/0.404/0.439/0.552`；random `0.406/0.426/0.442/0.528`；opacity `0.367/0.450/0.458/0.534`；
opacity@10% `0.306/0.450/0.470/0.489`；calibrated@10% `0.770/0.797/0.836/0.896`。
场景规模：L480-494（129,531 / 120,000 / 120,000 / 106,809），训练视角 L481/486/490（219/161/244），
留出规则 L521（"Every eighth view is held out"）。

**B1 复算（`research/results_v60/vt_flowers.json` + `vt_rest.json`）**

| 场景 | `voxel_prune30_drop_mean` | 95% 区间 | `task_clean_hit`→`task_prune30_hit` | 任务降幅 | Table 2 像素降幅 | 同粒度倍数 |
|---|---:|---|---:|---:|---:|---:|
| flowers  | 0.046061 | [0.0175, 0.1044] | 0.7409 → 0.5727 | 16.82 | 10.9 | 1.54× |
| bicycle  | 0.061447 | [0.0192, 0.1169] | 0.8960 → 0.6800 | 21.60 | 18.6 | 1.16× |
| treehill | 0.026075 | [0.0165, 0.0409] | 0.5889 → 0.2722 | 31.67 | 12.8 | 2.47× |
| stump    | 0.061433 | [0.0333, 0.0998] | 0.9063 → 0.7875 | 11.88 | 11.7 | **1.02×** |

对照论文报的体素倍数：16.82/4.606=3.65×、21.60/6.145=3.52×、31.67/2.608=12.14×、11.88/6.143=1.93×
（与摘要 1.9–12.1× 一致，说明我对表 3 的读法无误）。

**代码侧证据**
- `research/code/scripts/many_splits.py:88-90`：q 与 coverage 均为逐像素（`reshape(-1)`）→ Table 2 是 pixel-level。
- `research/code/scripts/voxel_and_task.py:5-7`（docstring：per-voxel max-residual）、`:97-99`（`pooled` = `nanmax` over views）、
  `:120-137`（voxel 降幅）、`:143-156`（任务）→ Table 3 的证书列是 voxel-level。
- `voxel_and_task.py:145-154`：`rng` 在 clean/prune50/prune30 之间连续消耗 ⇒ **三个变体用不同 patch 集，任务侧非配对**。

**未核实项（如实标注）**
- `vscp2026`（arXiv:2609.10307）、`manifoldgs2026`（arXiv:2608.00214）、`dong2026conformal`（Pattern Recognition 180:114249）、
  `attri2026aura`（DOI 10.31224/7689）的**书目元数据**：本次未联网核对（按任务要求，仅在核对引用真伪时联网；
  已核对 PUP 与 Barber 两条，均已给出 URL）。其中 AURA 由本地全文 `_ags_tmp/aura.txt` + `aura.pdf` 直接核对，可信。
- 论文声称的 "104 assertions / 46 unit assertions"：**未运行** `verify_paper_numbers.py`（审稿不执行代码）。
  但可指出：该检查若只做"表格数字 ↔ JSON 字段"的一致性，**不会**发现 B1 的粒度错配，因为两处都自洽。
  这是"自动校验抓不到的科学错误"的一个好例子。
