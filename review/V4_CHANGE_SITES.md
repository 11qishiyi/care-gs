# V4 变更落点图：`submission/main_v3.tex`（752 行）

> 审计对象：`submission/main_v3.tex`（L1–L752）。与 `submission/final/main.tex` **SHA256 完全一致**
> （`D9F02683…31ECE7`），两者行号可互用。
> 目的：把 C1/C2/C3 三项改动引起的**陈旧 / 残缺 / 自相矛盾**之处逐行列出，并给出最小修法。
> 本文件只做映射，不改动论文。

## 0. 口径说明

**三项改动**
- **C1**：`tab:criterion`（L314–332）由 2 准则 → 3 准则（新增 opacity × volume = "importance"）、由 2 场景 → 4 场景；
  Fisher 数字改用 **captured ground truth** 重算（并很可能删掉 L337–341 的 normalised 口径 caveat）。
- **C2**：`tab:task2`（L486–509）在既有 30% / 10% 两档上新增 stump、treehill 两场景（registration consensus + two-view pose）。
- **C3**：§3.1 的 treehill 段（L216–224）新增逐视角残差尾诊断：saturation fraction、99th-percentile residual、
  fraction of pixels beyond the fresh quantile。

**级别**：`P0` 必改（不改就数字错或自相矛盾）；`P1` 条件改（取决于 `results_v90` 新值，必须重算/重验后才能定稿）；
`P2` 可选（措辞、计数顺带）。

**新数据现状**：仓库里**还没有** `results_v90/`（只有 `results_v70/`、`results_v80/`）。但
`tools/make_tables_v90.py` 已写定 schema 并声明 "The conventions match the submitted paper: captured ground truth"，
criterion 键为 `opacity30 / fisher30 / opv30`，诊断字段为 `brightness_ratio / sat_white / p99 / beyond_q`，
场景列表 `["bicycle","flowers","stump","treehill"]`。因此本报告里所有新数值一律写 `TBD`，但字段名与场景名可以照此对齐。

**表号**：现 tex 中六张表按出现顺序是 表 1 `tab:main`、表 2 `tab:dose`、表 3 `tab:criterion`、表 4 `tab:convention`、
表 5 `tab:task`、表 6 `tab:task2`；两张图是 图 1 `fig:dose`、图 2 `fig:three`。
注意 `submission/main_v3.aux/.log` 是**旧构建**（aux 里没有 `tab:criterion`；`fig:three` 仍写 "Three yardsticks"；
`sec:task2` 仍写 "A second task family"），不要用 aux 推编号——checklist 第 33 行的"表 3 = 四种口径、表 5 = 第二任务族"
就是旧编号。

---

## 1. 正文 / 表格 / 附录落点（按行号排序）

