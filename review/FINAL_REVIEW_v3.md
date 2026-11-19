# FINAL_REVIEW_v3 — *Valid but Unusable: What Coverage Certificates Miss When 3D Gaussian Splatting Assets Are Edited*

> 评审身份：TMLR 审稿人（conformal prediction / 统计方向）。
> 本轮对象：`submission/final/main.pdf`（**12 页**，我核对页数 = 12）+ `main.tex`（738 行）。新增三组测量来自 `results_v80/`。
> 参照：上一轮 `review/FINAL_REVIEW.md`（针对 11 页版本）的 5 条 BLOCKER 与 6 条 MAJOR。
> 方法：`supplementary.zip` 解到 `_repro_tmp2/` 只读检查；用 numpy 从 `results_v70/*.json`、`results_v80/battery/*.json`、`results_v80/third_task.json`、`research/results_v58/selfcheck.json` **独立重算**（不采信论文自带的 verifier，只把它当线索）；跑了一遍作者的 `check/verify_tex_v3.py`；把 `results_v70` 与 `results_v80` 做了全字段 diff；把两张图重渲染后目视核查。**未修改论文/代码/数据**（仅在 `_repro_tmp2/` 解包与临时渲染）。
> 路径约定：`battery_{scene}.json` / `diag_{scene}.json` = `results_v70/`；`results_v80/battery/{scene}.json` = 新战役；`research/results_v*/` = zip 内的早期战役；`main.tex` L 号指行号。

---

## 1. 判定

**REJECT（borderline；"弱 reject"）。**

一句理由：**主干三组测量现在站得住（我一格一格重算过，全部对得上），但这次新并入的三组内容里，有一处摘要级的事实错误（第四任务族的 "rotation error" 不是 rotation error，且 "does not grow" 与自家数据相反），有两处新断言与自家表格/数据不符（granularity "within two points" 与 7 行不符、merge "same size" 与 27%/34% 不符），而能替它们撑住的对照数据就躺在新 artifact 里没被用上；再加上复现链路没跟上新内容（334 vs 360 vs 243 assertions、provenance 表 0 条 v80 行、README 不提 `results_v80`）——所以现有证据仍然不足以支撑现有措辞，但缺的是"删/改几段"，不是"再跑一个战役"。**

给作者的距离判断（重要）：这不是"结论不成立"。把 §3.5 末段删掉、§3.2 那两句改掉、reproducibility 三个数字对齐、把新 artifact 里已经算好的 merge/pup 的 task loss 补进正文，我会从 reject 改判 accept。反过来，如果只做文字修补而不碰第四任务族，我仍会给 reject，因为那是摘要里唯一一个"错的"陈述。

---

## 2. 上一轮 5 条 BLOCKER 的逐条状态

| # | 上轮 BLOCKER | 状态 | 一句话证据 |
|---|---|---|---|
| B1 | treehill 9.4 dB 的机理解释（残差剖面不像 offset；"no protocol repairs" 与 gain 臂冲突；四个工作点低于公开数字） | **部分解决** | 逐视角亮度比 + gain 臂都进来了且我逐项核对无误（0.96–1.77、6/18 views > 1.2、9.4→16.5 dB、label-free 9.3–12.3 dB）；但 gain 后仍 16.5 dB（= 6 dB 缺口）无解释，per-view error map/hist 仍缺 |
| B2 | "2.4× attenuation" 被当作普适结论 | **基本解决（正文）／部分（摘要）** | §3.3 现在四口径表齐全，16 格我全部重算一致，比率 0.42–1.01 / 1.04–1.17 / 0.86–1.57 精确；摘要已明说 symmetric/gain "does not"；残留：摘要/引言/§5 仍拿 2.4× 当标题数字（四场景中位数只有 0.84×） |
| B3 | pruning criterion 全文未定义，且作者已跑过的 criterion 对照把量级削 3–6× | **解决** | §2 "Edits" 现在写明 `ranks the primitives by their stored opacity and keeps the x% largest`（与 `torch.argsort(-opacities)[:k]` 一致）；Table 3 把 pup30 列进正文，8 个数我重算全部一致；Limitations 里"未测量 pruning criteria"已删 |
| B4 | 被评价的 certificate 未与 AURA/VSCP 区分 | **基本解决** | §2 明写 "The object certified here is therefore a *per-pixel marginal* coverage claim… AURA… VSCP… are different objects"；Related Work 加 "different in kind rather than in method"；残留：标题未收窄，§3.4 "Why" 仍把 marginal≠conditional 当新发现 |
| B5 | §3.7 整段用旧战役数字，且与 Table 1/2 矛盾 | **部分解决** | 拼接错误已修（现在明写 "0.864 at a 50% prune and 0.789 at 30%… treehill 0.853 and 0.768"，与 `research/results_v58/selfcheck.json` 完全一致）；provenance 已标注 `results_v58`；上轮点名的 4 处散文数字（2.4→3.6、−11.0→−11.1、App. B 0.971/0.876–0.927）全部改对。但仍在用 2 场景旧战役，而主战役有同一量的 4 场景版本，且两版差 1.8 点（见 §3.4） |

**逐条展开（只写需要证据的）：**

### B1 部分解决：机制这一半真修好了，保真度这一半没动

