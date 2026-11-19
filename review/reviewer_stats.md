# TMLR 审稿意见（统计 / conformal prediction 方向）

**审稿对象**：`submission/main.tex`（8 页，TMLR 投稿版）+ `submission/main.pdf`
**交叉参考**：`PAPER_certificate_invalid.md`（仅作历史对照，判定一律以 main.tex 为准）
**审稿人立场**：严格否决制。只认可"claim ↔ evidence 严格对齐且能复算"的内容。
**只读核对**：`submission/`、`research/code/`、`research/results_*/` 未做任何修改；所有重算只读 JSON。

---

## 0. 一句话结论

现在的稿子我会写 **reject**。原因不是"实验不够多"，而是**三处 claim 与 evidence 的对应关系是错的**，而且三处都可以被审稿人在 10 分钟内用作者自己的脚本 + 自己的 JSON 复算出来：

1. 摘要/表 3 的核心数字 `4.6 points` 与本文表 1 对同一资产同一编辑的 `10.9 points` 冲突——headline `1.9–12.1×` 是把 **patch 级下游损失** 除以 **3D-voxel 粒度** 的证书损失得到的，按匹配粒度（pixel）重算是 **1.0–2.5×**，其中两个场景（stump 1.02×、bicycle 1.16×）根本不存在"低估"；
2. §2 写 "Coverage is a **view-level** quantity: the effective sample size is the number of views (16–25), not the number of pixels"，而三份主脚本全部是 `reshape(-1)` 后按**像素**取 conformal 分位数与覆盖率——证书所认证的事件与实现完全不是一个东西；
3. "q grows 26–71%" 的分子分母用了**两个不同估计量**（edited q 是 400 次划分的均值，clean q 是第 0 次划分的单个值）。同一文件里被作者宣布为"完全免费"的 8-bit SH 量化，其 width_growth 读数是 **+2.2% / −18.1% / +12.1% / +0.4%**——估计量噪声地板 ±18%，与声称效应的下限 26% 同量级。

一句话给作者：**把"证书"到底认证什么（随机像素 / 随机视角 / 随机区域）定死，然后所有表都按这一个定义重算并标注粒度；在此之前，"1.9–12.1×"不能作为主结论。**

---

## 1. TMLR 两条接收标准下的逐条判定

TMLR 的判定标准：(A) claims 被 **accurate and convincing** 的 evidence 支持；(B) 工作对领域有独立价值且可复现声明成立。下表对 6 条核心 claim 逐条判。

| # | Claim（main.tex 原文位置） | (A) 证据准确且可信 | (B) 价值独立成立 | 一句话理由 |
|---|---|---|---|---|
| 1 | **Fresh 证书有效**（L65-68, L87-90, L176-179；值 0.894–0.901 vs nominal 0.900） | **Partially** | Yes | 数字全部复算一致（0.8938/0.8987/0.8997/0.9006），但"验证了实现"近乎同义反复：q 是像素经验分位数，clean 在同一像素池上必然 ≈ 1−α；且作者自己的自训场景 garden 是 **0.9556，CI [0.952, 0.959] 排除 0.9**（偏离 nominal 5.6pp），全文未提 |
| 2 | **几何编辑使证书失效**（L29-31, L91-94, Table 1；−10.9…−18.6） | **Partially** | Yes | 数值准确、可复算、符号一致；(A) 之所以是 Partially：区间不是 CI（§2 综述见 M1），且同一编辑在 region 粒度只有 −2.6…−6.1（作者自己在 L395-396 承认"region definition must be reported alongside any absolute number"，但摘要没做） |
| 3 | **外观 / 精度编辑不失效**（L31-32, L95-98, Table 2） | **Partially** | Partially | quant8 的 coverage 变化确是 1e-6~1e-7pp（四舍五入 0.00，成立）；但 (i) 同一组 quant8 的 q 变化是 −18.1%…+12.1%，与 L326-328 "leaves both the coverage and the interval width unchanged" **直接矛盾**；(ii) flowers 的 −2.0 与 0.00 **没有任何 artifact**（`results_v53/edit_families.json` 是 0 字节，作者自述 crit_a 因 OOM 丢失）；(iii) treehill 的 SH 3→1 是 coverage *上升* 0.20pp，被写成 "costs 0.2–2.0 points" |
| 4 | **证书低估下游损失 1.9–12.1×**（L32-34, L99-103, L260-262, Table 3, Fig. 9） | **No** | **No**（当前形态） | 分母换了粒度：Table 3 的 "Certificate drop" 列 = `voxel_prune30_drop_mean`（2.61/6.14/2.61/6.14），而 Table 1 同一编辑是 10.90/12.82/18.57/11.69。匹配粒度下 ratio = **1.02/1.16/1.54/2.47×**。Fig. 9 图例写了 "(3D voxel)"，表头与摘要没写 → 审稿人会直接判为粒度挑选 |
| 5 | **2–4 视角可修复**（L36-37, L104-106, Table 4a, L310-316） | **No** | Partially | 表 4(a) 删掉了 n=all 列：**flowers 0.892、bicycle 0.876（低于 nominal）**；而且四个场景都是 n=2 的覆盖率 **高于** n=all → 所谓"修复"是 2-view 分位数的**保守过覆盖**，不是回到名义水平。且曲线来自**唯一一个** cal 子集（`cal[:n]`），无子集分布、无区间 |
| 6 | **自检循环无法检测失效**（L107-110, L333-341） | **Partially** | **No**（应改写） | 被反驳的检验是恒等式：`pred = (cal 残差 ≤ 由 cal 残差算出的 q).mean() ≡ 1−α`，对**任何**模型都成立，"检测不到"不是实证发现而是同义反复。更糟：可用的 label-free 检测量恰恰是作者自己在 Table 4(a)/Fig. 2 里报的 **q drift（+26–71%）**——§3.6 与 §3.5(a) 互相矛盾 |

**综合**：6 条里 (A) 判 No 的 2 条（#4、#5），Partially 的 4 条。(B) 只有 #1、#2 独立成立。按 TMLR 的"claim 必须被准确证据支持"，**当前版本不达线**。

---

## 2. 分级意见

标注约定：`[离线可改]` = 只改文字/表格/已有 JSON 重算即可；`[需要新测量]` = 需要 GPU 渲染。

### 2.1 BLOCKER（不改会被拒）

---

**B1. 摘要的核心比率换了粒度：`4.6 points` vs 表 1 的 `10.9 points`**