| 行 | 变更·级别 | 原文（节引） | 为何失效 | 最小改法 |
|---|---|---|---|---|
| 29 | C1+C2 · P1 | "strengths. **Three findings.** First, geometric pruning is the only edit that matters…" | 摘要把"准则"当背景；C1 之后正文是 3 准则 × 4 场景的独立结果。是否仍"三条发现"必须与 L65 的 "Three results" 一起决定 | 若新增一条发现 → "Four findings." 并补一条加粗小标题；若不新增 → 保留，但摘要里要出现"criterion"一词，否则与表 3 的存在不相称 |
| 30–31 | C1 · P1 | "at 30\% it costs $10.8$--$27.7$ points … with the conformal quantile growing $53$--$122\%$" | 这两个区间只对 stored-opacity 准则成立；C1 后表 3 会并排给出三种准则的 $q$ growth（现有 Fisher 已是 $+174\%$），摘要的无条件区间会与表 3 冲突 | 加限定："under the stored-opacity ranking"；或改成跨准则的范围 |
| 41–43 | C2 · P0 | "A third yardstick, a global registration front-end, loses only $3.9$ points on the same edit where the local task loses $27.3$ … the choice of task moves the answer by a factor of seven." | $3.9$/$27.3$ 是 **bicycle 单场景**值；"factor of seven" = 27.3/3.9 也只在 bicycle 成立。加入 stump/treehill 后比率变成"每场景一个"（treehill 的 local 30% 已是 $-34.4$，若 registration 仍小，比率会远超 7），无条件 "seven" 即错；"holds its rotation error below a degree" 也需在 4 场景重验 | 改成 "on bicycle … 3.9 vs 27.3; across the four released checkpoints the same contrast spans $a$--$b\times$"；子度数断言按新数据收窄场景范围 |
| 65–66 | C1(+C2) · P1 | "We measure both on four released checkpoints … **Three results**, in increasing order of consequence." | 三条结果里没有"准则比较"这一条；"Three results" 与 L29 "Three findings" 必须同步 | 决定是否加第四条结果；加则 "Three"→"Four" + 新加粗标题，并同步 L29 |
| 104–107 | C2 · P0 | "Two further task \emph{families} … registration consensus loses $3.9$ points on bicycle where local matching loses $27.3$ and the certificate $22.1$, and two-view relative pose keeps its rotation but loses a tenth of its view pairs. The choice of task moves the answer by a factor of seven" | 证据从 2 场景变 4 场景；"a tenth of its view pairs"（现为 8.3/4.8 → 5–8 点）在新场景未定；factor of seven 仍是 bicycle 专属 | 单场景点值 → 四场景范围；"a tenth" 改成范围；factor seven 加 "on bicycle / up to $N\times$ across scenes" |
| 108–110 | C1 · P1 | "the quantile grows $53$--$122\%$ after a 30\% prune against a zero-width noise floor" | 同 L30–31：该区间是 opacity 准则；C1 后表 3 会并列三种准则的 $q$ growth | 加 "under stored-opacity pruning" |
| 133–137 | C1 · P0 | "``prune to $x\%$'' ranks the primitives by their stored opacity … which is **the criterion** an asset viewer applies when it hits a memory budget." | 第三个准则（opacity × volume "importance"）全篇**没有定义**；单数 "the criterion" 也不再成立。这是唯一能定义准则的地方 | 在此追加一句定义三准则：stored opacity；calibration-view Fisher-diagonal sensitivity（`\citep{hanson2025pup}`）；opacity × Gaussian volume（写明 volume 的具体公式/尺度来源），并声明 stored opacity 仍是默认 |
| 204–205 | C3 · P2 | "…Appendix~\ref{app:region}. **Two observations** matter as much as the drops themselves." | 若 §3.1 把残差尾诊断写成第三条 observation，计数要改 | "Three observations"（或明确不把它列为 observation） |
| 216–217 | C3 · P1 | "treehill is the weakest asset in the archive ($9.4$\,dB)." | 若诊断显示尾部主要来自捕捉端饱和/裁剪，"weakest" 需要限定（是 PSNR 最低，不是资产最差） | "treehill has the lowest PSNR in the archive ($9.4$\,dB), with $x\%$ of captured pixels clipped" |
| 217–218 | C3 · P0 | "The cause is view-dependent brightness **rather than** a global gain:" | 这是被新诊断直接细化的因果句：加入 saturation fraction / p99 / beyond-q 等于引入**第二个成因**（高光裁剪），二选一的 `rather than` 结构撑不住 | 改为 "The cause is view-dependent brightness **and clipped highlights**, not a global gain"，随后接三项诊断 |
| 219–220 | C3 · P1 | "on treehill it spans $0.96$--$1.77$, with **six of eighteen** views above $1.2$." | 新诊断是同族的逐视角统计，必须紧邻这句话；"eighteen" 必须与 L120 / 表 1 / 表 2 分组头的 18 个 test view 对齐；若新文本再给"sat>$5\%$ 的视角数"，两个计数要一致 | 保留亮度比，紧接三项诊断；核对 18 与 "six" |
| 221–222 | C3 · P1 | "Fitting one scalar per view … lifts the asset from $9.4$ to $16.5$\,dB" | $16.5$ 同时是表 4（L366）的 gain 单元格；任一重算都要同步（正文-表格双向） | 改时同步表 4 L366 |
| 222–224 | C3 · P1 | "treehill stays at $9.3$--$12.3$\,dB and shows **the same qualitative behaviour** as the other three" | 9.3/12.3 = 表 4 的 one-sided/symmetric PSNR；若尾部的相当部分来自饱和，"same qualitative behaviour" 需加一句限定，否则与"tail 主要是成像端"的读法冲突 | 保留结论但加一句"after removing clipped pixels…"或收窄措辞 |
| 232 | —（既有错误）· P0 | "\caption{Each edit family on **two released checkpoints**: four pruning strengths, the two non-geometric edits, and a voxel merge…}" | 表 2 实际有 **4** 个场景块（bicycle/flowers/stump/treehill），只有 merge 行是 2 场景。C1/C2 把别的表推到 4 场景后，这句"two"会被读成同一处 2 场景局限 | "on the four released checkpoints (the voxel-merge row on bicycle and flowers only)" |
| 317 | C1 · P0 | "\caption{Same 30\% budget, **two pruning criteria**. Opacity ranks by stored opacity; sensitivity ranks by…}" | 表将有三种准则 | → "three pruning criteria"，并点出三个名字与"全部在 captured ground truth 上计算" |
| 318–320 | C1 · P0 | "Opacity ranks by stored opacity; sensitivity ranks by the Fisher-diagonal score of \citet{hanson2025pup}, **computed on calibration views only** so that no deployment view informs the ranking." | (a) 缺第三准则定义；(b) C1 把 Fisher 换到 captured GT，这句对"用哪套 GT"完全沉默；(c) Fisher 用标定视角 GT 属 label-using，而 §3.3（L388）说认证只能用 label-free 口径，三种准则并排需要标注 | 补第三准则定义；补 "all three computed on the captured ground truth of section~\ref{sec:convention}"；给 label-free / label-using 打标 |
| 322 | C1 · P0 | "`\begin{tabular}{lrrrr}`" | 3 准则 ×（coverage drop, $q$ growth）= 6 数据列 | → `{lrrrrrr}` |
| 324–326 | C1 · P0 | "`& \multicolumn{2}{c}{coverage drop} & \multicolumn{2}{c}{$q$ growth}` / `\cmidrule(lr){2-3}\cmidrule(lr){4-5}` / `Scene & opacity & sensitivity`" | 跨列数、`\cmidrule` 范围、表头行都要扩一列 | `\multicolumn{3}{c}` ×2；`\cmidrule(lr){2-4}` + `{5-7}`；两处表头加 `importance` |
| 328–329 | C1 · P0 | "bicycle & $-22.1\,[-25.2,-18.8]$ & $-11.6\,[-14.8,-8.2]$ & $+105\%$ & $+84\%$"（flowers 行同理） | Fisher 四个数（$-11.6$、$-18.9$、$+84\%$、$+174\%$）整体作废（改 captured GT 重算）；还要加第三列 + stump/treehill 两行 | 4 行 × 6 格全部取 `results_v90` stage9 的 `opacity30 / fisher30 / opv30`（`drop_mean/lo/hi`、`q_growth_mean`） |
| 334–336 | C1 · P0 | "The criterion matters as much as the budget, **and it does not point one way** … halves the damage, from $22.1$ to $11.6$ … nearly doubles it, from $10.8$ to $18.9$, and the quantile grows by $174\%$ instead of $53\%$." | 四个 Fisher 数全部会变；"halves" / "nearly doubles" / "does not point one way" 是在旧二准则二场景上归纳的定性结论，方向可能反转，必须以新数重推 | 按新数重写整段（3 准则 × 4 场景的对比矩阵），不要只做数字替换 |
| 337 | C1 · P0 | "**The two rankings** are nearly unrelated on flowers, which is why they disagree there." | 三准则 → 三组两两比较；"nearly unrelated"（秩相关）需重算或删除 | → "the three rankings"；给出重算后的秩一致性，或改成定性表述 |
| 337–341 | C1 · P0 | "One caveat applies to the comparison: the Fisher score was computed on **the normalised ground truth** … It is still a fair comparison between **two criteria**, and **a ranking on the captured ground truth is left open**." | C1 的前提消失："left open" 变成"已做"，必须删；"two criteria"→"three" | 整句替换为 "All three rankings are computed on the captured ground truth (section~\ref{sec:convention}), the convention we report as primary." |
| 343–344 | C1 · P0 | "**We report both** rather than recommending one: a budget does not determine a damage level…" | "both" = 两准则 | → "all three"；若新数据出现一边倒（某准则在所有场景都更好），"rather than recommending one" 的立场要重述 |
| 457–459 | C2 · P0 | "A claim of the form ``coverage under-reports damage by a factor of $k$'' is therefore **not well posed**: the factor ranges from zero to well above one across four scenes at a fixed edit strength." | 这段明确否证 "factor of $k$" 式表述，而摘要 / L107 / L479 / L530 / L548 正是 "factor of seven"。C2 让任务侧比率变成每场景一组，两处必须统一（`review/FINAL_REVIEW.md` 已把它列为 M6） | 先在此段定义"per-scene ratio"，再按范围改其余五处；或反过来把此段改成"我们只报告每场景比率" |
| 463 | C2 · P2 | "with the task exceeding the coverage loss in $36/36$ cells on **both assets** at $2.0$ and $2.7$ times the coverage loss" | merge 仍只在 2 场景，本身不改；但 4 场景框架下 "both assets" 易被误读 | 必要时改 "on bicycle and flowers" |
| 475 | C2 · P0 | "`\includegraphics[width=0.92\linewidth]{fig_three.pdf}`" | 图 2 的 **PDF 本体是 2 场景**：`tools/make_fig3.py` 里 `cov`/`bat` 硬编码 bicycle+flowers，读的是 `results_v70/second_task.json` | 按 4 场景重画（读 `results_v90/second_task_stump_treehill.json` + `third_task_stump_treehill.json` + 4 场景 battery） |
| 476–479 | C2 · P0 | "\caption{Four yardsticks on **the same assets** and the same 30\% edit. … both lose **about a fifth** … loses **a tenth** of its view pairs, and a registration front-end loses **under four points**. … **a factor of seven**.}" | 每个概括值都在 2 场景上取；"under four points" 在 treehill 上很可能不成立 | 改"on the four released checkpoints at the same 30\% edit"，概括值换四场景范围 |
| 483 | C2 · P2 | "\subsection{Two more task families, and two more answers}" | 族数不变（2），但"two more answers"在 4 场景下变成"每场景一答" | 可留；或 "…and a different answer on every asset" |
| 489–491 | C2 · P0 | "\caption{Four yardsticks on **the same edited assets**." | 现在"the same edited assets"只是 2 个场景 | → "on the four released checkpoints" |
| 493–494 | C2 · P1 | "``pose'' is the drop in the fraction of view pairs … (**it does not change further between 30\% and 10\% pruning in our data**)." | 这是对 pose 列的数据断言（现表 −8.3/−8.3、−4.8/−4.8 相等）；stump/treehill 若两档不等，caption 即假 | 按新数重验；若不等，改为 "on bicycle and flowers it does not change…" 并在表内保留两档 |
| 498–509 | C2 · P0 | `tab:task2` 表体（bicycle/flowers 各 2 行） | 需新增 stump/treehill × 30%/10% 四行 + registration 列的 view-level bootstrap CI | 复制 `\multirow{2}{*}` 块结构；CI 用 `tools/make_fig3.py` 里同一个 `boot()` |
| 511–512 | —（既有错误）· P0 | "The **next two subsections** add two task families, and each answers the same question differently." | 两个族都在**本节**（§3.5）里，并不存在 "next two subsections"；C2 本来就要改这句上下文 | → "This subsection adds two task families…" |
| 519–525 | C2 · P1 | "the fresh asset already leaves the inlier ratio **$0.83$--$0.93$**, so the metric has little headroom … $3.9$ points is a larger fraction of the available range than it looks. Both push in the same direction: this task is less sensitive … **conservative for our argument**." | 0.83–0.93 是 2 场景 clean 范围（flowers 0.829 / bicycle 0.927）；treehill 只有 9.4 dB，clean inlier 很可能显著更低 → "headroom 很小，所以比较保守" 的论证可能整体反转 | 重算四场景 clean 范围；若 treehill 很低，这两句必须重写，否则与"less sensitive"结论冲突 |
| 527–531 | C2 · P0 | "loses \emph{3.9} points on bicycle and \emph{2.6} on flowers … The four yardsticks differ by a factor of seven **on the same asset** … At 10\% the first three collapse together ($-40.8$ to $-76.3$ points) while the pose measure stays where it was" | 需补 4 场景 30%/10% 值；factor seven、$-40.8$→$-76.3$ 区间、"pose stays" 三处都要重算 | 按新表重写；"on the same asset" → "on bicycle（其余场景见 $a$--$b\times$）" |
| 535–545 | C2 · P0 | "**It sits between the other two.**" / "on **both assets** ($0.40^{\circ}$ on bicycle, $0.66^{\circ}$ on flowers)" / "falls from $1.00$ to $0.92$ and $0.95$. That is **$5$--$8$ points** … more sensitive than registration consensus ($3.9$ points) and far less sensitive than local matching ($27$ points)" / "median error is $32$--$47^{\circ}$" | 整段是 2 场景；"on both assets" 必须变 4；子度数（$<1^{\circ}$）断言是摘要 L42 的支撑，treehill 上未必成立；三族敏感度排序（5–8 落在 3.9 与 27 之间）可能被新场景打破 | 全段四场景重写；"on both assets"→"on all four assets" 并补两个新场景的括号值；排序结论按新数据重述 |
| 547–552 | C2 · P1 | "moves the answer by **nearly an order of magnitude**. … **Coverage, local matching and global registration** respond to the same edit with different magnitudes and, at mild edits, different signs." | "nearly an order of magnitude" ≈ 7（同 factor seven）；枚举漏了 pose（现表里 pose 也随编辑变化），4 场景后更难自洽 | 改成范围；枚举里加 pose，或说明为何排除 |
| 562–565 | C1 · P1 | "The conformal quantile grows by **$53\%$ to $122\%$** after a 30\% prune … and by $325\%$ after a 10\% prune (Table~\ref{tab:dose})" | 同 L30–31 / L108–110：区间是 opacity 准则的；表 3 将并排三种准则的 $q$ growth，可能超出 122% | 加 "under stored-opacity pruning"，或把区间扩成跨准则范围 |
| 644–646 | C2 · P2 | "\paragraph{What is not measured.} **Three task families are measured** (local template matching, global registration consensus, and two-view relative pose); a learned detector … would test whether **the spread we report** is itself task-specific." | 族数不变（3），无需改数；但 "the spread we report" 现在建立在 4 场景上，措辞可加强 | 可选："…on four assets" |
| 647–648 | C1 · P0 | "and **a criterion sweep beyond the two criteria** of Table~\ref{tab:criterion}." | 点名句：三准则已测完，"beyond the two" 双错（数目错 + 已做） | → "a wider criterion sweep beyond the three criteria of Table~\ref{tab:criterion} (e.g.\ mixed per-carrier scores)"，或整条删除 |
| 650–653 | C3 · P0 | "That range deliberately includes the weakest asset in the archive (**$9.4$\,dB, a brightness offset between render and capture**)" | 这是 §3.1 诊断在 400 行外的**压缩副本**；C3 改因果句后必须同步，否则同一事实两处解释不一致 | → "($9.4$\,dB, a brightness offset between render and capture plus clipped highlights)" 或与新诊断一致的措辞 |
| 673–675 | C1+C2+C3 · P0 | "…by an automated check of **359 assertions** that parses this \LaTeX{} file and exits non-zero on any mismatch" | 新表新增约 24（C1）+ 40（C2）+ 12（C3）个十进制字面量；断言数会变，且不新增 check 会失败或漏覆盖 | 跑一次 `tools/verify_tex_v3.py` 得新计数并回填（checklist/playbook 同步，见 §3） |
| 676–679 | C1+C2+C3 · P1 | "The assets themselves are recorded in a provenance file (archive identity and size, renderer and library versions, per-scene primitive counts, resolutions and view counts)" | 新数字需要 artifact 出处（`results_v90/stage9/*.json`、`second_task_stump_treehill.json`、`third_task_stump_treehill.json`），provenance 表要登记 | 扩 `tools/make_provenance.py` 并重生成 |
| 680–682 | C1+C2+C3 · P0 | "**All but a handful of the decimal literals** in the paper are covered by an assertion; the exceptions are parameters ($\alpha$, percentiles), one illustrative example…" | 加表后若不同步扩 `verify_tex_v3.py`，这句就是假的；更危险的是"percentiles"这个例外条款会被误用来豁免新的 **p99 残差**（那是测量值，不是参数） | 扩 check；把 p99 明确排除在"参数例外"之外 |
| 682–684 | C1+C2+C3 · P1 | "…are each a single command. Code, per-scene result files and the check suite are provided as anonymised supplementary material." | 现有 `submission/supplement.zip` 只有 `results_v70/`、`results_v80/`（98 项），无 `results_v90`；zip 内 `paper/main.tex`、`check/verify_tex_v3.py` 也要重打包 | 重跑 `tools/make_supplement.py`，纳入 stage9 产物，并复核 checklist 的"98 项 / 223 KB" |
| 710–713 | C1 · P1 | "(…measured in our earlier campaign, **under the normalised convention** of section~\ref{sec:convention}) … $-2.6$ to $-6.1$ points at 30\% pruning, against **$-10.9$ to $-18.6$** at pixel granularity in the normalised convention, i.e.\ a factor of $1.9$--$4.9$." | C1 之后全篇不再有主表使用 one-sided 口径，本附录成了唯一"用非主口径比主结论"的地方；而 §3.2（L299–301）引用这 $1.9$–$4.9\times$ 时未提口径；且 $-10.9$/$-18.6$ 取自表 4 的 one-sided 两格（flowers/bicycle），表 4 一改就得跟 | 保留但显式写明"早于 captured-GT 切换"，或按 captured GT 重跑 voxel；并核对 $-10.9$/$-18.6$ 与表 4 |