- 我重算 `diag_treehill.json` 的 `render_view_means/gt_view_means`：区间 **0.965–1.773**（论文写 0.96–1.77 ✔），>1.2 的视角 **6/18** ✔；其余三场景合起来 **0.916–1.193**（论文写 0.92–1.19 ✔）。`gain` 臂 9.415 → **16.502 dB** ✔，`norm_gt` **9.312**、`norm_both` **12.295**（论文写 9.3–12.3 ✔）。
- 这条修法是对的，而且比我上轮建议的更硬：**逐视角亮度项能解释掉 80% 的 MSE**（raw MSE 0.1145 → gain 0.0224，rms 0.338 → 0.150），残差长尾确实来自那 6 个 view。上轮"11% 饱和像素 vs brightness offset"的矛盾因此被消掉了。
- **没解决的部分**：(i) gain 拟合之后 rms 仍有 0.150（16.5 dB），离同资产公开量级仍差约 6 dB，而这是在 1/4 分辨率下（通常 PSNR 会**升**）；论文对这 6 dB 一个字没写。(ii) §2 仍写 "so these are deployable assets rather than undertrained ones"，但四个工作点里唯一能对标的是 bicycle（archive 自报 25.2 dB，这里 22.2 dB，差 3.0 dB），另外三个场景论文既没给参考数字，读者也无从核对。(iii) 上轮明确要的 per-view residual map / hist 仍然没有（现在只给了 per-view mean，这够解释 offset 型，不够解释为什么 gain 后还差 6 dB）。

### B5 部分解决：修的是"诚实"，没修的是"用哪套数"

- `results_v58/selfcheck.json` 我读过：flowers@50 = 0.8644、@30 = 0.7894；treehill@50 = 0.8534、@30 = 0.7684，over-prediction err_mean 分别是 0.0356 / 0.1106 / 0.0466 / 0.1316 → 论文 "3.6–13.2" ✔ 完全一致。
- 但同一个量在主战役里是：flowers@30 stale **0.7921**（§3.7 写 0.789）、treehill@30 stale **0.7501**（§3.7 写 0.768）。**同一量、同一场景、同一 edit strength，论文里有两个值，差 1.8 点**，而且用的是没有区间、只有一个 seed 的旧战役。按主战役重算，30% prune 的 over-prediction 是 **10.8–27.9 点**（0.900−0.6776/0.7921/0.6215/0.7501），不是 3.6–13.2。§3.7 的定性结论不变，但"用旧战役替代主战役"这件事会被直接问："你手上已经有四场景 400 splits 的版本，为什么给一个两场景的？"

---

## 3. 三组新结果的核查

### 3.1 表 3（criterion 对比）：**数字完全支持，"方向相反"成立；但支撑强度被四处可修问题削弱**

我从 `results_v80/battery/{bicycle,flowers}.json` 的 `coverage.pup30` 与 `coverage.prune30` 独立重算：

| scene | criterion | drop_mean（我算） | 区间（我算） | 论文 | q growth（我算） | 保留 primitives |
|---|---|---|---|---|---|---|
| bicycle | opacity | **−22.08** | [−25.18, −18.81] | −22.1 [−25.2, −18.8] ✔ | +104.7%（论文 +105%）✔ | 1,577,677 |
| bicycle | sensitivity (pup30) | **−11.61** | [−14.81, −8.20] | −11.6 [−14.8, −8.2] ✔ | +84.3%（论文 +84%）✔ | 1,577,677 |
| flowers | opacity | **−10.84** | [−11.90, −9.76] | −10.8 [−11.9, −9.8] ✔ | +52.8%（论文 +53%）✔ | 938,145 |
| flowers | sensitivity | **−18.94** | [−23.31, −14.66] | −18.9 [−23.3, −14.7] ✔ | +173.6%（论文 +174%）✔ | 938,145 |

**判定：表 3 的 8 个数字 + 4 个区间 + 4 个 q growth 全部正确；两场景的预算严格等量（保留数完全相同），不是"大约"。方向相反是真的**（bicycle 减半 1.90×，flowers 放大 1.75×），**且两场景内部区间不重叠**，所以在 split-to-split 意义上这个反转是被数据支持的。

但作为审稿人要提五件事（都不影响"反转"本身，影响"所以呢"）：

1. **q growth 那一列丢了区间，而 bicycle 上两臂区间重叠。** artifact 里 pup30 的 `q_growth` 区间是 **[45.1%, 137.9%]**，opacity 是 [93.9%, 117.1%]——**pup30 的区间包含 105%**，所以 bicycle 的 "+105% → +84%" 不可分辨。正文只对 flowers 用了 q growth 作证据（"174% instead of 53%"，[130,211] vs [48,58] 不重叠 ✔），所以这还不是陈述错误；但 Table 3 只给点估计，读者会把它读成"bicycle 的 q 也变好了"。把 artifact 里已有的区间补上，并在 bicycle 那行注明"不可分辨"，这个弱点就消失了。
2. **这是一个 label-free 与一个 label-using criterion 的对比，论文没点破。** `calib/sensitivity.py` + `experiments/make_pup_variant.py` 的 Fisher score 是对 **calibration views 的 photometric L1 loss 做反传**得到的（需要 GT；`n_views` 默认 4，PUP 原文用 6）。按论文 §3.3 自己的规矩（"For certification only a label-free one is [legitimate], and that excludes gain"），pup30 这一臂恰恰是 label-using 的。这不影响它作为压缩 baseline 的合法性，但 Table 3 的结论句 "a budget does not determine a damage level" 现在把"准则"和"是否看标签"两个轴混在一起了。一句话就能修：注明 sensitivity 需要 calibration labels、以及排名视图数 = 4。
   更微妙的一层：这个 score 的 GT 是 `normalize_exposure(...)` 之后的目标（每图缩放到 mean = 0.40，`calib/colmap_io.py:300`），也就是 §3.3 刚判为病态的 **one-sided 口径**；而评估用 captured GT。渲染没被归一化，所以梯度是在"逐视角亮度残差"上算的——这会把 view 之间的权重交给 offset 大的视角，从而改变排名（bicycle/flowers 的 offset 只有 0.92–1.19，影响比 treehill 小，但原理一样）。也就是说：**Table 3 里"更好"的那个臂，其准则是在论文自己否掉的口径下导出的**。这句必须写，否则就是同一份稿子里两套标准。