- **原文**：L32-34 "an asset whose coverage drops by **4.6 points** loses 16.8 points of patch re-localisation accuracy, and this gap ranges from 1.9× to 12.1× across four scenes"；L236-241 Table 3 列名 "Certificate drop"；L255-256 Fig. 9 caption "The certificate shrinks by 2.6–6.1 points"；L260-262。
- **事实**：`research/results_v60/vt_*.json` 的 `voxel_prune30_drop_mean` = flowers 4.61 / treehill 2.61 / bicycle 6.14 / stump 6.14；`make_figures.py::fig_task_vs_cert()` 用的正是这个字段，图例写 "certificate coverage (3D voxel)"。而 Table 1（`results_v52/many_splits.json`）对同一 edit 是 10.90 / 12.82 / 18.57 / 11.69。**同一篇论文里"证书缩水"有两个值（10.9–18.6 与 2.6–6.1），相差 1.9–4.9×，表 3 与摘要用了小的那个，且没标粒度。**
- **审稿人一句话**："The abstract reports a 4.6-point coverage loss for flowers@30% pruning; Table 1 of the same paper reports 10.9 for that exact asset and edit. The 1.9–12.1× headline is obtained by dividing a patch-level task loss by a voxel-level certificate loss. Using the pixel-level certificate the ratio is 1.0–2.5×, i.e. on two of four scenes the certificate does not understate the damage at all."（匹配粒度复算：stump 1.02×、bicycle 1.16×、flowers 1.54×、treehill 2.47×）
- **最小修法**：`[离线可改]` (i) Table 3 列名改成 "Certificate drop (0.25-unit 3D voxel) [pixel-level in Table 1]"；(ii) 摘要同时给两个数（"4.6 points at voxel granularity / 10.9 at pixel granularity"），或只给匹配粒度；(iii) 正文补一列 pixel-level ratio，明确"task 是 patch 级，所以 region 粒度是匹配的"这一**论证**（现在只有图例暗示，正文没说）；(iv) 遵守你自己在 L395-396 定的规矩。**注意：这一改会把"12.1×"降到"2.5×"，摘要第二段与贡献 2 必须重写，但这比被审稿人抓出来好。**

---

**B2. §2 的 "view-level" 定义与实现相反（证书认证的事件不对）**

- **原文**：L132-137 "Coverage is a \emph{view-level} quantity: the effective sample size is the number of views (16–25), not the number of pixels. A single split therefore has large variance."；L23-25 摘要 "with probability 1−α, the rendering error on a **held-out view** stays below a threshold q"。
- **事实**：`many_splits.py` L88-90、`edit_families.py`、`voxel_and_task.py` 全部是 `r_clean[Ci].reshape(-1)` → `cq(...)` → `(r[Vi].reshape(-1) <= q).mean()`；`certificate_audit.py` L222-225 同样（`per_view_cov` 只喂给 bootstrap CI，headline `cov_pix` 是像素均值）。**q 是像素展平的 conformal 分位数，coverage 是像素比例。** 像素在视角内强相关，因此"随机像素的边际覆盖 ≥ 1−α"**不蕴含**摘要里的 per-view 陈述；而如果真按 per-view 取 n=8–12 个分数，α=0.1 时 k=⌈(n+1)0.9⌉ 在 n=10 就等于 n → q 取校准集**最大值**，coverage≈1.0，主表全部数字要变。
- **审稿人一句话**："Your protocol section states the effective sample size is the number of views, but `many_splits.py` flattens all pixels before taking the quantile and before measuring coverage. The certified event in the abstract (per-view error ≤ q) is therefore not the event you compute. Which one is the contribution? And if it is per-view, why is the quantile taken over millions of pixels?"
- **最小修法**：`[离线可改]` 文字层：把 L132-137 改成"我们认证的是 **随机像素** 的边际覆盖（pixel-level marginal coverage），并额外报告 per-view 覆盖；因此有效样本量是像素而非视角——这解释了为什么区间是本稿报告的样子"；摘要同步改。`[需要新测量]` 若要保留 view-level：把主表换成 per-view 分数（每视角平均残差 / 每视角 95 分位），用已有的 `certificate_audit.py::bootstrap_ci(per_view_cov)` 出区间。**这一步是最高风险项**（见 §3 排序 #3）。

---

**B3. "26–71% wider interval" 的估计量不匹配，噪声地板 ±18%**

- **原文**：L36-37 摘要 "at the cost of a 26–71% wider interval"；L305-306 Fig. 2 caption "the conformal half-width grows 26–71% after a 30% prune"；L312-316；Table 4(a) 的 "q growth" 列（L284-289）。
- **事实**：`edit_families.py` 里 `q0` 是 **i==0 那一次划分**的 clean q（`if i == 0: q0 = q`），而 `{name}_q` 是 **400 次划分的均值**，`width_growth = 100*(mean(qs)/q0 − 1)`。同一份 `results_v55/widths.json` 给出被认定为"完全免费"（coverage 变化 1e-6~1e-7pp）的 8-bit SH 量化的 width_growth：**+2.2% / −18.1% / +12.1% / +0.4%**。一个 no-op 编辑在正确估计量下必须读 0%，读数 ±18% 就是估计量噪声。更硬的反证：treehill 的 SH 3→1（只会增大残差）报告 q **下降 17.1%**（0.2357→0.1954），物理上不可能。
- **审稿人一句话**："Under the estimator that produces your 26–71% claim, your own no-op edit (8-bit SH quantisation) shows ±18% spurious growth, and SH truncation shows a 17% *decrease* in the quantile. The width effect is not established until the quantiles are estimated consistently."
- **最小修法**：`[离线可改 / 需要新测量]` 把 clean q 换成**同一批 400 个划分**的 clean q 均值（或直接报 paired ratio 的分布与 2.5/97.5 分位）。改动量极小（`edit_families.py` 里 q0 改成 `mean(q_clean_over_splits)`），但需要重跑该脚本（GPU 1–2 h；若先缓存残差图则纯离线，见 §3 #1）。**同时给出 no-op 噪声地板**（这一句反而会加分：说明作者知道自己的分辨率极限）。
- **最坏情况**：26% 掉进噪声 → Fig. 2 删掉或改成 paired ratio + 区间；规则 (a) 的"代价 26–71%"改写为实测区间。

---