---

## 2. C3 需要的**新增内容**（不是"改"，是"补"，容易整体漏掉）

1. **三项统计量的定义**必须落地（论文里目前一个都没有）：
   - saturation fraction：饱和的判据（例如 captured 图里 $\ge 254/255$ 的像素？三通道同时？），以及是"逐视角"还是"全场景汇总"；
   - 99th-percentile residual：在**哪些**像素上取（全部 held-out 像素 / 逐视角再取中位）、单位与 $q$ 同尺度；
   - fraction of pixels beyond the fresh quantile：注意它按定义等于 $1-\text{coverage}$（§2 L149–150），若不加"逐视角"，就会与表 1 的 coverage 列重复。
2. **对称性**：现段落对"其它三场景"只给了亮度比（$0.92$–$1.19$），新诊断若只给 treehill，读者会问"你怎么知道这是 treehill 特有问题"。
   `tools/make_tables_v90.py` 的 `resid_diag` 是**四个场景都算了**的，建议同时给四场景（至少给一行对照）。
3. **若做成新表**：会插入第 7 张表 → 其后所有 `\ref` 自动对，但 checklist / playbook / `verify_tex_v3.py` 内部注释里的**硬编码表号会全部右移**（见 §3、§4）。建议做成段落内联数字或并入表 1，避免表号地震。
4. **与 L120 的视角数对齐**：18 个 test view（L120、L198、表 2 分组头）是逐视角诊断的分母。

