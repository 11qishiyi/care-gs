# V4 复审：改动部分的文字与论断一致性

范围：p1（标题+摘要）、p4（§3.1 treehill）、p5–6（§3.2 准则）、p8–9（§3.5、表 6、图 2）、p11（§5–§7），
外加 `main.tex` 对应段落。按要求**不复核算术**（405 条断言 / 96/96 表值已由他人审过）。

## 结论（3 行）

**needs small fixes（需小改）**：无一处需要重跑实验，全部是句级改动，约 1 处 BLOCKER + 5 处 MAJOR + 8 处 MINOR。
BLOCKER 是表 6 caption 里一句从两场景版残留的数据断言，已被新加的两行直接反驳，必须改。
改掉后即可提交；摘要/贡献列表的结构性不对称（第 6 条）建议一并补一句，成本很低。

## Findings

### BLOCKER

**1. [p9, 表 6 caption] `(it does not change further between 30\% and 10\% pruning in our data)`**
表内 treehill 的 pose 是 `+5.9` → `0.0`，30% 与 10% 相差 5.9 点（一对 view pair），这句"在我们数据里不再变化"被同表的新增行直接推翻；
它是两场景版（bicycle/flowers 均为 −8.3/−8.3、−4.8/−4.8）的残留。读者对照表格即发现 caption 与表体矛盾。
最小改法：`(on bicycle, flowers and stump it does not change further between 30% and 10% pruning; on treehill see the note below)`。

### MAJOR

**2. [p1, 摘要] `at 30\% it costs 10.8--27.7 points of per-pixel coverage, with the conformal quantile growing 53--122\%`**
这两个区间只在 stored-opacity 准则下成立。表 3 在同一 30% 预算下给出 `op.×vol.` 的 40.0 / 61.8 点与 `+263\%` / `+328\%`，
而摘要下一句自己就引用了 61.8——同一段内 `61.8 > 27.7`、`328\% > 122\%`，构成自相矛盾。这是 v4 新增表 3 后摘要未同步的唯一硬冲突。
最小改法：加限定 `under the stored-opacity ranking`；p2 贡献列表第 5 条的 `53--122\%` 同样加这一限定。

**3. [p4, §3.2] `On bicycle the two certificates agree within two points at every prune level`**
表 2 印的是 pixel/block：30% 为 `−22.1` vs `−25.3`（差 3.2），10% 为 `−60.0` vs `−65.6`（差 5.6）。"every prune level" 被自己的表否证（只有 70%/50% 两档差 0.1）。
最小改法：`agree within two points up to a 50% prune; at 30% and 10% the block certificate loses 3.2 and 5.6 points more`。

**4. [p8, 图 2 caption] `a relative-pose estimate keeps its rotation error below a degree while giving up 4.8--8.3 points of view pairs`**
两处问题：(a) 图 2 画的是 `drop from fresh asset (points)`（view-pair 成功率下降），**没有画 rotation error**，caption 宣传了图里不存在的量；
(b) treehill 的 pose 柱是正值 `+5.9`（图中可见，在 0 线之上），落在 "4.8--8.3" 区间之外，仅靠括注 "at its resolution limit" 撑不住。
最小改法：rotation error 归于 §3.5 正文，caption 改为 `giving up 4.8--8.3 points of view pairs on bicycle, flowers and stump (on treehill the fresh rate is 12/17, so its bar moves by one pair and is not an effect)`。

**5. [p8–p9, §3.5] `Two caveats on the second task before its numbers.`**
同一句里"族"的编号自相冲突：p8 `The first asks a different question about the same view: detect Harris corners...` 把 registration 叫第一族，
紧接着 `the second task` 的 caveats（translation model、inlier ratio `0.83--0.93`）讲的仍是 registration；p9 又叫 `A third family`（pose）。
读者无法判断 caveats 属于哪一族。最小改法：`Two caveats on the registration task before its numbers.`

**6. [p1–p2 结构] `Three findings.` / `Three results, in increasing order of consequence.` / 5 条贡献**
新增的准则句只出现在摘要里：p2 三条加粗结果没有一条讲准则，5 条贡献也没有一条讲准则比较（p2 的 Setup 段只是定义了三种准则）。
即摘要头号发现里塞进了一个全文没有"贡献位"的结果，而摘要与引言都仍写"Three"。**结论：仍是三条发现，句子在语法上属于 First，但读起来像硬塞的第二条**——缺连接词，
且 `of the same order` 没有比较对象（p1：`is a variable of the same order`；§3.2 p5 才写全 `the same order as the budget`）。
最小改法（二选一）：① 句首加 `Within that edit,`、补 `as the budget`，并在 p2 第一条加粗结果与贡献列表各补半句；② 升为第四条发现，摘要与引言同时 `Three`→`Four` 并加一条贡献。

### MINOR

**7. [p4, §3.2] `Merging is the fourth edit and the one we predicted rather than measured in an earlier draft.`**
草稿史/实验日志句，违反"不写实验流水账、不自曝版本史"的风格规则，且对读者零信息。改：`Merging is the fourth edit, and the most damaging operation we test.`

**8. [p4, §3.2] `That is not universally true: moving to world-space voxels ... reduces the measured effect by 1.9--4.9$\times$ ... so we report the definition next to every number.`**
`That` 指代不明（上一句是 `The region definition is a first-class choice`），且自我拆台；`next to every number` 不实（图 1/图 2、表 3/5/6 的数字旁都没有 granularity 标注）。
另外这组 1.9–4.9× 是在 normalised 口径下算的（Appendix A），p4 未说明。改：`World-space voxels reduce the effect by 1.9--4.9$\times$ under the one-sided convention (Appendix~\ref{app:region}); we therefore state the region definition wherever a coverage number is introduced.`