**B4. Table 4(a) 删掉了唯一与结论相反的列（n = all），"2–4 视角可修复"不成立**

- **原文**：L278-289（表只到 n=8）+ L310-316 "2--4 held-out views restore coverage to near nominal. Re-certification is therefore cheap in \emph{data}."
- **事实**：`results_v22/cert_v3.json` 的 `repair_curve` 有第 5 个点（n=all），main.tex 没印：**flowers 0.8915、treehill 0.9272、bicycle 0.8764、stump 0.9023**（nominal 0.900）——两个场景在**用满**校准视角时低于 nominal。而且四个场景**全部**是 coverage(n=2) > coverage(n=all)（0.917>0.892、0.971>0.927、0.882>0.876、0.882=0.882）：这表明 n=2–4 的"恢复"是**小样本分位数的保守过覆盖**，不是修好了。曲线还只是**一个** cal 子集（`cal[:n]`），没有子集分布。
- **审稿人一句话**："The repair curve is non-monotone in the wrong direction: coverage at n=2 exceeds coverage at n=all on every scene, and the omitted n=all entry shows flowers 0.892 and bicycle 0.876, i.e. full re-certification does not reach the nominal level. 'Two to four views suffice' is an artifact of conservative over-coverage from a two-view quantile."
- **最小修法**：`[离线可改]` 把 n=all 列放回去，正文改写为"2–4 个视角即可重新签发，但会**过度保守 3–7pp**；用满校准集才收敛到 0.876–0.927"，规则 (a) 从 "restore coverage" 改为 "restore validity at the price of conservativeness"。`[需要新测量]` 若要有区间：每个 n 抽 ≥100 个 cal 子集（依赖 §3 #1 的残差缓存，纯离线）。

---

### 2.2 MAJOR

**M1. 400 次划分不是独立重复，区间不是 CI，"all intervals exclude zero" 不是证据**
原文：L28 "paired confidence intervals"、L30 "all intervals exclude zero"、L92-93（claims 表）、L132-137、L399-402。
事实：`many_splits.py` 对**同一批 16–25 个视角**做 400 次重新对半分；cal 集高度重叠 → 400 个数字强相关；报告的 2.5/97.5 分位只是**划分构成**的散布，不含"16–25 个视角来自一次更大采集"这一层抽样不确定性。表 1 的 fresh 覆盖率区间宽度 7.1–15.7pp 全部跨过 −α 之外的合理范围，恰恰说明视角层的随机性很大，而这层随机性在选择 cal/dep 时被**固定**掉了。
审稿人："The 400 splits are re-partitions of one fixed view pool; their 2.5/97.5 percentiles are not confidence intervals, and 'all intervals exclude zero' therefore says nothing about whether the drop generalises to unseen views."
最小修法：`[离线可改]` 全文把 "confidence interval" 改成 "split-to-split range"；删掉"all intervals exclude zero"作为推断依据；`[离线可改]` 用 `certificate_audit.py` 已有的 `per_view_cov` + `bootstrap_ci` 给主表补一列 **view-level bootstrap 区间**（v61/v62 的 `ci_lo/ci_hi` 就是它，说明代码已在）。

**M2. 规则 (b)「改用 sensitivity 剪枝」用了 deployment 视角的 GT（信息泄漏）**
原文：L318-324 + Table 4(b)（sensitivity cost 2.0–9.3 vs opacity 11.7–18.6，缩减 70–83%）。
事实：`criteria_stats.py` L94 `sens = sensitivity_scores(base, c2w, K, gt, views[:8], ...)`，其中 `views = sorted(set(cal_idx + dep_idx))` —— **梯度打分用的是 cal∪dep 的前 8 个视角**，而 400 次划分里每个视角有一半概率进入 deployment。也就是说"知道哪些视角会被拿来考"的剪枝准则被拿去和"不知道"的不透明度准则比。另外 flowers 的 sens 值（9.3 [6.8,11.6]）**没有 artifact**（`results_v54/crit_a.json` 不存在，作者自述 OOM 丢失）。
审稿人："Your sensitivity criterion is computed by back-propagating the photometric loss on views that include the deployment views; the opacity baseline has no such access. The 70–83% reduction may be an artifact of target-view information. And the flowers row has no stored artefact."
最小修法：`[需要新测量]`（2–4 h GPU）用**训练视角**或与 deployment 完全不相交的第三个视角集重算 sensitivity；`[离线可改]` 至少先把这一点写进 limitation，并把 flowers 行的 artifact 补出来或删掉该行。

**M3. 下游任务不是 paired，且 10 patch/视角、无区间、单任务单阈值**
原文：L230-232 Table 3 caption、L246-250、L260-262。
事实：`voxel_and_task.py` L145-155：`for name in ("clean","prune50","prune30")` 循环里，`sample_patches(g, patch, n_patches, rng)` **共用同一个 rng 且状态持续前进** → 三个 variant 采样到**不同随机位置的 patch**。因此 hit rate 的差值里混进了 patch 选择的噪声，不是 paired 比较。每视角只取 10 个 patch（treehill 共 180 个），hit rate 无任何区间（treehill p=0.589 时二项 SE≈3.7pp，且视角内相关使其更大）。整条 headline 只基于 **1 个任务、1 组阈值**（patch 32 / tol 2 / peak ≥ 0.6 / ±24px 窗），没有任何敏感性分析——而 treehill 的 31.7pp（ratio 的上限 12.1× 的唯一来源）恰好最依赖 `peak ≥ 0.6` 这个硬阈值。
审稿人："Patch positions are resampled independently for the clean and pruned renders (the RNG is shared and advances between variants), so the reported task drops are not paired; with 10 patches per view and no interval, and with the largest drop depending on a hand-set peak threshold of 0.6, the numerator of your headline ratio is unquantified."
最小修法：`[需要新测量]`（GPU 0.5–1 h，若缓存渲染图可离线）固定 patch 集合 → paired；每场景给 per-view bootstrap 区间；至少扫 `peak ∈ {0.5,0.6,0.7}` × `tol ∈ {1,2,3}`。