3. **Spearman 0.19 的唯一支撑文件是坏的。** `results_v80/pup_summary.json`（zip 内与工作区都是 819 B）**不是合法 JSON**：`json.load` 抛 `Invalid control character at line 30`，文件在第 30 行 `"ply": "/workspace/res/extra/flowers_` 处被截断，**bicycle 的整块不存在**。我手工从残文里读出 flowers 的 `spearman_fisher_vs_opacity = 0.1904`（论文 0.19 ✔），但一个评审者解包后跑 `json.load` 会直接 exception。而正文那句 "The two rankings are nearly unrelated on flowers (Spearman 0.19), **which is why** they disagree there" 是从一个相关系数反推机制——0.19 并不能推出"所以 flowers 上 sensitivity 更差"。
4. **最有力的免费证据被浪费了（两次）。** (a) pup30 的 PSNR **在两个场景上都比 opacity-prune 更好**（bicycle 18.07 vs 16.33、flowers 12.66 vs 12.10），而 coverage 一好一坏——这正是"图像指标单调、证书反转"的直接演示，Table 3 却没有 PSNR 列。(b) 新 artifact 里已经算了 pup30 的 task sweep：bicycle 任务掉 **−19.1**（coverage −11.6，33/36 格"任务更差"）、flowers 掉 **−25.8**（coverage −18.9，36/36 格）。

### 3.2 表 2 的 merge 行：**四个数全对，但可比性没写清，"same size" 是错的，而同段另一句与自家表直接矛盾**

我重算 `coverage.merge40` / `block.merge40` / `psnr.merge40`：

| scene | merge 保留 | drop（我算） | block（我算） | q（我算） | PSNR（我算） | 论文 |
|---|---|---|---|---|---|---|
| bicycle | 1,444,765 / 5,258,922 = **27.47%** | −35.45 [−37.29, −33.47] | −44.26 | +226.6% | 14.868 | −35.4 [−37.3,−33.5] / −44.3 / +227% / 14.9 ✔ |
| flowers | 1,067,911 / 3,127,149 = **34.15%** | −19.54 [−21.22, −17.64] | −18.61 | +118.4% | 13.374 | −19.5 [−21.2,−17.6] / −18.6 / +118% / 13.4 ✔ |

**数字 100% 对得上。问题全在措辞与对照设计：**

1. **"a prune of the same size (22.1 and 10.8)" 不成立**：merge 在 bicycle 只保留 **27.5%**（比 30% 剪枝**更狠**），在 flowers 保留 **34.1%**（比 30% 剪枝**更松**）。两个场景的方向相反，所以"same size"既不能统一解释，也不该无条件写。**而且这个错误是双向的**：flowers 上 merge 用更多 primitive 得到更差结果（结论更强），bicycle 上 merge 用更少 primitive 得到更差结果（结论也更合理）——只要把预算对齐写清楚，结论只会更硬。
   - 我做了论文没做的对齐：用四个剪枝点做 log-retention 插值，**同预算剪枝**在 bicycle ≈ **−25.1**、flowers ≈ **−9.0**，merge 分别是 −35.4 / −19.5，即 **同预算下 merge 多伤 10.3 / 10.5 点**。这句话可以直接替掉 "same size"，而且比现在的写法更有信息量。
2. **artifact 与论文对保留率的记录互相矛盾（未核实成因）**：`experiments/merge_variant.py` 的默认 `--target 0.4`，`tools/make_tables_v80.py` 的小标题写 "merge edit (**40%** of the primitives)"，变体名还叫 `merge40`——但实际产出是 27.5% / 34.1%。论文只报结果、不报参数，所以**读者按默认参数复现不出 27%/34%**。我不知道真实用的是哪个 target（工作区与 zip 都没有 merge 的运行摘要），标 **未核实**，但"文档写 40%、数据是 27/34、论文拿 27/34 去比 30%"这三件事同时存在，必须写清。
3. **同一段里 "for pruning they track within two points (−1.1 vs −1.0 at 70%, −25.3 vs −22.1 at 30%)" 自己打自己**：括号里的第二个例子就是 **3.2 点**间距。把 Table 2 的 16 个 pixel/block 成对行都算一遍，**7 行间距 > 2 点**：treehill@10% 是 **−44.9 vs −13.4（31.5 点，3.4×）**、stump@10% 17.2 点、treehill@30% 10.5 点、bicycle@10% 5.6 点、stump@30% 5.5 点、treehill@50% 4.0 点、bicycle@30% 3.2 点。也就是说"剪枝的 headline 不取决于 region 定义"这句话，只在 bicycle/flowers 成立，在 treehill/stump 显然不成立（上轮 M3 就是这条，这轮不但没修，还把措辞写得更绝对）。
4. **"A merge is also the one edit that separates the two granularities" 只有一半**：bicycle merge block −44.3 vs pixel −35.4（分开了 ✔），但 **flowers merge block −18.6 vs pixel −19.5（没分开，方向还反了）**。所以"merge 是唯一区分粒度的 edit"在自家表里就是 1/2，而 treehill 的剪枝（30%: −15.2 vs −4.7）比 merge 更能"区分粒度"。
5. Table 2 caption 写 "Each edit family on **two** released checkpoints…"，但表里有 **四个场景**，只有 merge 是两场景。caption 与表不符。

### 3.3 §3.5 第三任务族（two-view relative pose）：**"最不敏感"这个结论现在不成立，而且它的度量不是论文说的那个东西**

从 `results_v80/third_task.json` 重算（全部一致）：