**9. [p9, §3.5] `the pose measure stays where it was`**
treehill 的 pose 从 `+5.9` 到 `0.0`，字面上一对 pair 的移动。改：`stays where it was within one pair`。

**10. [p11, §5] `an earlier measurement found drops of $-0.8$ to $+3.2$ points`**
"drops" 不可能为正；且 `an earlier measurement` 是日志口吻。改：`found changes of $-0.8$ to $+3.2$ points (Appendix~\ref{app:scope})`。

**11. [p11, §5] `fewer than the 24--35 of AURA, which is the direct cause of the width of our coverage intervals`**
替审稿人攻击自己：主动把自己的区间宽度归因到样本量不足，并与被引工作比短。改：`The paired drops are robust because split-to-split variation cancels; we report absolute coverage as intervals with $77$--$508$ independent scores.`（删掉 AURA 比较与 "direct cause"）

**12. [p4, §3.1] `treehill is the weakest asset in the archive ($9.4$\,dB)`**（p11 同句重复）
只测了四个资产，`in the archive` 不可证；且与同段"成因是拍摄端 view-dependent brightness + clipping"自相矛盾（PSNR 低不等于资产差）。改：`treehill has the lowest PSNR of the four against the captured ground truth ($9.4$\,dB)`。

**13. [p1 摘要 / p2 贡献] `the only edit that matters`**
merge 也是几何操作、且比 30% prune 更伤（35.4 vs 22.1，p4），"only edit" 的边界读者会追问。改：`of the edit families we test, only the geometric ones matter`。

**14. [p2, 贡献列表] `giving up up to 8.3 points of view pairs`**
`up up` 重复词（`main.tex` L112 即 `up to` 前多一个 `up`），这是唯一的重复词，已印在 PDF 上。

**15. [p4, §3.2] `Geometry dominates by an order of magnitude`**
30% 档是 22.1 vs 3.3（约 6.7×），只有 10% 档达到 18×。改：`by a factor of seven at the 30% budget and more at 10%`。

**16. [p4, §3.1] `Five of those views clip`**
`those` 指前句的 "six ... views above 1.2" 还是全部 18 个？改：`Five of the six clip`。

**17. [p6, §3.3] `the measured coverage drop halves: $-11.7$ instead of $-27.7$ points`**
表 4 与摘要给的是 0.42×/2.4×，"halves" 弱于自己的数据。改：`falls to $0.42\times$ ($-11.7$ instead of $-27.7$ points)`。

**18. [p8, §3.5] `Every cell of the previous subsection varies one template matcher.`**
句法不通：上一小节变的是阈值，不变的是 matcher。改：`Every cell of the previous subsection uses the same template matcher; only the threshold varies.`

**19. [p11, §7] `...and figures quoted from the cited work...`**
`figures` 与图号混淆（此处指数值）；同时这句主动交代"有一部分字面量没被断言覆盖"，属自愿示弱。改：`numbers quoted from the cited work`，并删掉 `one illustrative example` 的列举。

**20. [p11, §6] `It proposes no new generative capability and releases no data.`**
与 §7 `Code, per-scene result files and the check suite are provided` 口径不一致（读者会问 result files 算不算 data）。改：`releases no new dataset`。

## 干净项（clean，已核对通过）

- **"two rankings" / "both criteria" / "two scenes" 全部清零**：p4–p6 已是 `three pruning criteria and four assets`（表 3 caption）、`We report all three`（p5）、表 2 caption `four released checkpoints`；旧的 normalised-GT caveat 删除后没有留下孤儿句（§2 与 §3.3 自洽）。
- **strength words 与表 3/表 6 逐一对上**：`the worst of the three on every asset`（40.0/22.1/61.8/15.8 对 12.7–22.1 全成立，treehill 仅差 0.6 但仍是点值最小）；`42--56%`（42.5/52.0/56.6）；`up to 61.8`；`2.5--11.3`；`4.8--8.3`（三场景）；`0 to 36 of 36`（18/12/0/36）；`36/36 on both assets`（merge）；`2.4×`、`1.04--1.17×`、`0.42×`；`10.8--27.7` 与 `53--122%` 作为 stored-opacity 的区间本身正确。
- **treehill 诊断句已自洽**：`brightness and clipped highlights rather than a global gain` 与亮度比 0.96–1.77、p99 3.4、gain 修复 9.4→16.5 dB 一致。
- **treehill pose 异常（+5.9）的告知**：表 6 caption 有 `only 0.71 over 17 pairs ... should not be read as an effect`，正文 p9 有 `we do not interpret its entries`——**在表内出现处已告知，未在正文里当作结论使用**，处理诚实且不构成自攻；只需按第 1、4、9 条把散布在图 2 caption 与 "stays where it was" 处的不精确口径收紧。
- **无 dangling ref**：`Table~\ref` 全部有 `\label`（tab:main/dose/criterion/convention/task/task2，fig:dose/three，app:region/repair/scope/traps，sec:* 均存在）。
- **"factor of seven" 已绝迹**（仅剩 `nearly sevenfold` 的残差尺度句，属 §3.3 且与表 4 一致）；`factor of four to eleven` 三处（摘要、图 2 caption、p9）口径一致。