**M4. 「自检循环」是恒等式，不是发现；且与规则 (a) 矛盾**
原文：L107-110、L333-341（"The check returns 0.900 by construction … A stale certificate is therefore \emph{not detectable} from the calibration set alone"）。
事实：`selfcheck_stats.py` 的 `pred = (r_clean[Ci] <= q).mean()`，q 就是这批残差的分位数 → pred ≡ 1−α，**对任何模型恒成立**，所以"检测不到"是数学恒等式。审稿人真正会设计的 check 是"**q 有没有漂移**"——而这正是 Table 4(a)/Fig. 2 报告的 +26–71%，即 §3.6 说"不可检测"的东西在 §3.5 里被当作事实报告了。两节互相拆台。另外 `selfcheck.json` 只有 **2 个场景**，而且 prune50 的误差区间 **含 0**（flowers [−0.33,+7.94]、treehill [−2.06,+13.12]），正文却写 "over-predicts 3.6–13.2 points" 而不提显著性。
审稿人："The self-check you refute is an identity, and the informative label-free statistic — quantile drift on the original calibration views — is exactly what Table 4(a) reports as 26–71%. Sections 3.5 and 3.6 contradict each other."
最小修法：`[离线可改]` 把 §3.6 从"负结果"改成"为什么覆盖率自检不可行 + 给出可行的标签无关检测量（q drift）"，并把它与规则 (a) 合并；删掉"not detectable from the calibration set alone"这句全称判断。

**M5. 「fresh 0.894–0.901 验证了实现」近似同义反复，且 garden 0.956 未讨论**
原文：L176-179、L65-68。
事实：q 是像素经验分位数、clean 覆盖率在同一像素池上求均值 → 只要分位数索引没写错，读数必然≈1−α，这条"验证"对实现错误（除 off-by-one）不敏感。而作者自己的自训场景 **garden fresh = 0.9556、CI [0.9517,0.9595]**（avoids nominal 5.6pp，`results_v62/garden_base.json`，且 `cal_med 0.0444 < dep_med 0.0400`，说明该场景的划分存在难度偏置），5 个自训场景中 room 0.9198、kitchen 0.9230 也都偏离 2pp 以上——这些恰好**削弱**"fresh 一定有效"的论断，但全文一句没提。
审稿人："A pixel-level empirical quantile attains nominal coverage on its own distribution almost by construction, so this is not a validation. Meanwhile your own garden checkpoint certifies 0.956 with a CI excluding 0.9, an over-coverage of 5.6 points, and this is never discussed."
最小修法：`[离线可改]` 把"验证实现"降级为"确认没有索引错误"，把真正能验证实现的证据换成 **附录 trap 2**（训练视角泄漏会把 fresh 拉到 0.822/0.823/0.894）——那才是会因 off-by-one/泄漏而暴露的敏感实验；同时用一句解释 garden 的过覆盖。

**M6. "nine scenes / 400 splits per scene" 与事实不符；九个场景里有五个是 11–16 dB 的欠训练模型**
原文：L27-28 摘要 "Across nine scenes, with 400 random calibration/deployment splits per scene"；L121-122 "6000 steps (107k–300k primitives, 11–16 dB)"；L184-187。
事实：400 划分只对 4 个 released checkpoint 做了；5 个自训场景是**单次划分**（表 1 caption 承认），且 PSNR 11–16 dB — 这个质量的 3DGS 资产在部署语境下不可用，而附录自己说效应"只出现在 fully optimised 资产上"。于是"nine scenes"实际是"4 个可部署资产 + 5 个反例池"。
审稿人："The abstract claims 400 splits across nine scenes; only four scenes have 400 splits. The other five are 11–16 dB models that, by your own Appendix A, are in the regime where the effect does not appear — they inflate the scene count without testing the claim."
最小修法：`[离线可改]` 摘要改成 "four released checkpoints (400 splits each) plus five self-trained models (single split, reported separately as a scope control)"；把"nine scenes"的措辞从摘要挪到 §3.1。

**M7. Reproducibility statement 对这份稿子不成立**
原文：L353-357、L472-474（"104 assertions covering the reported values"、"A single command re-runs the main table"）。
事实：`research/code/scripts/verify_paper_numbers.py` 的 `PAPER = PAPER_certificate_invalid.md`（不是 main.tex），且它校验的是 **v22/v23/v28 的旧数字**（prune30 stale 0.785/−11.4pp、width growth 26–83%、abstract 11.4–20.6pp、criterion −11.6/−10.0 等），这些数字 main.tex 已经不报了。我实跑：`104 numeric checks, 0 failures` —— 但它证明的是**另一篇稿子**。main.tex 里至少 6 组数字没有 artifact：flowers 的 SH −2.0、quant8 0.00、sensitivity 9.3 [6.8,11.6]、ΔSH=3.4–4.1e-4、half-resolution 序列（−12.8/−12.2/−20.3/−13.7）、附录 trap 的 0.944–0.988/0.45–0.91。
审稿人："I ran `verify_paper_numbers.py`: it targets the markdown draft and the v22/v23/v28 artefacts, not main.tex. At least six numbers in the submitted PDF have no stored artefact, and one of them (the flowers SH row) carries an unexplained asterisk."
最小修法：`[离线可改]` 要么把校验脚本指向 main.tex 并把 v52–v62 全部纳入（工作量 1–2 h，纯离线），要么把 statement 改成可辩护的弱表述（"the main table is regenerated by `many_splits.py`; values from run logs are marked"）。**TMLR 会把 reproducibility statement 当正式声明读，这一条不改就是送分给审稿人。**

**M8. 4 个下游任务参数没有任何敏感性分析**
原文：L230-232、L249-250（"The matcher is deliberately simple so that the number measures the render, not the matcher"）。
事实：patch=32 / tol=2 / peak≥0.6 / ±24px 四个常数直接决定 hit rate 的**绝对水平**，进而决定 ratio 的分子；没有 sweep、没有 chance-level 分析。作者声称 matcher 简单所以"measure the render"，但 hit rate 是 4 个阈值的函数，简单 ≠ 无偏。
审稿人："Four hand-set constants define the numerator of your headline ratio, and none is varied. A reviewer cannot distinguish 'the render degrades' from 'the peak correlation crossed 0.6'."
最小修法：`[需要新测量]` 见 M3 同一批 sweep（可共用一次运行）。