| scene | variant | n_pairs | rot median | rot **mean** | dir median | success@5° |
|---|---|---|---|---|---|---|
| bicycle | clean | 24 | 0.397（论文 0.40 ✔） | 0.722 | 32.2 | 1.000（24/24） |
| bicycle | prune50 | 24 | 0.456 | 0.688 | 41.3 | 1.000 |
| bicycle | prune30 | 24 | 0.316（论文 0.32 ✔） | **1.709** | 49.6 | 0.917（22/24，论文 0.92 ✔） |
| bicycle | prune10 | 24 | 0.555 | **3.386** | 52.3 | 0.917 |
| flowers | clean | 21 | 0.659（论文 0.66 ✔） | 0.934 | 47.3 | 1.000 |
| flowers | prune30 | 21 | 0.902（论文 0.90 ✔） | **1.781** | 44.1 | 0.952（20/21，论文 0.95 ✔） |
| flowers | prune10 | 21 | 1.127 | 1.637 | 46.6 | 0.952 |

论文这 6 个数字一个没错。**但这一段里有三个实质问题 + 一条口径不一致，任何一个都够让这一族进不了正文：**

1. **它测的不是 rotation error。** `experiments/third_task.py` L305：
   ```python
   rot.append(abs(rotation_angle(p["R"]) - rotation_angle(gt_pose[(i, j)]["R"])))
   ```
   `rotation_angle(R)` 是 R 的**旋转角（一个标量）**，所以这个量是 **|θ̂ − θ_gt|，即"两个旋转的角大小之差"**，不是两个旋转之间的距离。轴被完全丢掉了：视野对之间的相对旋转若被估计成"同样的角度、完全不同的轴"，这个指标给 **0**。随后 L311 `success_5deg = mean(r < 5)` 用的还是同一个一维量。所以正文的 "the median rotation error stays below a degree" 与 "the fraction of view pairs **solved within five degrees**" 都不是代码算的东西。正确的量是 `angle(R_gtᵀ R̂)`（geodesic），而且**真值相对位姿本来就在 `cameras.json` 里**（渲染全部用它），根本不需要从 GT 图像再估一个参考——现在的做法是"用同一个估计器在 GT 图上再估一遍"当参考，docstring 自己说是 degradation 度量，正文没说。
2. **"does not grow at 30% pruning (0.32° and 0.90°)" 与数据相反。** flowers 是 **0.66 → 0.90（+37%）**；bicycle 是 0.40 → 0.32，**在一个"退化度"指标上变小本身就是可疑信号**（n=24，噪声主导）。更严重的是 **mean**：bicycle 0.72 → **1.71**（+137%），10% 时 **3.39**（+369%）。"不增长"只在 median 上、只在 30% 上成立。
3. **"It is the most tolerant of the three" 按论文自己的数字是错的。** 这一段自己接了一句 "That is **5–8 points**, against 22 points of coverage and 27 points of local matching"——而 registration 是 **3.9 点**（Table 6）。3.9 < 5–8，所以最 tolerant 的是 registration，不是这一族。如果 "three" 指的是三个 yardstick（coverage / local / registration），那这一族根本不在其中，是类别错误。两种读法都不成立。
4. 附带：**success@5° 是饱和指标**（clean = 1.000），分辨率 = 1/n_pairs = **4.2 / 4.8 点/对**，所以 "5–8 点" = **1–2 对 view pair 翻转**，没有任何区间。而论文在 registration 那里明确用了"天花板/headroom"论证，到这一族却不提——同一份稿子里两种标准。

**关于"平移方向误差 32–47° 被当作噪声主导、不作为指标"这个处理——可接受，但不完整：**

- 可接受的部分：理由写在正文里（"its median error is 32°–47° even on the fresh asset"），也如实说明了"所以只报 rotation 和 success"，这是诚实的 scope 声明，不是藏。
- 不完整的部分：(i) 32–47° 的基线误差意味着这个"two-view relative pose"族实际上只有**旋转**可用，族名过宽，应改称 "two-view relative **rotation**"；(ii) 这个被排除的量**对 edit 有响应**：bicycle 上 dir median 是 **32.2 → 41.3 → 49.6 → 52.3（单调）**，也就是说"因为基线噪声大所以不报"同时丢掉了一个会动的信号，属 outcome-dependent exclusion，至少应在脚注给数；(iii) 更干净的做法是用 `cameras.json` 的真值 baseline 方向 + geodesic 旋转误差重算一遍——这不需要新渲染，是一次纯后处理。

**§3.5 结论判定：**"（在 30% 剪枝下）这一族对 edit 最不敏感"——**当前不成立**。成立的是一个弱得多的陈述："在两场景、21–24 对 view pair、只测旋转角大小、只看 median 的情况下，看不出显著退化。" 而这个弱陈述支撑不了摘要里 "a fourth, two-view relative pose, holds its rotation error below a degree"。

### 3.4 新内容引出的新内部矛盾（这一节是本轮最该看的）

以下四条都是**新并入的内容与论文既有主张之间的冲突**，而且**反驳它们的证据就在新 artifact 里**：

1. **"the sign of the comparison is a property of the asset, not of the certificate"（L450–451）被新数据推翻。** 新 battery 里已经算了 pup30 / merge40 的 task sweep，我从没被论文引用的 `task_sweep[...][pup30|merge40]` 重算：

   | variant | scene | coverage drop | task drop（主操作点 s32_w24/tol2_peak0.6） | 任务损失 > coverage 损失的格数 |
   |---|---|---|---|---|
   | prune30 | bicycle | −22.1 | −27.3 | 18/36 |
   | prune30 | flowers | −10.8 | −11.1 | 12/36 |
   | **pup30** | bicycle | −11.6 | **−19.1** | **33/36** |
   | **pup30** | flowers | −18.9 | **−25.8** | **36/36** |
   | **merge40** | bicycle | −35.4 | **−71.7** | **36/36** |
   | **merge40** | flowers | −19.5 | **−53.5** | **36/36** |

   在 merge 下，**两个资产都是 36/36**，任务损失是 coverage 损失的 **2.0× / 2.7×**。这直接否掉"符号是资产的属性"——符号同样取决于 **edit 类型**（以及 criterion）。更关键的是：**这是全文"coverage 低估效用损失"最干净的一次演示**（同一份渲染、同一批 view、4 个数字对 4 个数字），比现在 §3.4 依赖的"18/36 vs 12/36"强得多，却没有进正文。
