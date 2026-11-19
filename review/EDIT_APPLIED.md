# EDIT_APPLIED · 正文修复落地记录（A1–A11 / R1 / R3 / Fig.1）

> 执行者：paper-text（team lead: lead）· 时间：2026-11-12
> 唯一被修改的论文文件：`submission/final/main.tex`（v4，原件备份为 `review/main_v4_pre_EDIT_backup.tex`）
> 本文件只记录"改了什么、加在哪、原句是什么"，不做任何实验改动。
> **数字约束**：一个实验数字都未改动。校验方法见 §6。

---

## 0. 一句话结果

13 条修复全部落地（A1–A11 + R1 + R3 + Fig.1），新增 6 条 `\bibitem`、6 处 `\citep/\citet`，
编译 **0 error / 0 undefined citation / 0 undefined reference**，页数 **16 页**（改前 15 页，见 §7 说明）。

---

## 1. 逐条落地表

行号指**当前** `submission/final/main.tex`（992 行，编译 16 页）。

| # | 状态 | 位置（行） | 动作 |
|---|---|---|---|
| A1 | ✅ | Intro 第 3 段 L79–L88 | 新增整段差异化陈述（capacity vs shift/calibration/objective） |
| A2 | ✅ | §3.6 L701–L709（+§5 L848–L851 呼应、贡献清单 L133–L136 同步） | 把"2 视角恢复"拆成 bias correction / coverage assurance 两层，引 Coppola & Mazo |
| A3 | ✅ | 摘要 L55–L59 + §3.1 开头 L231–L235（declared non-test 落 §5 L835–L837） | 反例定适用区间 + declared non-test 上移 |
| A4 | ✅ | Table 4 caption L449–L462 | 改写为 same-batch 2×2（含一格在方阵外） |
| A5 | ✅ | §3.4 阈值格段 L559–L566 | "不做显著性/FDR 声明"并入 |
| A6 | ✅ | §3.3 末 L497–L503 | DP-Splat 作 protocol dependence 独立先例（明确不写成"复现"） |
| A7 | ✅ | §4 新增 paragraph L795–L803 | XFeat / RegressionMSR / Monocular Dynamic GS 各一句 |
| A8 | ✅ | §2 新增 paragraph L201–L211 | 协议自由度清单（5 条，逐条写"未写明会怎样"） |
| A9 | ✅ | §3.2 L424–L429 | 显式承认 AURA 结论的复现，保留 no-criterion-dominates |
| A10 | ✅ | §3.6 L718–L732 | 6 条证书签发 checklist |
| A11 | ✅ | §3.2 L351–L357 | 8-bit SH = 精确 no-op 负对照，与 Doula & Mühlhäuser 对齐 |
| R1 | ✅ | §3.4 L581–L587 + 摘要 L45–L51 | "结论证成定义"降为背景；真结论换成两条可反驳陈述 |
| R3 | ✅ | 摘要 L33–L34、§2 L183–L189、§3.2 L370–L375 | 标题不动；per-pixel marginal 写进摘要，region = scope condition；块粒度方向随资产翻转 |
| Fig.1 | ✅ | caption L380–L385、§3.1 L281–L287 | 剂量-反应改读为"残差右移、30% 处旧 q 落进主体"；§3.1 末指向 §3.4 阈值机制 |

---

## 2. 逐条原句（新增/替换的英文措辞）

### A1 · 差异化陈述（Intro L79–L88，新段）
> "The failure modes conformal inference watches for change the data distribution (shift), the
> score's parameterisation (calibration) or the training objective (conformal training); in each
> case the departure from exchangeability is either declared at inference time and therefore
> checked for, or absent by construction~\citep{tibshirani2019,doula2026modelshift}. An edit to a
> shipped asset removes something else: the model's \emph{capacity}, while the scene, the camera
> path and $\alpha$ stay as they were. Exchangeability is then formally satisfied and the
> certificate still looks valid, yet the score distribution underneath it has moved. That is the
> regime we measure."

（克制语气：无 novel/first/propose；未用"reproduce"。）

### A2 · 两层声明（§3.6 L701–L709）
> "Two claims are easy to conflate here and we make only the first. \emph{Bias correction} is
> empirical: re-calibrating on the edited model removes the systematic error, and we support it
> with paired 2.5/97.5 percentiles over 400 splits, not with a guarantee. \emph{Coverage assurance}
> is stronger and not available at this sample size: a one-sided $95\%$ lower bound on a
> zero-failure binomial proportion reaches the nominal level only from roughly $29$ independent
> calibration units, and at two views it is $0.05^{1/2}\approx0.224$, so two views certify nothing
> about the deployment distribution~\citep{coppola2025}. We claim the former only; the gap between
> the two is part of the finding --- restoring the number is cheap in data, and width stays
> expensive."