**M9. Region 粒度的量级说错（"3–4×" 实为 1.9–4.9×），且主表与附录的粒度关系没写**
原文：L394-397、L466-470。
事实：pixel/voxel 的 prune30 损失比 = flowers 2.37、treehill 4.92、bicycle 3.02、stump 1.90 → **1.9–4.9×**。附录还说"Moving regions from 64×64 image blocks to voxels reduces 3–4×"，但 main.tex 从未给出 block 级的数字，读者无法验证这一句。`certificate_audit.py` 的 `q_blk/cov_blk` 说明这个数据是存在的（只是没进稿）。
审稿人："The appendix says the effect shrinks 3–4× under a region definition; recomputing from your own files gives 1.9–4.9×, and the numerator (64×64 block-level numbers) is never reported."
最小修法：`[离线可改]`（数据不足则 `[需要新测量]`）把 "3–4×" 改成实测区间，并把 block 级数字补成表 1 的一列（或删掉该句）。

---

### 2.3 MINOR

- **m1. 三张表用了三种符号约定**：Table 1/2 用负号表示损伤（L159-162, L200-202），Table 4(b) 用正号表示损伤（L294-297："+10.9 [9.3,12.6]"），摘要混用（L29 "lowers … by 10.9–18.6" vs L105 "q grows 26–71%"）。→ `[离线可改]` 统一成"损伤为正、并写明 sign convention"。
- **m2. Table 2 的 `−2.0*` 星号全文无脚注**（L201）。→ `[离线可改]` 要么解释（"from run log, no artefact"），要么补 artifact。
- **m3. 5 个自训行的 artifact 不可识别**：garden 用 `garden_base.json`、room 用 `room_small.json`（其余 `_base`），且 garden 无 `_small`、room 无 `_base` → 读者无法判断每行是哪个模型（原始模型 / 剪到 200k 未微调 / 剪后微调）。→ `[离线可改]` 表 1 加一列 "variant"，或按 variant 分表。
- **m4. Half-resolution "within 1.4 points" 是对旧数字算的**（L463-464）。用 main.tex 表 1 的值（10.9/12.8/18.6/11.7）复算最大偏差是 **1.7pp**（最优配对）/ **2.0pp**（按原文顺序 flowers/treehill/bicycle/stump）；"1.4" 只在对比**已弃用**的 v22 单划分值（11.4/11.9/20.6/12.5）时成立。且该实验**无 artifact**（只在旧 md 里有表）。→ `[离线可改]` 改成 "within 2 points of Table 1"，并补 artifact 或删句。
- **m5. α sweep 的第三点不满足"fresh close to nominal"**（L459-461）：α=0.20 时 bicycle fresh = 0.740，比 nominal 0.80 低 6.0pp。→ `[离线可改]` 如实报告，或说明这是单划分估计。
- **m6. 符号笔误**（L184-186："the five self-trained models drop only $6.7$ to $-0.7$ points"），表 1 实为 −6.7 到 **+0.7**。→ `[离线可改]`。
- **m7. Table 1 的 50% 列无区间、30% 列有**，caption 未解释（L152-162）。→ `[离线可改]` 补上（JSON 里有 `drop_lo/hi`）。
- **m8. "q" 被称为 "conformal half-width"**（L305-306, L312）：split-conformal 的 q 是**上分位数**（单边上界），不是半宽。→ `[离线可改]` 统一术语为 "quantile / upper bound"。
- **m9. "no post-hoc correction avoids both"（L316）只测了一种修正**（重新标定）。→ `[离线可改]` 改成"我们测过的唯一修正方式"。
- **m10. "removes the split-to-split jitter"（L66）用词过强**：400 次划分只是把抖动平均掉并报告其分布，没有"移除"。→ `[离线可改]`。

### 2.4 NIT

- **n1.** Table 1 表头 "Fresh coverage [95%]"（L157）与 caption 的 "2.5/97.5 percentiles" 语义不一致，读者会读成 95% CI。→ 改成 "split range [2.5, 97.5]%"。
- **n2.** L220-222 "Merging, which we did not measure, is geometric by construction and should be treated as harmful." —— 未测量的处方性建议。
- **n3.** 5 个自训场景的 fresh/deploy 难度偏置（garden `cal_med` 0.0444 > `dep_med` 0.0400）值得一句注释：这正是附录 trap 1 说的"视角难度不交换"，而它在自训场景里依然存在。
- **n4.** L399-402 把"视角抽样误差"和"划分抖动"混为一谈：paired 抵消的是 clean/stale 的公共成分，**不**抵消"只有 16–25 个视角"这一层。
- **n5.** L184-187 与 L387-392 对同一现象的表述（"eight of nine negative" vs "0.7–6.7 points"）应统一。
- **n6.** 参考文献中 2026 年的 AURA / VSCP / Manifold-GS / Dong 四条本审稿不核实其存在性，但 L361-369 用"我们核对了该文不含 edit/re-certify/invalidate 三个词"作为新颖性论据**偏弱**，且容易被反驳（词不含不代表问题未讨论）。→ 建议换成"该文的证书绑定其自身的 pruning ladder 与阈值，我们的问题是 receiver 用自己的准则剪枝"（这本来就是更好的论证）。

---

## 3. 必须做的增补测量清单（按 价值/算力 排序）

> 关键前置：`residual maps` 与 `rendered RGB` **都没有缓存**（脚本只存 JSON 摘要）。所以下面凡是"零 GPU"的项，都依赖 **#1 先做一次带缓存的渲染**。做掉 #1 之后，#2/#3/#4/#5/#9 全部变成离线分析。