2. **摘要 "geometric pruning is the only edit that matters" 与 merge 矛盾**：merge 是最"matter"的几何编辑（−35.4 / −19.5 > 同预算剪枝），摘要里却连 merge 都没出现。
3. **§3.2 的 granularity 结论**（3.2 节第 3、4 点）与 Table 2 的 7 行冲突。
4. **§3.7 的 0.789 / 0.768 与 Table 1/2 隐含的 0.792 / 0.750 冲突**（§2，B5）。

---

## 4. 六个指定数字的独立核对

方法：numpy 直接读 JSON；区间用 artifact 里的 `drop_lo/hi`（split-to-split percentile，非我重抽）；registration 用 view-level paired bootstrap（20,000 次，percentile）。

| # | 论文数字 | 位置 | 我重算 | 结论 |
|---|---|---|---|---|
| 1 | bicycle merge 行：−35.4 [−37.3,−33.5]，block −44.3，q +227%，PSNR 14.9 | Table 2 | −35.447 [−37.289,−33.472]；block −44.262；+226.6%；14.868 | **四个全对** |
| 2 | bicycle 两准则：−22.1 [−25.2,−18.8] 与 −11.6 [−14.8,−8.2]（+105% / +84%） | Table 3 | −22.085 [−25.178,−18.811]；−11.606 [−14.811,−8.195]；+104.7% / +84.3% | **全对** |
| 3 | treehill 30% 行：0.250（−34.4） | Table 5 | `task_sweep.s32_w24.tol2_peak0.6`：clean 0.5944、prune30 0.24998 → **−34.44** | **对**（0.24998 舍入到 0.250 正常） |
| 4 | bicycle §3.5：0.40°（clean）与 0.92（success@5°） | §3.5 正文 | 0.39683 → 0.40；0.91667 = 22/24 → 0.92 | **对**（但见 §3.3：这两个量都不是论文描述的那个量） |
| 5 | （附加）Table 4 全部 16 格 PSNR/drop + 三条 relative 行 | Table 4 | 逐格一致：17.139/12.907/…；比率 0.842/1.006/0.422/0.845 → 0.42–1.01；1.046/1.172/1.060/1.035 → 1.04–1.17；1.086/1.567/0.990/0.862 → 0.86–1.57 | **全对** |
| 6 | （附加）36 格计数：18/36、12/36、0/36、36/36，且"30% 时 36/36 全部受损" | Table 5 / §3.4 | 逐格重算一致；四场景 n_neg 均 = 36/36 | **全对** |

**顺带核到的一致与不一致：**
- `results_v70` 与 `results_v80/battery` 全字段 diff：**144 个键有差异，全部是"v70 缺失、v80 新增"，没有一个已有数值被改动**。新战役是严格超集——这一点很好，说明三组新测量没有偷偷改旧数字。
- Table 6 registration 我重抽：bicycle −3.89 [−5.1,−2.8]、10% −31.13 [−33.9,−28.1]；flowers −2.62 [−4.3,−1.1]、−28.36 [−31.2,−25.4]。与论文差 ≤0.1（bootstrap seed 差异），**可复现**。
- 作者 verifier 我在解包目录实跑：**361 checks / 0 failures**，打印 **360 assertions**；同一次运行报告 "189 decimal literals, 176 covered (13 not)"。

---

## 5. 结构性风险：**是**，已经变成"什么都测了一点"

**先给数字：** 6 张表（Table 1–6）、2 张图、12 页；正文覆盖 **4 种 edit**（prune / SH-degree / SH-quant / voxel-merge）× **4 种 ground-truth 口径** × **3 个任务族**（+ 1 个新族）× **2 种 criterion** × **2 个粒度**（+ voxel）；但**每个主张的资产数从 4 掉到 2**：dose–response 4 场景、convention 4 场景、task sweep 4 场景；而 criterion 2、merge 2、registration 2、relative pose 2。**新增的三组测量全部落在同一个"中等难度"资产对（bicycle, flowers）上，而最极端的两个场景（stump −27.7、treehill 36/36）一个都没进新测量。**

**摘要与正文的错位是最硬的证据：** 摘要仍写 "Three findings"，其中 (a) 完全没有 merge，(b) 完全没有 criterion——而这两项正是本轮的"新增三组"里的两组；摘要里唯一提到的新组是**证据最弱的那一组**（第四任务族），并且提法是错的。也就是说：**摘要的强调顺序与证据强度顺序相反。**

**具体的删/并建议（按收益排序）：**

1. **删 §3.5 末段（第四任务族，L522–530）+ 摘要 L42–43 那一句。** 五个理由：2 场景、21–24 对、指标不是论文说的那个量、fresh 端 1.00 饱和、结论与 Table 6 矛盾。删掉后 §3.5 仍是完整的一节（两族对比 + factor-of-seven），而全文少掉唯一一处摘要级错误。
2. **把 Table 3（criterion）并进 Table 2**：每个资产加一行 `pup30`（cover drop / block / q / PSNR），正文留 2–3 句 + Spearman/重叠度一句话。省一张 float，且顺带把 pup30 的 PSNR 列放进来（免费证据）。
3. **把 merge 的 task 数补上，并让 merge 与 pup30 成为 §3.4 的主证据**（36/36、2.0–2.7×）。现在 §3.4 靠 18/36 vs 12/36 的"符号不稳"，反而比新数据弱。
4. **把 Table 4 的 `symmetric` / `gain` 两列移到 appendix**，正文只留两种 label-free 口径（captured / one-sided）+ 一句话说明另外两臂；§3.3 现在是全文第二长的小节，但结论只有一条。
5. **App. A（voxel 粒度）压成 3 句**，并把 §3.2 里那段"merge 区分粒度"改成"粒度效应随场景而异（treehill 剪枝 30%: −15.2 vs −4.7；bicycle merge: −35.4 vs −44.3；flowers merge: −19.5 vs −18.6）"。
6. 如果还想保留"第四族"这个词：把它降级成 appendix 一段，并改成 "two-view relative **rotation**"，用 geodesic + 真值位姿重算，报 CI。