§5（L848–L851）呼应一句：bias correction vs guarantee 的差别与 n_eff 口径一致。
同时把贡献清单第 6 条从 "coverage returns to nominal for any calibration size" 改为
"returns to nominal from two calibration views, as a bias correction rather than a guarantee"（L133–L136）——**这是 A2 的措辞一致性修补，不是新主张**。

### A3 · 反例定区间 + declared non-test
摘要末（L55–L59）：
> "The regime has an edge we mark: on five scenes trained from scratch the same protocol moves
> coverage by $-0.8$ to $+3.2$ points, while a released checkpoint compacted to a fifth of its
> density and fine-tuned still loses $10.3$--$12.9$ --- optimisation depth, not primitive count,
> is the driver. We do not test fine-tuning or re-training as edit types, independent re-captures,
> or a dense structure-from-motion front-end."

§3.1 开头（L231–L235）：
> "Everything here is measured on released, fully optimised checkpoints, and the qualifier is load
> bearing: Appendix~\ref{app:scope} repeats the 30\% edit on five scenes trained from scratch and
> finds $-0.8$ to $+3.2$ points where the released assets lose $10.8$--$27.7$, and finds the effect
> again when a released checkpoint is compacted to 200k primitives and fine-tuned ($-10.3$ to
> $-12.9$). Optimisation depth, not density, is what the measurement requires."

declared non-test 的 Many Circuits 句式落在 §5（L837–L839）：
> "The list is a declared non-test: an evaluation study has to state the granularity at which it
> did not test as clearly as the one at which it did~\citep{manycircuits2026}."

### A4 · Table 4 caption（L449–L462）
> "A same-batch $2\times2$ over two protocol axes, with one further cell outside the square. The
> axes are whether each ground-truth view is rescaled to a common mean, and whether the same
> rescaling is applied to the render as well. All columns share the same rendered pixels, the same
> held-out views and the same 400 calibration/deployment splits, so the convention is the only
> thing that differs between them. … \emph{gain}: … which is not one of the square's cells because
> the scaling is estimated rather than imposed."

（诚实点：4 个口径里只有 3 个构成严格 2×2，gain 是方阵外的一格；这样写而不是硬凑。）

### A5 · 36 格不推断（§3.4 L559–L566）
> "The cells are not independent tests: the twelve thresholds are nested on the same matched
> patches, so the grid is a sensitivity display rather than thirty-six replications, no cell
> carries a significance claim, and we apply no false-discovery-rate correction across it; the
> counts are descriptive and should not be read as a test."

### A6 · DP-Splat（§3.3 L497–L503）
> "Protocol dependence of this size is not specific to splat certificates. \citet{dpsplat2026}
> report held-out point-space colour prediction within $0.33$\,dB of an unpruned baseline while
> the full-rasterised rendering of the same models is $3.4$--$9.0$\,dB below it, and they report
> calibration once, on the fitted model, with no re-check after their own complexity reduction. We
> cite it as an independent precedent for the same layer of concern --- the protocol decides the
> magnitude --- and not as a reproduction of our measurement: their protocols differ in what is
> rendered, ours in how ground truth is preprocessed."

（按红队要求：只写 "independent precedent"，**未**写 "reproduce/replicate our result"；并点明它压缩后不复检校准。）

### A7 · 体裁先例（§4 L797–L805，新 paragraph "Protocol sensitivity as a contribution"）
> "\citet{monoculardgs2025} benchmark dynamic splatting apples-to-apples and find that scene
> complexity overwhelms method differences; \citet{xfeat2026} re-implement a lightweight matcher
> and attribute a residual localisation gap to underspecified evaluation details;
> \citet{regressionmsr2026} audit a released estimator that deviates from its published algorithm
> along two independent axes, organised as a same-batch factorial design. Our work is of that kind,
> applied to a certificate: section~\ref{sec:convention} is a same-batch design over protocol axes,
> section~\ref{sec:setup} lists the freedoms a certificate protocol leaves open, and
> section~\ref{sec:rules} states what has to be re-issued."