| # | 要测什么 | 用哪些已有 artifact / 代码 | GPU | 时间 | 最坏情况 → 论文怎么改 |
|---|---|---|---|---|---|
| **1** | **缓存 per-view per-pixel 残差图**（clean/prune50/prune30/shdeg1/quant8/pup30 × 9 场景），并缓存渲染 RGB。`many_splits.py`/`edit_families.py` 只需加 `np.save` | `many_splits.py`, `edit_families.py`, `voxel_and_task.py` | 需要 | 1–2 h（5M primitives 的 PLY 载入是瓶颈） | 无风险，纯基础设施；它把后面所有统计从"重跑"变成"重算" |
| **2** | **粒度一致的 ratio 表**：同一 edit 在 pixel / 64×64 block / 0.25 voxel 三种粒度下的证书损失 + task ratio | `many_splits.json`(pixel) + `vt_*.json`(voxel+task) + `certificate_audit.py::block_max` | 依赖 #1 | 0（#1 后） | 最坏：pixel ratio = 1.0–2.5× → 摘要把"低估 1.9–12.1×"改成"在 region 粒度低估 2–12×、在 pixel 粒度 1–2.5×"，并新增一条真结论："覆盖率的失真量级由粒度决定，这是阈值统计量的固有性质" |
| **3** | **view-level 证书重算**（per-view 平均残差 / 95 分位作分数；主表在 view-level 与 pixel-level 两种定义下并排） | #1 + `certificate_audit.py::bootstrap_ci` | 依赖 #1 | 0 | **最高风险**：n=10、α=0.1 时 q=max，主表 drop 可能缩到 2–6pp 或消失 → 论文只能保留 pixel-level 陈述并改摘要措辞（B2 的文字修法），但仍可发表 |
| **4** | **paired q 增长 + no-op 噪声地板**（同一 400 划分上 q_edited/q_clean 的比值分布；quant8 作为 0 点校准） | `edit_families.py` 改 3 行 | 依赖 #1（否则 1 h） | 0–1 h | 最坏：26–71% 缩到 10–30% 且区间重叠 → Fig. 2 换成 paired ratio 图，规则 (a) 的"代价"改成实测区间；不删规则 |
| **5** | **修复曲线的子集分布**：每个 n∈{2,4,6,8,all} 抽 ≥100 个 cal 子集，报分位区间；n=all 必须入表 | #1 + `results_v22/cert_v3.json`（对照） | 依赖 #1 | 0 | 最坏：确认 n=2 是保守过覆盖（预期如此）→ 规则 (a) 改写为"2–4 视角足够但会过度保守 3–7pp"，这是**更好的**规则 |
| **6** | **下游任务 paired 化 + 阈值 sweep**：固定 patch 集合；`peak ∈ {0.5,0.6,0.7}` × `tol ∈ {1,2,3}`；每场景 per-view bootstrap 区间 | #1（含 RGB 缓存）+ `downstream_task.py` | 依赖 #1 | 0.5–1 h | 最坏：treehill 的 31.7pp 掉到 15pp、ratio 上限从 12 掉到 ~6 → 与 #2 合并改写，方向性结论大概率保住 |
| **7** | **第二下游任务**（如 patch 级深度/边缘一致性，或 ORB/SIFT 类特征匹配命中率），检验"是否只有一个任务表现如此" | #1 + 新代码 | 需要 | 1–2 h | 最坏：第二任务与 coverage 同步 → 第 2 贡献降级为"task-dependent"，那就只留一个任务并明写局限（可接受，但不能再叫"the" downstream task） |
| **8** | **sensitivity 剪枝准则去泄漏**：用训练视角或独立第三视角集算 Fisher 打分 | `sensitivity.py` + `criteria_stats.py` | 需要 | 2–4 h（梯度回传内存重，crit_a 曾 OOM） | 最坏：优势从 70–83% 缩到 20–30%、flowers 变负 → 规则 (b) 降级为"三个场景成立、flowers 除外"，或整体降为 observation |
| **9** | **5 个自训场景补 400 划分协议**（现在单次划分） | #1 + `many_splits.py --scenes garden,room,counter,kitchen,bonsai` | 依赖 #1 | 0.5 h | 最坏：garden/room 的符号翻转（`garden_base −6.7` vs `garden_ft −17.8` 已提示极不稳定）→ 明写"这 5 个场景只作定性，不进主表" |
| **10** | 更多视角 / 独立重采集 / 更多场景（外部效度） | — | 需要 | 天级 | 留给 future work；但**每个场景 16–25 视角**是本稿所有区间宽度的直接原因（L399-402），至少要说明为什么无法再加 |

**如果只能做一个**：做 #2（粒度一致化）。它把"1.9–12.1×"这个最容易被打死的数字变成可控的、可辩护的陈述，且完全离线（voxel、pixel 两边的数据都已在 JSON 里，只差 task 与它们的配对表）。

---

## 4. 我会怎么给分

### 4.1 现在这一版：**reject**

三条理由（每条都能独立成立）：

1. **核心 headline 与本文主表自相矛盾**：摘要的 4.6 与表 1 的 10.9 是同一资产同一编辑；`1.9–12.1×` 依赖一次未声明的粒度切换，匹配粒度下是 `1.0–2.5×`，其中两个场景连"低估"都不成立。这是彻底的 claim–evidence 不匹配，不是表述问题。
2. **证书认证的事件与实现不是同一个东西**：§2 说 view-level、摘要说 per-view error ≤ q，代码是 pixel-level 边际分位数。要么改 claim，要么改全部主表；现状是两者都没有。
3. **26–71% 的宽度结论被作者自己的 no-op 编辑推翻**（±18% 噪声地板、SH 截断相位下 q 反降 17%），而且修复曲线删掉了唯一与结论相反的 n=all 列（0.876/0.892）。这两点合起来会被读成"选择性报告"。

补充：M2（sensitivity 剪枝用 deployment 视角 GT）与 M7（reproducibility statement 指向另一篇稿子）会让"三条可落地规则"中的一条和"可复现性"这一整节同时失去信用——这正是 TMLR 最看重的两样东西。

### 4.2 改到什么程度我会写 accept（可执行门槛）

**必须全部满足（否则仍是 reject）：**

- **A. 粒度一致化**：表 1、表 3、摘要、Fig. 9 使用同一粒度并显式标注；摘要给出**匹配粒度**下的 ratio 区间。若结果是 `1.0–2.5×`，照写 `1.0–2.5×`。（→ #2，离线）
- **B. 证书事件定死**：明确"随机像素"或"随机视角"，主表在所选定义下重算，摘要措辞与之一致；删除"effective sample size is the number of views"这类与实现相反的句子，或让实现符合它。（→ #3，离线/一次渲染）
- **C. q 增长换 paired 估计并给出 no-op 噪声地板**（quant8 作为 0 点）；若 26% 落在噪声内，删/改 Fig. 2 与规则 (a) 的代价数字。（→ #4）
- **D. 修复曲线补 n=all 与子集区间**，正文承认 n=2–4 是"过度保守"而非"回到名义水平"。（→ #5，离线）
- **E. 复现声明与 main.tex 一致**：校验脚本指向 main.tex 并把 v52–v62 纳入，或把 statement 降级为可辩护的弱表述；6 组无 artifact 的数字补出或标注。（→ M7，离线）

**做到 A–E 我就会写 accept**，即使 headline 从 `12.1×` 掉到 `2.5×`——因为那时论文的真实贡献是**两条协议级陷阱**（①chronological split 会静默过高覆盖并掩盖约一半损伤；②把训练视角混入校准会低 8pp 且看起来完全正常）+ **一条"证书指标与下游任务解耦"的量化**，这些是 3DGS 社区里任何后续"certified asset"工作都必须处理的，价值独立于 ratio 的具体倍数。