---

## 3. 数值同步对照（表格 ↔ 正文）：**哪些行必须跟着格改**

> 用途：重算后只改这些行；反之，这些行里只要有一处没改，就是硬伤。

| 表 | 关键单元格 | 正文出现处（行） | 备注 |
|---|---|---|---|
| 表 1 `tab:main` L195–198 | PSNR $22.2/16.8/23.9/9.4$ | 76、217、221、375、650、652 | 同时被**表 4 第 1 列原样复制**（L363–366），改一处必须改两表 |
| 表 1 | drops $-22.1/-10.8/-27.7/-15.2$ | 69、77、212–214、292、335、376、440、445–447、502–506、529 | 其中 502–506 是表 6 的 coverage 列（同值复用） |
| 表 1 | $q$ growth $+105/+53/+122/+108$ | 31、109、563 | 与表 3 的 $q$ growth 并列时需口径限定（见 L30–31/L562–565） |
| 表 1 / 表 2 分组头 | views $25/22/18/16$ | 120、220、242、251、260、268 | C3 的 "six of eighteen" 依赖 18 |
| 表 2 `tab:dose` L242–274 | $-1.0/-4.9/-22.1/-60.0$、$-0.8/-3.6/-10.8/-40.8$、$-15.2/-62.4$、$-44.9$、$-35.4/-19.5$、$3.3/0.0$、block $-44.3/-13.4$ | 68–71、212–214、279–301、445–447、531、563 | 531 的 "$-40.8$ to $-76.3$" 是把表 2（flowers 10%）与表 6 混在一起说的 |
| **表 3 `tab:criterion` L328–329** | $-22.1/-11.6/+105\%/+84\%$；$-10.8/-18.9/+53\%/+174\%$ | **只在 335–337** | 好消息：Fisher 重算只需重写 §3.2 那两句；但 opacity 半边（$-22.1/-10.8/+105\%/+53\%$）与表 1/2 共用，**不能单独改** |
| 表 4 `tab:convention` L363–368 | $22.2/-22.1$ … $16.5/-13.1$；$0.42$–$1.01$/$1.04$–$1.17$/$0.86$–$1.57$ | 75–79、221–223、373–380、392、710–713 | "as captured" 列 = 表 1 的 PSNR+drop，绑定改 |
| 表 5 `tab:task` L414–428 | $18/36$、$12/36$、$0/36$、$36/36$；任务点值 | 38–41、102、440–441、445–447、455–456、460（$r=0.99$） | C2 不动它；但 8 个 scene-level 点的 $r=0.99$ 若被读者与 4 场景任务表混淆，需一句"来自表 5 数据" |
| **表 6 `tab:task2` L502–506** | $-22.1/-27.3/-3.9[-5.1,-2.7]/-8.3$；$-60.0/-76.3/-31.1/-8.3$；$-10.8/-11.1/-2.6/-4.8$；$-40.8/-60.7/-28.4/-4.8$ | 41–43、105–107、476–479、528–531、543；$3.9$ 另见 522，$27.3$ 另见 38/42/81/440 | $-76.3$ 只在 531 出现；pose 值只以 "5–8 points"、"a tenth" 的形式出现（542、478） |