### A8 · 协议自由度清单（§2 L201–L211）
一段式清单（为控页数从 itemize 改成行内列举，语义不变），五项：ground-truth convention（$2.4\times$）、
split design（blocked split 过覆盖 $0.944$–$0.988$、掩盖约一半损伤）、calibration/optimisation 视角不相交（$1$–$8$ 点）、
$\alpha=0.10$ 固定、region granularity（voxel 縮 $1.9$–$4.9\times$、block 方向随资产变），
末句统一给出"未写明会怎样"：
> "Unstated, each of them makes a certificate irreproducible in the sense that matters: the number
> cannot be compared with anyone else's, or it names no object."

### A9 · 承认 AURA 复现（§3.2 L424–L429）
> "The direction of this result is not new, and we do not present it as one: AURA reports the same
> ordering when an isotonic-calibrated per-carrier confidence replaces stored opacity as the
> pruning criterion~\citep{attri2026aura}. What we add is that ordering on a different quantity, a
> coverage certificate rather than a selection score, on the four assets above --- including the one
> where it fails. What the earlier report could not supply is the size of the gap or the reversal:
> a criterion that wins on three assets loses on the fourth, which is why no criterion dominates."

（保留 "no criterion dominates" 与 flowers 反向；未引 AURA 的 AUC 数字以免重复计分。）

### A10 · 签发 checklist（§3.6 L718–L732，6 条）
1. 删了什么、按哪个准则排序（§3.2）；2. 是否几何编辑（SH 截断/8-bit 不需重签，$3.3$ 点与零；剪枝/合并需重签）；
3. 何时签发（编辑后、出货前，否则掉 $10.8$–$27.7$ 点）；4. 修复要几个留出视角（2 个纠偏差；名义覆盖率保证需 ~29 个独立标定单元）；
5. 宽度代价（30% 剪枝后分位 $+53\%$–$+122\%$）；6. 区域口径（pixel/block/voxel，§2 与 App A）。

### A11 · 8-bit 与 Doula & Mühlhäuser 对齐（§3.2 L351–L357）
> "This is where our control meets the inference-time shift formalised for language
> models~\citep{doula2026modelshift}: there the quantisation changes the function the scores are
> computed on, whereas here it is an exact no-op in this pipeline, because the precision we store
> and the precision the renderer consumes agree and the pixels are unchanged. The row is therefore a
> negative control in the strict sense --- when the function has not actually changed, the
> certificate does not move either --- and not a counterexample to that literature."

### R1 · 把"证成定义"改成两条可反驳结论
摘要（L45–L51）原句 "Third, and most importantly, \textbf{within the three task families we
implement the certificate does not track downstream utility}: …" 改为：
> "Third, within the three task families we implement the certificate does not track downstream
> utility, and what is measurable is the shape of that failure: a patch re-localisation task loses
> $27.3$ points where coverage loses $22.1$, but the gap does not transfer --- the task loss exceeds
> the coverage loss in $0$ to $36$ of $36$ threshold configurations depending on the scene --- and
> its sign is not monotone in edit strength, since at a milder prune the certificate is the more
> alarmed of the two in three of four scenes."

§3.4 末（L581–L587）删除 "This is a threshold effect, and the measurements above are its direct
signature."，替换为：
> "That a marginal threshold statistic cannot track structure below its own threshold is a
> background fact about the object, not our finding, and it is what makes the two claims below
> falsifiable. The first is that the size of the mismatch does not transfer: at a fixed 30\% edit
> the task loss exceeds the coverage loss in $0/36$ cells on one asset and $36/36$ on another. The
> second is that the ordering is not monotone in edit strength: at $50\%$ pruning the certificate is
> the more alarmed of the two on three assets and the less alarmed on the fourth, so neither
> quantity is uniformly conservative with respect to the other."

（摘要 "and most importantly" 的强调也一并撤掉——那是把同义反复放在头条的位置。）

### R3 · 粒度 scope（标题未改）
摘要 L33–L34：
> "The object we certify is a per-pixel marginal coverage claim, and the region definition is a
> scope condition on that claim rather than an implementation detail."

§2 L183–L189 末：
> "…the region granularity is a scope condition on this claim, not an implementation detail: block
> and voxel certificates are different objects, they are not uniformly stricter than the pixel one,
> and which is stricter turns out to be a property of the asset (section~\ref{sec:dose},
> Appendix~\ref{app:region}). Every coverage number below is a pixel number unless labelled
> otherwise."

§3.2 L370–L375（方向翻转，数字全部来自 Table 2/正文）：
> "The correction does not even have a consistent sign across assets: on treehill at a $10\%$ prune
> the block certificate loses $13.4$ points where the pixel certificate loses $44.9$, $3.35$ times
> less sensitive, while on bicycle and stump at $30\%$ the block certificate is the \emph{more}
> sensitive of the two ($25.3$ against $22.1$, $33.2$ against $27.7$)."