**再加以下任一条，我会写明确 accept（无保留）：**
- F. 下游任务 paired + 阈值 sweep + 每场景区间（→ #6），并补第二任务（→ #7）；
- G. 规则 (b) 的 sensitivity 准则用不相交视角重算并保住 70% 以上缩减（→ #8）。

**我不会因为以下理由拒**（提前说明，免得作者过度防御）：场景只有 4 个 released、单任务、α 单点、剪枝=按不透明度排序、负结果占版面——这些在一个 measurement study 里都可以接受，只要如实标注边界。真正致命的是上面 A–E。

---

## 5. 已核对数字

全部由本审稿人用 `numpy` 直接从 JSON 重算；脚本片段见附录 A（临时脚本已删除，只保留片段）。
`✓` = 与 main.tex 一致；`✗` = 不一致；`未核实` = 找不到 artifact。

| # | main.tex 的说法（行号） | 我重算的值 | 来源 | 结论 |
|---|---|---|---|---|
| 1 | 表 1 fresh cov 0.894–0.901（L159-162） | flowers 0.9006 [0.8629,0.9336]；bicycle 0.8938 [0.8202,0.9507]；treehill 0.8987 [0.8235,0.9544]；stump 0.8997 [0.8074,0.9640] | `results_v52/many_splits.json` | ✓ |
| 2 | 表 1 30% drop −10.9/−18.6/−12.8/−11.7（L159-162） | −10.90 [−12.55,−9.31]、−18.57 [−21.81,−15.15]、−12.82 [−15.40,−9.62]、−11.69 [−13.75,−9.37] | 同上 | ✓ |
| 3 | 表 1 50% drop −3.6/−5.3/−4.5/−2.1 | −3.63、−5.35、−4.53、−2.07 | 同上 | ✓ |
| 4 | 表 1 五个自训行 0.956/0.920/0.898/0.923/0.899，drop −6.7/−2.0/+0.7/−3.5/−2.2 | 0.9556/−6.70；0.9198/−1.97；0.8979/+0.69；0.9230/−3.55；0.8986/−2.17 | `v62/{garden_base,room_small,counter_base,kitchen_base,bonsai_base}.json` | ✓（但 room 用了 `_small`，其余用 `_base`；见 m3） |
| 5 | 表 2 SH 3→1 −2.0*（flowers）/ −1.0 / −0.2 / −1.0 | flowers **无 JSON**；bicycle +1.02 [+0.57,+1.52]；treehill +0.20 [−0.44,+0.59]（cost 约定）；stump +1.00 [+0.49,+1.51] | `results_v53/ef_rest.json`,`ef_bicycle.json`（`edit_families.json` 为 0 字节） | flowers 行**未核实**（run log）；其余 ✓（符号约定相反） |
| 6 | 表 2 quant8 = 0.00（四场景） | treehill −2.3e−4pp、bicycle +0.1e−4pp、stump −3.2e−4pp；flowers 未核实 | 同上 | ✓（四舍五入 0.00） |
| 7 | "q grows 26–71%"（L36-37, L312-314） | +54.2 / +42.6 / +71.2 / +25.9 % | `results_v55/widths.json` | ✓ 数值；**估计量不匹配**（B3） |
| 8 | 表 2/L326-328 "quantisation leaves interval width unchanged" | quant8 的 width_growth = **+2.2 / −18.1 / +12.1 / +0.4 %** | 同上 | **✗** 与正文矛盾 |
| 9 | 表 3 task 0.741/0.723/0.573 等 + drop −16.8/−21.6/−31.7/−11.9 | 0.7409/0.7227/0.5727 → −16.82；0.8960/0.8680/0.6800 → −21.60；0.5889/0.4722/0.2722 → −31.67；0.9063/0.9125/0.7875 → −11.88 | `results_v60/vt_*.json` | ✓ |
| 10 | 表 3 "Certificate drop" −4.6/−6.1/−2.6/−6.1（L238-241） | 实为 `voxel_prune30_drop_mean` = 4.61/6.14/2.61/6.14 | 同上 | 数值 ✓，**语义 ✗**（是 voxel 粒度，非表 1 的 pixel 粒度；是 B1 的直接证据） |
| 11 | headline ratio 1.9–12.1×（L34, L101, L260） | 用 voxel 分母：1.93 / 3.52 / 12.14 / 3.65 → **1.9–12.1×**；用 pixel 分母：**1.02 / 1.16 / 2.47 / 1.54 → 1.0–2.5×** | 同上 + `many_splits.json` | voxel 版 ✓；匹配粒度版 **✗** |
| 12 | 附录 region "drops 3–4× smaller"（L395-396, L466-467） | pixel/voxel = 2.37 / 4.92 / 3.02 / 1.90 → **1.9–4.9×** | 同上 | **✗** |
| 13 | 表 4(a) 修复曲线 0.917/0.917/0.907/0.898 等（L286-289） | 逐点一致（v22 `repair_curve`）；**被删掉的 n=all = 0.8915 / 0.9272 / 0.8764 / 0.9023** | `results_v22/cert_v3.json` | 表内 ✓；**缺列 = 与结论相反**（B4） |
| 14 | 表 4(b) opacity +10.9/+18.6/+12.8/+11.7，sensitivity +9.3/+5.6/+3.9/+2.0 | crit_b/crit_c: opacity 12.82/18.57/11.69、pup 3.87/5.60/1.99；**flowers 的 10.9/9.3 无 `crit_a.json`** | `results_v54/crit_{b,c}.json` | 3/4 场景 ✓；flowers **未核实** |
| 15 | 缩减 15%/70%/70%/83%（L294-297） | (10.9−9.3)/10.9=14.7%；69.9%；69.5%；82.9% | 同上 | ✓（flowers 依赖未核实值） |
| 16 | §3.6 自检 +3.6/+11.1/+4.7/+13.2pp（L336-337） | +3.56 [−0.33,+7.94]、+11.06 [+6.00,+15.89]、+4.66 [−2.06,+13.12]、+13.16 [+4.40,+22.27] | `results_v58/selfcheck.json` | 数值 ✓；**只有 2 个场景**，且 prune50 两个区间含 0 |
| 17 | 附录 α：−8.1 / −14.1 / −19.4（L459-461） | α=0.05: −8.04；α=0.10（v22 单划分）: −14.10；α=0.20: −19.39 | `results_v28/cert_a0.0{5}.json`, `cert_a0.2.json`, `results_v22/cert_v3.json` | ✓（但三点混用两个 artifact 与两种协议） |
| 18 | "fresh coverage close to nominal at each level"（L460-461） | α=0.05: 0.947/0.967/0.935/0.957；α=0.20: 0.801/0.816/**0.740**/0.791（nominal 0.80/0.80/0.80/0.80） | 同上 | **✗** 部分（bicycle 低 6.0pp） |
| 19 | 附录 A 三分对照 −10.3…−12.9、fresh 0.900/0.898/0.900/0.900（L426-429） | −11.60/−12.94/−10.92/−10.27；fresh 0.8998/0.9003/0.8984/0.9001 | `results_v51/three_way.json` | ✓ |
| 20 | 附录 A "200k 未微调仍损失 5.5–15.4"（L431-433） | flowers −8.59、treehill −5.51、bicycle −15.36、stump −9.82 | `results_v61/*_nofinetune.json` | ✓（注意 fresh cov 0.871–0.919，单划分可偏 3pp） |
| 21 | 附录 D half-resolution −12.8/−12.2/−20.3/−13.7 "within 1.4 points"（L463-464） | 找不到 artifact；旧 md 里对比的是 **v22** 的 −11.4/−11.9/−20.6/−12.5（差 ≤1.4）；对比 main.tex 表 1 的 −10.9/−12.8/−18.6/−11.7 则最大差 **1.7–2.0pp** | 仅 `PAPER_certificate_invalid.md:306` | 该实验**未核实 / 无 artifact**；"1.4" 用的是已弃用基线（m4） |
| 22 | ΔSH = 3.4–4.1×10⁻⁴（L217-218） | 找不到 artifact（`certificate_audit.py` L257-258 只 print 到 stdout） | — | **未核实** |
| 23 | 附录 B trap：chronological 0.944–0.988、隐藏约一半损伤、residual ratio 0.45–0.91、训练视角混入后 0.822/0.823/0.894（L445-454） | 未找到直接 artifact；`results_v2` 的 block-split naive cov 为 flowers 0.874 / treehill 0.943（**不同的 view pool，不可直接对照**） | `results_v2/*.json` | **未核实**（但这是全稿最值得补 artifact 的一条，见 §4.2） |
| 24 | "nine scenes" / "400 splits per scene"（L27-28） | 400 划分仅 4 个 released 场景；5 个自训场景为单次划分 | 全部 JSON 结构 | **✗**（容量表述，M6） |
| 25 | Reproducibility "104 assertions covering the reported values"（L353-357, L472-474） | 实跑 `verify_paper_numbers.py` → `104 numeric checks, 0 failures`，但 `PAPER` 指向 `PAPER_certificate_invalid.md`，校验对象是 v22/v23/v28 旧值 | `research/code/scripts/verify_paper_numbers.py:17,40,67,89` | **✗** 对 main.tex 不成立（M7） |
| 26 | 404 scaffold：`many_splits.py` 的 coverage 是 pixel 级 | `r[...].reshape(-1)`，`cq(...)`，`(... <= q).mean()` | `many_splits.py:88-90`；`edit_families.py` 同；`certificate_audit.py:222-225` | **✗** 与 §2 "view-level" 矛盾（B2） |
| 27 | 下游任务参数 tol=2 / peak≥0.6 / patch=32 / ±24px（L231-232） | 与 `task_success(..., tol=2, min_peak=0.6, search=24)`、`--patch 32 --n_patches 10` 一致；但 masked patch 位置**跨 variant 不固定** | `calib/downstream_task.py:75-104`；`voxel_and_task.py:145-155` | 参数 ✓；paired 性 **✗**（M3） |
| 28 | sensitivity 剪枝用哪些视角 | `sensitivity_scores(base, …, views[:8], …)`，`views = sorted(set(cal_idx+dep_idx))` | `criteria_stats.py:87,94` | **✗** 含 deployment 视角 GT（M2） |