---

## 4. `SUBMISSION_CHECKLIST.md` 中会过期的条目（按行号）

| 行 | 原文（节引） | 问题 | 最小改法 |
|---|---|---|---|
| 3、5、20 | "12 页，329 KB"、"98 个目录项，223 KB"、"12 页 / 336,501 B，与投稿 PDF 逐字节相同" | 加 6+4 行表格、一段诊断与新数后会重新编译；zip 项数/体积也变 | 重编译后回填页数/字节数/项数 |
| 6、8、14、15、33、46 | "**359 条断言**"（6 处） | C1/C2/C3 会新增数十个十进制字面量 | 统一回填新计数；同时修 73/76 的 "336 assertions"（与 359 自相矛盾） |
| 33 | "…四种 GT 口径（表 3）、36 格阈值扫描（表 4）、第二任务族（表 5）" | 这是**旧构建**的表号：现 tex 中 表 3=准则、表 4=口径、表 5=patch 任务、表 6=四标尺；再加一张诊断表则全部右移 | 改成按内容命名（"准则表""口径表""任务表"），不写编号 |
| 44 | "正文 ≤12 页 ✅ 12 页（正文约 8 页…）" | 主表加行后总页数会变；若新增一张表可能逼近门槛 | 重编译后复核 |
| 63 | "§3.1：渲染偏亮、**约一成像素饱和**；…per-view gain 能抬到 16.5 dB" | 论文正文目前**没有"饱和"二字**；C3 恰好补上——checklist 已经"超前"于论文 | 保留，用实际数值回填"约一成" |
| 64 | "\"只测一种剪枝准则\" → §2 定义 stored-opacity top-k；**§5 明说未做准则对比**" | 双重过期：论文已比 2 准则，改后 3 准则；§5 现在写的是 "beyond the two criteria" | → "\"3 准则 × 4 场景\"，见 表 3 + §3.2；§5 改为'超出三准则的扫描'" |
| 65 | "§3.4 36 格 × 4 场景；§3.5 **第二任务族**，两者相差 **7 倍**" | 实为两个族（registration + pose）；7 倍只是 bicycle | → "两个任务族（registration / two-view pose），$7\times$ 仅 bicycle，四场景 $a$–$b\times$" |
| 86 | "剪枝准则未对比（**只测了 opacity**）" | 与同文件 L92 自相矛盾（那里说做了 Fisher 对比） | 整句删除或改写 |
| 92 | "剪枝准则对比（Fisher…）bicycle $-22.1$→$-11.6$；flowers $-10.8$→$-18.9$（方向相反）" | Fisher 数会因 captured-GT 重算而变；场景扩到 4；新增第三准则 | 换成 4 场景 × 3 准则的新值 + "新表 3" |
| 94 | "三族任务敏感度谱：$27.3 / 3.9 / 5$–$8$ 点" | 4 场景后是范围不是点值 | 换成"四场景范围 + 图 2 重画" |
| 81 | "数据：`results_v70/`（…）；附录沿用 `research/results_v17…`" | 缺 `results_v90/`（stage9 一次跑完的 clean/opacity30/fisher30/opv30 + 诊断 + 两个新场景任务） | 补一行 `results_v90/`（stage9 三件套） |