---

## 6. 剩余 MAJOR（按"会不会直接导致拒稿"排序）

### MAJ-1（最高风险）§3.5 第四任务族：度量错 + 结论与数据相反 + 与 Table 6 矛盾 —— 而它进了摘要

- **位置**：main.tex L522–530；摘要 L42–43。
- **会怎么失分**：我会写——"论文称 'the median rotation error stays below a degree' 与 'the fraction of view pairs solved within five degrees'；`experiments/third_task.py:305` 算的是 `abs(rotation_angle(R_est) - rotation_angle(R_gt))`，即旋转角标量之差，轴被丢弃；`success_5deg`（L311）用的是同一个一维量。因此这一族没有测过旋转误差。此外 flowers 的 median 从 0.66° 涨到 0.90°（+37%），mean 从 0.93° 涨到 1.78°，与 'does not grow at 30% pruning' 相反；bicycle 的 mean 从 0.72° 涨到 1.71°（10% 时 3.39°）。且 'the most tolerant of the three' 与 Table 6 的 3.9 点冲突（5–8 > 3.9）。"
- **最小修法**：删掉这一段与摘要对应从句（`[离线可改]`）；若要保留，用 `cameras.json` 真值 + `angle(R_gtᵀR̂)` 重算、报 mean 与 cluster bootstrap CI、并把族名改成 relative rotation（`[需要新测量，但只是 CPU 后处理]`）。

### MAJ-2 新写的 granularity / merge 段与自家 Table 2 相反

- **位置**：L290–299（"more damage than a prune of the same size"、"block 44.3 vs 35.4"、"for pruning they track within two points"、"A merge is also the one edit that separates the two granularities"）。
- **会怎么失分**："你的表里有 7/16 对剪枝行的 pixel/block 间距 > 2 点（treehill@10% 31.5 点、stump@10% 17.2 点），括号里的 −25.3 vs −22.1 本身就是 3.2 点；flowers 的 merge 是 −18.6(block) vs −19.5(pixel)，也没'分开'。另外 merge 保留率是 27.5%/34.1%，不是 30%，'same size' 两个方向都不对。"
- **最小修法**：改成 (i) "merge 保留 27%/34%，与 30% 剪枝预算不严格相等；用 dose–response 插值到同预算，等量剪枝约 −25.1/−9.0，故 merge 多伤 10.3/10.5 点"；(ii) "pixel 与 block 在 bicycle/flowers 上一致（≤3.2 点），在 treehill/stump 上差 3.2–3.4×"；(iii) 删掉"merge 是唯一区分粒度的 edit"。`[离线可改]`

### MAJ-3 "符号是资产的属性" 与新的（已算好但未用的）数据相反，且最好的证据被漏掉

- **位置**：L445–454；§3.4 结尾；Table 5 的 "> coverage" 列。
- **会怎么失分**："merge 在两个资产上都是 36/36、任务损失是 coverage 的 2.0–2.7×；pup30 在 flowers 36/36、bicycle 33/36。所以符号取决于 edit（甚至 criterion），不只是资产。而这是你全文核心主张最干净的一次演示，却不在正文。"
- **最小修法**：Table 5 加 `merge`/`pup30` 两组行（或一张 4 行的表），§3.4 末段改写。`[离线可改]`（数据全在 `results_v80/battery/*.json` 的 `task_sweep`）

### MAJ-4 推断强度：fresh coverage 无区间却写 "validates the protocol and the implementation"；task 列无任何不确定性却断言"task 更敏感"

- **位置**：L207–210；Table 5（无区间）；§3.4 L433–436（"the task is the more sensitive gauge"，−27.3 vs −22.1）。
- **事实**：fresh coverage 的 split-to-split 区间是 bicycle ±4.4、flowers ±2.6、stump ±5.5、treehill ±6.7 点（`clean_lo/hi`），Table 1 只给点估计；在一个 ±4.4 点的区间里读 0.898/0.902 并写 "an off-by-one in the quantile index would show up here" 站不住——calibration 的像素分数 n ≈ 1.2×10⁷（见 m1），off-by-one 是 1/10⁷。task 一侧（−27.3 vs coverage −22.1，差 5.2 点）**完全没有区间**：`task_sweep` 只存均值，没有 per-view 命中率，所以"task 是更敏感的 gauge"目前无法从包内材料做配对检验；5.2 点与 coverage 区间半宽（3.2 点）同量级。
- **最小修法**：Table 1 加 fresh coverage 的 [2.5,97.5] 列；把 "validates the protocol and the implementation" 降为 "is consistent with nominal within the split-to-split interval"；Table 5 给 task 加 view-level bootstrap CI（per-view 命中率可以重抽）或明确写"未做检验"。`[离线可改]` + 少量 `[需要新测量]`

### MAJ-5 §3.7 仍在用旧战役，且与主表差 1.8 点