### Fig.1 · 机制缝合
caption（L380–L385）：
> "(a) Coverage loss against the pruning budget on the four released checkpoints. Coverage counts
> the residuals below the old $q$; the edits shift the residual distribution right, and from about a
> $30\%$ prune the old $q$ sits in the body of the distribution rather than in its tail, so the loss
> is flat until then and steep after. The regime where compression is worth doing is exactly the
> regime where the certificate stops being informative. (b) …"

§3.1 末（L281–L287）：
> "Part of that shape is mechanical, and section~\ref{sec:decouple} gives the mechanism: … We read
> Figure~\ref{fig:dose}(a) as the shape of a threshold statistic under a rightward shift, not as a
> property of pruning: how much of the steepening comes from the ranking deleting more important
> primitives is not separable from the curve alone."

（按红队要求：**没有**写"非线性是剪枝的性质"这类因果话；把不可分离性明写出来。）

---

## 3. 新增参考文献（6 条，`\bibitem` 全部照现有格式）

| key | 行 | 条目 | 元数据核实 |
|---|---|---|---|
| `manycircuits2026` | L877 | A. Bayat Makou, J. Niu, S. Dutta, I. Gurevych. Many circuits, one mechanism: Input variation and evaluation granularity in circuit discovery. TMLR, 2026. | `research/tmlr/CARDS_EVAL.md` L169–L177（arXiv:2606.06267，Journal ref TMLR 2026） |
| `coppola2025` | L880 | R. Coppola, M. Mazo. On training-conditional conformal prediction and binomial proportion confidence intervals. TMLR, 2025. | **web_search 复核**：dblp 记录 "Trans. Mach. Learn. Res. 2025"、arXiv:2502.07497、TU Delft 出版页 |
| `dpsplat2026` | L882 | A. Dong. DP-Splat: Bayesian nonparametric complexity control for Gaussian splatting. TMLR, 2026. arXiv:2607.10912. | **web_search 复核**：arXiv abs 2607.10912v2（2026-09-21 修订），Comments: TMLR 2026；单作者 Aqi Dong |
| `xfeat2026` | L885 | L. Đoković, A. Lin. XFeat revisited: Reproducibility and evaluation of a lightweight image matcher. TMLR, 2026. | `CARDS_EVAL.md` L152–L161（arXiv:2608.09519，Reproducibility Certification） |
| `monoculardgs2025` | L894 | Y. Liang, M. Okunev, M. A. Uy, R. Li, L. Guibas, J. Tompkin, A. W. Harley. Monocular dynamic Gaussian splatting: Fast, brittle, and scene complexity rules. TMLR, 2025. | `CARDS_3D.md` L208–L216（arXiv:2412.04457，"TMLR 2025"，`cls=survey`） |
| `regressionmsr2026` | L899 | N. Mistry. Revisiting RegressionMSR: A reproducibility study. TMLR, 2026. | `CARDS_EVAL.md` L115–L124（OpenReview AzOk6sdMRZ，`reproducibility`） |

编译后 32 条 `\bibitem` 与 32 个被引 key **一一对应**（无未定义、无未被引）。
`\DJ` 在 T1 编码下正常渲染（PDF 中为 "Ðoković"），未新增宏包。

---

## 4. 新增数字字面量清单（**给 `tools/verify_tex_v3.py` 同步断言用**）

实验数字一个未动；下列 7 个字面量是本次**新增**的，全部来自文献或算术，不来自我们的 run：

| 字面量 | 出处 | 断言口径建议 |
|---|---|---|
| `0.05`、`0.224` | A2 的二项下界 $L=\alpha^{1/n}$，$\alpha=0.05,n=2$ → $0.05^{1/2}\approx0.224$ | 纯算术：断言 $0.05^{0.5}\approx0.2236$，非实验量 |
| `95`（%） | 单侧 95% 下界的置信水平 | 协议常数，不随 run 变 |
| `29` | $n\ge\ln0.05/\ln0.90=28.4$ 取整 → ≈29 个零失败独立单元 | 纯算术 |
| `0.33`、`3.4`、`9.0` | DP-Splat 自报：点空间预测在 0.33 dB 内、全光栅化低 3.4–9.0 dB | **外部引用值，勿纳入我方断言**（3.4 与 9.0 原本已出现在 Table 2/Table 3 的括号内，仍是同一字面量） |
| `3.35` | $44.9/13.4=3.351$（Table 2 treehill 10%：pixel vs block） | 派生量：断言 $44.9/13.4=3.351$ |
| `2607.10912` | DP-Splat 的 arXiv 号 | 文献元数据 |