---

## 5. `review/REBUTTAL_PLAYBOOK.md` 中会过期的条目（按行号）

| 行 | 原文（节引） | 问题 | 最小改法 |
|---|---|---|---|
| 4、5 | "12 页"、"359 条断言" | 同 checklist | 重编译/重跑后回填 |
| 21 | "treehill 0.96–1.77（6/18 视角 >1.2）；per-view gain 可抬到 16.5 dB"；"若对方坚持要补：**需要 per-view residual map 才能进一步定位（一次渲染）**" | C3 正是这件事，做完后"要补"一栏必须变成"已有" | 补饱和比例 / p99 / beyond-q 三个数字，删"需要 per-view residual map" |
| 22 | "表 3：opacity vs Fisher…；**第三条准则（volume/importance）需节点**" | 第三条准则已测；Fisher 数也会变 | 改为"表 3：三准则 × 四场景（captured GT）"，并删"需节点" |
| 23 | "表 6 + 图 2：四族标尺 $27.3 / 22.1 / 5$–$8 / 3.9$ 点；表 5 36 格阈值扫描" | 表 6 由 4 行变 8 行，点值变范围；图 2 要重画 | 换四场景范围；"四族标尺"仍成立（证书/局部/注册/位姿） |
| 28–30 | 补实验排序第 1 条"第三族/第二族扩到 4 场景"、第 2 条"per-view residual map + treehill 诊断"、第 3 条"第三条剪枝准则" | **这三条正好是 C2 / C3 / C1**，全部将已完成 | 三条标记 done（或删除），队列重排为"微调作为编辑""学习型匹配器"；成本表随之改 |
| 24 | "4 个场景太少 → 附录 C：5 个自训场景无效应" | 场景数仍是 4（除非本轮也扩），论证不变 | 不改，但若扩到 4 场景后审稿人问"为何不是 8 场景"，答案仍是附录 C |