- **位置**：L559–573。
- **事实**：见 §2-B5。0.768 vs 0.750（treehill@30）、0.789 vs 0.792（flowers@30）；按主战役，30% 的 over-prediction 是 10.8–27.9 点而非 3.6–13.2。
- **最小修法**：用 `battery_*.json` 的 `stale_mean` 重算一句（四场景、400 splits），把 v58 那句降级为脚注或删掉。`[离线可改]`

### MAJ-6 复现链路没跟上新内容（三处 assertion 数字 + 三处缺口）

- **事实**（全部可复核）：
  - 论文 Reproducibility 写 "an automated check of **334** assertions"；`check/assertion_sources.json` 确实 334 行；但 verifier 实跑 **360**。差的 26 条正是本轮新增的 Table 3 / merge / third_task 断言。
  - `assertion_sources.json` 里 **0 行**指向 `results_v80`（provenance 表在 v80 检查之前就写盘了，`verify_tex_v3.py` L337–344 在 L346 之前）。也就是说"the check also writes a provenance table naming the artifact behind each value"对新内容不成立。
  - 补充材料 `README.md` 写 "**243** assertions"，且 **完全没提 `results_v80/`**，也没列 `make_pup_variant.py` / `merge_variant.py` / `third_task.py` 三条复现命令——三组新测量的入口在包里但不在文档里。
  - `results_v70/PROVENANCE.json` 仍写 "everything the paper reports about released assets comes from this campaign"，`tasks` 只列 2 个族，没有 pup30/merge40 的参数，也没有第三族。
  - `results_v80/pup_summary.json` 非法 JSON（见 §3.1-3）。
- **最小修法**：把 statement 改成实际数字；把 provenance 写盘移到所有 check 之后；README 加 `results_v80` 段与三条命令；`PROVENANCE.json` 加 v80 的变体定义（criterion、n_views=4、merge target、third_task 参数）。`[离线可改]`

---

## 7. 剩余 MINOR

| # | 位置 | 问题 | 修法 |
|---|---|---|---|
| m1 | §2 "How many independent scores" L164–170 | "the **2.6×10⁵** pixels of a split" 与实际不符：`node_run.split_stats` 把 **12 个 cal view 的全部像素**拼起来做 quantile（`cq(rc[ci]).reshape(-1)`），bicycle 是 **12×822×1236 = 1.22×10⁷**（flowers 1.14e7 / treehill 9.5e6 / stump 8.2e6）。相应的 binomial sd 应是 **~9×10⁻⁵** 而不是 6×10⁻⁴。结论方向不变（设计效应更大），但这是统计段落里的一个 47× 常数错误 | 改数字，或直接删掉 binomial 对照、只留 n_eff 77–508 |
| m2 | Figs 1–2 | 图仍被裁（上轮 m3/m4 只修了一半）：`fig_three.pdf` 的 y 轴标签在 mediabox 外（文本 bbox y=−1.5），成稿上 **"drop from fresh asset (points" 的右括号被切掉**、'0' 刻度也被切；`fig_dose.pdf` 面板 (b) 的 y 轴标签 "(%)" 顶端同样被切。**已修**：面板标题相撞（m3 前半）、(b) 纵轴单位（m3 后半）。**未修**：Fig 2 柱状图仍无任何误差棒（Table 6 有 CI，m4 后半） | `savefig(..., bbox_inches='tight')` 重导出两图；给 registration 柱加 CI（数据已有），`[离线可改]` |
| m3 | L290 | "Merging is the fourth edit and the one we **predicted rather than measured in an earlier draft**" —— 草稿史泄漏给评审看 | 改成 "which an earlier version of this work argued for without measuring"，或删 |
| m4 | L499–500 | "**The next two subsections** add two task families" —— 两个族都在本小节（§3.5）内，§3.6/§3.7 是 repair 与 circularity | 改 "This subsection adds two more task families" |
| m5 | Table 2 caption | "Each edit family on **two** released checkpoints" 与表内容（4 场景；只有 merge 是 2 个）不符 | 改成 "four released checkpoints (merge: two)" |
| m6 | §3.2 L287–288 | "SH degree reduction costs a little because truncating high-order coefficients **smooths the render**"：SH3→1 使 **3/4 场景 PSNR 上升**（flowers +1.16、stump +0.43、treehill +2.5、bicycle −0.07 dB）。smoothing 不解释 PSNR 系统性上升；而这其实是"图像指标变好、证书变差"的又一次免费证据 | 改成"图像指标反而变好，证书变差——与 §3.4 同一现象" |
| m7 | 摘要 L33–35 / 引言 L73–79 / §5 L637–642 | "attenuates … by up to 2.4×"、"the number moves by a factor of 2.4"：四场景中位数只有 **0.84×**（只有 stump 才是 2.37×），且三处都没写 "under the one-sided convention" | 加 "one-sided" 限定，或改成 "up to 2.4× on one scene, none on the others" |
| m8 | 摘要 L29–31 | "geometric pruning is **the only** edit that matters" 与 merge（更伤）矛盾 | 改 "edits that change geometry matter; appearance and precision edits do not" |
| m9 | §3.4 L456–461 | "**This is a threshold effect**, and the measurements above are its direct signature" —— 机制是断言：没测"离阈值多远"，也没有 conditional / Mondrian coverage；而 marginal ≠ conditional 是 CP 教科书结论（Vovk 2005；Lei et al. 2018），应有引用并降级 | 改 "is consistent with a threshold effect"，并引 Lei et al. 2018 |
| m10 | §3.6 L544–547 | "What the smallest sets do is **over-cover** (treehill 0.971)… conservative rather than invalid"：artifact 里 bicycle n=2 = **0.882**、stump n=2 = **0.882**，是 **under-cover 1.8 点**；bicycle full-set 0.876（−2.4 点）。under-coverage 恰恰是"修复"要修的东西 | 加区间（bicycle ±4.4 点内不可分辨），或改 "over- or under-covers by up to 7 points depending on scene and n" |
| m11 | App. A L697–703 | voxel 数字来自 `results_v60`，pixel 基准混用 `research/results_v52`（跨战役），正文未说明；"blocks sit between the two" 在 2/4 场景不成立 | 说明战役来源或统一 |
| m12 | Table 3 正文 L335–338 | Spearman 0.19 唯一源文件 `pup_summary.json` 损坏，且 0.19 不是任何 assertion 的 token；"which is why they disagree" 是从相关系数反推机制 | 修 JSON；把"so the rankings barely agree"改成描述而非因果 |
| m13 | 摘要/正文 | 摘要完全没有 merge 与 criterion（本轮两组新测量） | 二选一：摘要补一句 criterion + merge，或按 §5 删/并 |