---

## 附录 A：重算片段（可直接粘进 `python -c` / 临时 .py 复现上表）

```python
import json, io, os
ROOT = r"D:\3dsg_1"
L = lambda p: json.load(io.open(os.path.join(ROOT, p), encoding="utf-8"))
SC = ["flowers", "treehill", "bicycle", "stump"]

ms = {(r["scene"], round(r["ratio"],1)): r for r in L("research/results_v52/many_splits.json")}
vt = {r["scene"]: r for r in L("research/results_v60/vt_flowers.json") + L("research/results_v60/vt_rest.json")}
wd = {r["scene"]: r for r in L("research/results_v55/widths.json")}
ef = {r["scene"]: r for r in L("research/results_v53/ef_rest.json") + L("research/results_v53/ef_bicycle.json")}
v22 = {(r["scene"], r["edit"]): r for r in L("research/results_v22/cert_v3.json")}

for s in SC:                                     # #1/#2/#3/#10/#11
    td  = 100 * (vt[s]["task_clean_hit"] - vt[s]["task_prune30_hit"])
    vd  = 100 * vt[s]["voxel_prune30_drop_mean"]
    pvd = -100 * ms[(s, 0.3)]["drop_mean"]
    print(f"{s:8s} fresh={ms[(s,0.3)]['clean_mean']:.4f} p30={-pvd:+.2f} "
          f"task={td:+.2f} voxel={vd:.2f} ratio_voxel={td/vd:.2f} ratio_PIXEL={td/pvd:.2f}")

for s in SC:                                     # #7/#8  (no-op 噪声地板)
    print(s, "q_prune30_growth=%.1f%%  q_quant8_growth=%.1f%%  q_shdeg1_growth=%.1f%%"
          % (wd[s]["q_prune30_growth_pct"], wd[s]["q_quant8_growth_pct"], wd[s]["q_shdeg1_growth_pct"]))

for s in SC:                                     # #13  n=all 被删掉的列
    rc = v22[(s, "prune30")]["repair_curve"]
    print(s, [(c["n_cal"], round(c["cov_rc"], 3)) for c in rc])
```

**说明**：本次审稿只读 `submission/main.tex`、`research/code/**`、`research/results_*/**`、`PAPER_*.md`；未改动任何文件；`review/reviewer_stats.md` 之外未留下任何写入。