> 同族但不在本次清单内的两点（顺带记一笔，避免同一处反复改）：
> - `submission/final/OPENREVIEW_SUBMISSION.md` L18–36 是**摘要副本**，且已落后当前 `main.tex` 一版
>   （缺 "and a fourth, two-view relative pose, holds its rotation error below a degree"、"in three of four scenes"）。
>   摘要一改，这里必须重贴；L33–34 的 "factor of seven" 同样受影响。
> - `submission/PATCH_stage8.md` L46 把上一轮整改目标写成 "a criterion sweep beyond two criteria"，本轮结束后作废（可作本轮 PATCH 模板）。

---

## 6. 已核对、**不需要**改的句子（防止过度改写）

| 行 | 句子 | 为什么不用改 |
|---|---|---|
| 27–28 | "four released 40k-iteration checkpoints … 400 random calibration/deployment splits" | 场景数/划分数本来就说的是 4 个场景；C1/C2 不增加场景，只是把已有场景补进两张表 |
| 68–71 | "costs $1.0$/$4.9$/$22.1$/$60.0$ coverage points on bicycle … at most $3.3$ points and nothing" | 表 2 的 bicycle 剂量曲线；C1/C2/C3 都不动这些渲染 |
| 73–79 | "…inflates the residual scale nearly sevenfold on one scene … by up to $2.4\times$" | 口径结论来自表 4；C1 只是把**准则**改用 captured GT，不改口径结论。（注意 "sevenfold" 与 "factor of seven" 是两件事，别做全局替换） |
| 92–95、100–103 | 贡献 1、3 | 40 万次划分、有效样本量 $77$–$508$、36/36 与 $0/36$–$36/36$ 都来自表 1/表 5 |
| 116–123 | Assets 段（4 个 checkpoint、view 数 $25/22/18/16$、gsplat 1.5.3） | 已是 4 场景 |
| 125–131 | "Two conventions are in use…" | 与 C1 不冲突（反而 C1 之后更干净） |
| 139–152、154–175 | Certificate 定义、Protocol、有效样本量 | 与三项改动无接口 |
| 185–189、195–198 | 表 1 caption 与数据 | 已有 4 场景、captured GT |
| 207–215 | fresh coverage $0.898$–$0.902$、bicycle/flowers 剂量 | 不受影响 |
| 242–277、279–301 | 表 2 数据与剂量/合并段 | merge 仍 2 场景（见 L463 的 P2） |
| 349–371、373–395 | 表 4 与 §3.3 全节 | C1 不改口径表；Fisher 重算也不动它 |
| 400–471 | §3.4 全节（含 $r=0.99$、$18/36$…） | 来自表 5；C2 只动表 6 |
| 558–586 | §3.6 修复、§3.7 循环检查 | 与三项改动无接口（除 L562–565 的口径限定） |
| 588–632 | Related work | 只提方法名，不提数字 |
| 657–661 | 样本量段（$16$–$25$ 视角、$24$–$35$ of AURA） | 不变 |
| 719–750 | 附录 B/C/D（repair、scope、traps） | 不变；"five scenes" 与 "four checkpoints" 是两批资产，别"统一" |