---

## 8. 如果只改一处，改哪里

**删掉 §3.5 末段（main.tex L522–530）与摘要 L42–43 的对应从句：**

> `and a fourth, two-view relative pose, holds its rotation error below a degree: the choice of task moves the answer by a factor of seven.`

理由，按重要性：

1. **这是全文唯一一处"摘要级事实错误"。** 该段的 rotation 度量不是 rotation error（`third_task.py:305` 是 |θ̂−θ|），"does not grow" 对 flowers 是反的（0.66→0.90），"the most tolerant of the three" 与 Table 6 的 3.9 点冲突。删掉这三句，摘要里就不再有不成立的陈述——这对 TMLR 的 "accurate evidence" 是决定性的。
2. **它同时缓解 §5 的结构问题**：少了 1 个任务族、2 个资产、1 个饱和指标；§3.5 从"registration + pose 两族"回到"registration 一族"，正好对上 Table 6 与 Fig. 2 的三根柱（coverage / local / registration）。
3. **不需要新测量、不需要新数字、不与其他章节耦合**（§3.6 的 sequencing rule 与它无关，Fig. 2 只画三根柱）。工作量：删 9 行 tex + 改 1 句摘要。
4. 备选（如果作者坚持保留）：必须用 `cameras.json` 真值位姿 + `angle(R_gtᵀR̂)` 重算，报 mean 与 cluster-bootstrap CI，把 `success@5°` 重定义成 geodesic<5°，并把族名改成 relative **rotation**。**注意风险**：n=21–24 对、每对 4.2–4.8 点分辨率，加上 dir 误差 32–47° 的基线，重算后"最 tolerant"很可能翻掉（registration 3.9 点已经更 tolerant）。所以"删"比"修"更划算。

**次选（如果只想改一处措辞）**：MAJ-2 的两句（"same size" + "within two points"）。改动量 3 行，但它一次性消掉与自家 Table 2 的两处直接矛盾，而且顺手能把 merge 的结论写得比现在更强（同预算多伤 10 点）。

---

## 9. 未核实 / 我无法从现有材料判断的事项

1. **merge 的真实 target**：`merge_variant.py` 默认 0.4、`make_tables_v80.py` 写 "40% of the primitives"、变体名 `merge40`，但实际保留 27.5%/34.1%；工作区与 zip 内都**没有 merge 运行摘要**（`merge_variant.py` 会写 `merge_summary.json`，未随包发布）。所以"为什么两次都不到 40%、且两场景差 6.7 点"我无法判断，标 **未核实**。
2. **Fisher score 实际用了几个 view**：代码默认 `n_views=4`，`pup_summary.json` 记为 4，但该文件损坏/截断，bicycle 块缺失，无法确认两次 prune 用的是同一批视角。**未核实**。
3. **`2.6×10⁵` 的来源**：我按 `node_run.split_stats` + battery 的 W/H 推得 1.2×10⁷；若真实运行有子采样（supplement 版 `node_run.py` 里没有），则我的判断需修正。标 **未核实（但按包内代码是 47× 偏差）**。
4. **treehill 的 6 dB 缺口**（gain 后 16.5 dB）是否来自 SH 高阶项处理或参考实现差异——无 per-view residual map、无第二次渲染，**未核实**。
5. **archive 自报的 flowers/stump/treehill PSNR**：论文只给了 bicycle 的 25.2 dB，其余三个场景没有参考数字，我也没有 archive 的 eval 输出，故"系统性偏低"这句只对 bicycle 可核（22.2 vs 25.2，差 3.0 dB，且是 1/4 分辨率）。**未核实**。
6. 我没有复现渲染（无 GPU/archive），所有结论基于 artifact 与代码，不涉及端到端复现。

---

## 10. 附：本轮实际执行过的检查（便于作者复现我的质疑）

1. `python check/verify_tex_v3.py --root . --tex paper/main.tex`（解包目录）→ **361 checks, 0 failures**，打印 **360 assertions**；`check/assertion_sources.json` = **334 行，0 行含 `v80`**。
2. `results_v70/battery_*.json` × `results_v80/battery/*.json` 全字段 diff → 144 处差异，**全部为 v80 新增键，无既有值变动**。
3. 从 `results_v80/battery/*.json` 重算 Table 3 的 8 个数 + 4 个区间 + 4 个 q growth（§3.1）；重算 merge 行（§3.2）；重算 `task_sweep` 在 `pup30`/`merge40` 上的 36 格（§3.4）。
4. 从 `results_v70/battery_*.json` 重算 Table 1/2/5/6 与 36 格计数、per-view breadth ratio、n_eff。
5. 从 `results_v80/third_task.json` 重算 §3.5 的 6 个数，并读 `experiments/third_task.py:299–311` 确认度量定义。
6. `pdftotext`/PyMuPDF 核 PDF：12 页；两图重渲染后目视核查裁切。
7. `research/results_v58/selfcheck.json`、`research/results_v22/cert_v3.json`（repair curve）、`results_v70/PROVENANCE.json`、`README.md` 逐项核对。