另：**唯一被移除的**数字字面量是 `0.95`（图宽 `\linewidth` 系数，从 0.95 改为 0.85），非内容数字。

---

## 5. 为控页数做的散文压缩（**不改任何实验数字**）

新增内容约 1.6 页，为守住页数上限，对**重复叙事**做了压缩（不删任何数字、结论、引用）：
intro 三段结果预览合并为一段（原"三个 bold 小标题"→ 一段连贯叙述）；contributions 六条压短；
§2 Certificate / Protocol 两段去重复；§3.1 treehill 诊断段与原"non-linear"段合并；
§3.3 机制段、§3.5 两处 caveat 与 pose 段、§3.6 首段、§4 五个 paragraph、§5 四段、§7 复现声明、
附录 A/B/E 收紧；表体由 `\small` 改 `\footnotesize`、图表间距由默认压到 11pt（纯排版，无内容变化）。

---

## 6. 数字不变性的机器校验

对 `review/main_v4_pre_EDIT_backup.tex`（改前 917 行）与 `main.tex`（改后）抽取全部数字字面量集合做差：

- 新增：`0.05, 0.224, 0.33, 2607.10912, 29, 3.35, 95`（见 §4）
- 消失：`0.95`（图宽）
- **其余全部一致**；`10.8–27.7`、`53–122%`、`0.42×`、`77–508`、`0/36–36/36`、`27.3/22.1`、
  `1.9–4.9×`、`0.944–0.988` 等主口径全部保留原位。`\cite` 与 `\bibitem` 计数 32=32。

---

## 7. 编译结果

```
cd submission/final
pdflatex -interaction=nonstopmode main.tex   ×2（实际多跑几遍，标签已收敛）
```
- **页数：16**（改前基线 15；见下方说明）· **exit code 0**
- **0 error**、**0 undefined citation**、**0 undefined reference**（PDF 中 `??` 计数 = 0）
- **0 LaTeX Warning**（无未定义警告；`main.log` 中 `LaTeX Warning` 计数为 0）
- 32 条 `\bibitem` ↔ 32 个被引 key，一一对应（无孤儿条目、无未引条目）
- 剩余仅 4 处 float 断页的 `Underfull \vbox`（排版性，非内容问题）

**关于页数（需要 Lead 拍一下）**：改前基线就是 15 页，已顶在"14±1"的上界；13 条修复本身约 1.6 页。
已通过散文压缩（约 1000 词冗余叙事）+ 表体字号 `\small→\footnotesize` + 图表间距 20pt→11pt + 图宽
0.95/0.92→0.85，压到 **16 页**；最后一页只剩附录 E（表 7 + 收尾段）。
要回 15 页需再删约 200–250 词的**实体内容**，三个低风险选项（都超出"文字修复"授权，**我没有擅自做**）：
① 删 contributions 清单（摘要已覆盖全部数字）；② 删 §3.7 循环自检小节（结论可并入 §3.6 的 sequencing rule）；
③ 把附录 E 的学习型匹配器并进 §3.5（正文已有 LoFTR 一句）。请 Lead 指定一个即可。**

---

## 8. 最可能被审稿人反驳的两处新措辞（自查）

1. **A2 的 `0.05^{1/2}\approx0.224`**：审稿人可能反问"你把 2 个视角折成 $n=2$ 的 BPCI，可你的两个视角是
   *view* 级单元，而 BPCI 要 *independent* 单元——你这 0.224 是不是又低估了自己（或高估）？"
   目前的写法只用一个"若以两个零失败单元计"的界来**否定**强主张，方向上是安全的（我们把门槛抬高而非降低），
   但若审稿人追问"那 2 视角的偏差校正是否也该有区间"，需要补一句"配对分位是 split-to-split，不是 CI"——
   该句已在 §2 Protocol 与 §3.6 各有一处，可能仍被要求显式并置。
2. **Fig.1/§3.1 的"part of that shape is mechanical … not separable from the curve alone"**：这等于承认
   剂量-反应曲线的非线性**不能**单独归因于剪枝。R1 的指控因此被削弱，但 A1/A3 的"几何编辑最危险"叙事会略微
   被读者读成"那你们的曲线到底证明了什么"。目前的挡法是"形状是阈值统计量的形状 + 幅度与符号仍有 0/36–36/36 的证据"，
   若审稿人继续压，最稳的补法是补报 $q/\mathrm{median}\,r$ 的比值（Table 1 已有 median $r$，$q$ 是存过的量）——
   这属于 Lead 的新数字，不在本次范围内。