---

## 7. 风险清单：最可能被忘的三处

1. **"factor of seven" 这条链的五个落点 + 一处自我否证**。L43（摘要）、L107（贡献）、L479（图 2 caption）、L530（正文）、
   L548（"nearly an order of magnitude"）同一句话说了五遍；而 L457–459 又在论证 "a factor of $k$" 的说法 **not well posed**。
   C2 之后它必然是"每场景一个比率"，五处必须一起改成范围——最容易忘的是 L457–459（现有 `review/FINAL_REVIEW.md` 的 M6 正是这条）。
2. **L650–652 讨论节的 treehill 括注**："($9.4$\,dB, a brightness offset between render and capture)"。
   它是 §3.1 诊断在 400 行外的压缩副本；改 §3.1 因果句时几乎必然漏掉，漏掉后同一事实两处解释不一致。
3. **`fig_three.pdf` 这个二进制本体（L475）**。文本搜索永远搜不到它；而 `tools/make_fig3.py` 把场景硬编码成
   bicycle+flowers（`cov` / `bat`，读 `results_v70/second_task.json`）。最典型的翻车方式是"caption 改成四场景了，图还是两场景"。

**次席（顺手一起解决）**：L674 的 "359 assertions" 与 checklist 里 6 处计数（若每次都跑 verify 会自动暴露）；
L232 表 2 caption 的 "two released checkpoints"（本来就是错的，C1/C2 后会显得格外刺眼）；
L30–31 / L108–110 / L562–565 的 "$53$–$122\%$"（新表 3 里会出现比 122% 更大的 $q$ growth，若不加准则限定会被现场打脸）。

---

## 8. 建议的落地顺序（避免来回改同一处）

1. 跑完 stage9 → `results_v90/`，用 `tools/make_tables_v90.py` 打出三准则 × 四场景、诊断、两个新场景任务的全部数字。
2. 先改**表**（表 3 结构 + 表 6 行），再改**依赖表的句子**（§3.2 L334–344、§3.5 L527–545）。
3. 再改**摘要/贡献/图 caption**（L29–43、L104–110、L476–479、L530、L548），最后回头统一 L457–459 的口径。
4. 重画 `fig_three.pdf`，扩 `tools/verify_tex_v3.py`，重跑断言 → 回填 L674。
5. 重打包 `supplement.zip`（含 `results_v90`），最后更新 `SUBMISSION_CHECKLIST.md` / `review/REBUTTAL_PLAYBOOK.md` / `OPENREVIEW_SUBMISSION.md` 摘要副本。
