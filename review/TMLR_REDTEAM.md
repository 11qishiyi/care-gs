# TMLR 红队复审 · main.tex v4（917 行）

> 立场：我是要拒这篇的审稿人，不是来帮忙的。所有行号指 `submission/final/main.tex`；数字口径按 `review/WORK_PORTRAIT.md` §1。
> 总判断：**R1 危险、R2 危险、R3 可挡**。危险的不是证据量，是**主张的形态**——我们把两条可以被打成"同义反复"或"未建立"的主张放在摘要最前面，把三条能救命的材料放在附录和 §2 的普通段落里。

---

## 1. 三条最可能的拒稿理由（按概率）

### R1（最可能）"你的核心结论是自己定义的同义反复，而你在正文里把它证明了两遍"

> *"The authors' own mechanism paragraph (§3.4) shows that a threshold statistic cannot track any task that depends on sub-threshold structure; the measurement is therefore a signature of a definition, not a finding about 3DGS."*

挡不住的是 **L520 这一句**："This is a threshold effect, and **the measurements above are its direct signature**." —— 这句话把 §3.4 全部测量降格为定义的直接推论。同一件事在 §2 已被提前承认：L170-173 只说"per-pixel marginal 是最弱但仍可核对的声明"，没有说"最弱 ⇒ 必然不追踪任务，我们测的是幅度与符号"。摘要 L41-44 又把这条同义反复放在 "and most importantly" 之后。审稿人只要引 L515-520，我们无从回答。

**最小修补（不动实验，2 段话）**：把"certificate does not track utility"从**结论**降为**背景**（"a marginal threshold statistic cannot, by construction, track sub-threshold structure"），把**真正的结论**换成可反驳的那一条：*失效幅度跨任务不可迁移（0/36–36/36），且符号在编辑强度上非单调（50% 处证书更惊慌、30% 处任务更惊慌）*。摘要 L41-49 与 L515-520 各改 3 句即可。改完之后 R1 从"同义反复"变成"我们量化了一条已知不可能性的边界形状"——这是 TMLR 的合法贡献形态（CARDS_EVAL §"测量/协议敏感性"四篇都是这个形态）。

### R2 "任务侧的每个数都没有区间，而你的招牌反转落在覆盖率的括号里；0/36–36/36 是你自己声明不做推断的量"

> *"Every coverage number carries a 2.5/97.5 bracket and no task number carries any; the claimed reversal on bicycle (4.9 vs 3.1–3.5 points) sits inside the coverage drop's own bracket [-7.0,-2.9], and the 36-cell grid is disclaimed two paragraphs later as not thirty-six replications — yet it is the number in the abstract."*

挡不住的是 **L493-496**（"the ordering reverses on three of four scenes"）+ **Table 5 L459-478 全表零区间**（对比 Table 6 L547 只有 registration 列有 view-level paired bootstrap）+ **L502-504**（"we read the grid as a sensitivity display rather than as thirty-six replications"）与 **L117-118、L45**（摘要/贡献把它当头条）。实测 50% 处：bicycle 差值 **1.4–1.8 点**，落在覆盖率配对区间 [-7.0,-2.9]（宽 4.1 点）之内；flowers **1.2 点**，与覆盖率区间自身宽度（1.2 点）同量级、而任务侧连区间都没有；只有 stump **5.4 点**、treehill **4.6–7.3 点**是分离的。另有一处连带风险：0/36 ↔ 36/36 的极端值由 treehill 提供，而 treehill 正是 L244-256 自诊为"高光裁剪、9.4 dB、免标签口径修不了"的那一个资产。

**最小修补（近似零成本）**：`Table 6` 的注册列已经在用 view-level paired bootstrap——把同一套代码套到 Table 5/6 的 task 列（前提：per-view 分数已存盘，**需作者确认**；若未存，这一条升级为小实验）。同时把 L493-496 改成"stump 与 treehill 上分离，bicycle 与 flowers 上不分离"，并在 §3.4 明写"0/36–36/36 是敏感性展示，不作推断"。这会把 R2 从"未建立"变成"我们知道自己几斤几两"——而这恰好是我们唯一真正的强项（n_eff 77–508、400 划分）。

### R3 "标题里是复数'Coverage Certificates'，正文只测了一个对象、一个粒度，而另一粒度就在同一张表里没被用"

> *"The decoupling test is run only at pixel granularity; the paper measured a 64×64 block certificate one section earlier and never crosses it with the task, although a block max-residual certificate is the object closest to the patch task used as the utility measure. And the title's plural is one object."*

挡不住的是 **L328-335**（自己写"The region definition is a first-class choice, not a detail"）与 **§3.4/§3.5 通篇只用 pixel** 的落差；证据就在 **L303-304**：treehill 30%/−15.2（pixel）vs −4.7（block），10%/−44.9 vs −13.4（**3.35×**）；而 bicycle/stump 在 30% 处 block 反而更敏感（−25.3 vs −22.1、−33.2 vs −27.7）。即"粒度修正的方向本身随资产翻转"，我们从没说过这件事，而它同时是我们最强的自辩材料。

**最小修补**：优先级 (b) > (a)。(b) 把标题与摘要限定为 per-pixel marginal certificate（一句话），并把 region 定义在 §2 写成 scope condition；(a) 用 Table 2 的 block 列 + Table 5 的任务列做一张并置小表，明确标注"非配对、不同划分"（弱证据，但挡住"你没查"）。**不要**在这条上做 head-to-head：L680-686 拒绝 AURA 对打的理由是"对象不同"，成立；但要补一句"AURA 的证书也是按签发时的保留集定义，所以我们的测序规则不与它冲突，只是量化它没测的编辑后漂移"——**AURA 的实际构造我只看到 L670-677 的转述，需作者确认后再写**。

---

## 2. 三类"送分题"的失分点（素材 / 藏在哪 / 该搬到哪）

**① 推断强度三件套：400 次划分 + n_eff 77–508 + 拒绝把分位称 CI。**
- 素材：L184-190（400 splits；"they are not a confidence interval for the scene"）、L192-198（观测 sd 0.013–0.034 vs 二项 1e-4 ⇒ 77–508）、L773-776（§5 又提一次）。
- 藏在：§2 两段普通正文；摘要 0 处；Table 1 标题只说 "400 random splits"，没说为什么是 400 而不是 40；§5 用"On the size of the sample"的防守语气重复第三遍。
- 搬到：§3.1 Table 1 之后设一个 named paragraph（如 *Why these brackets can be trusted*），写成一条链：观测 sd → 二项反证 → n_eff → 因此按视角重采样 → 因此括号是 split-to-split 而非 CI → 因此配对差值才是我们要报的量。摘要补半句 "effective sample size 77–508"。理由：CP 审稿人的第一问是 n 与区间语义，现在要把三段拼起来才能答（CARDS_CP §1-C 的对照表也证明"这批论文没有一篇这么报"）。

**② 反例定适用区间（全文最便宜的一分）。**
- 素材：App C **L856-863**（5 个从零短训场景 −0.8/+0.0/−0.2/+1.1/+3.2；发布检查点压到 200k 再微调仍 −10.3~−12.9；"optimisation depth, not density"），§5 L746-751 一句转述。
- 藏在：倒数第二个附录。审稿人读到 §1 时看到的是"4 个资产、一个归档"，读到 §5 时看到的是"not a law"。
- 搬到：摘要末句 + §3.1 开头。它把"外部效度不足"改写成"有边界、且边界做过实验的适用区间"——这是唯一不需要租机器的补强。同时把 L750-751 从 limitation 语气改成 claim 语气。

**③ 精确 no-op 当噪声地板 + 两条 trap 被自我降级。**
- 素材：L158/L268（8-bit 被写成 "control"）、**L316-321**（"Any method whose width growth is non-zero under this edit is measuring its own estimator noise"）、L200-203（"we report this as a trap … rather than as a contribution"）、App D L868-875（分块划分掩盖近一半退化；训练视角混入标定集降 1–8 点）。
- 藏在：no-op 在 §3.2 第三段；两条 trap 被显式降级进附录，还写了"不作为贡献"。
- 搬到：no-op 那句与①合并成同一节"estimator validation"（它是全文唯一能证明"我们测的是编辑不是噪声"的证据，比 fresh coverage 0.898–0.902 更有力，因为后者在交换性下几乎必然成立）；两条 trap 改写成编号 protocol rules 放进 §2 Protocol，并在 §7 复现声明指向它们。理由：CARDS_EVAL XFeat（L152-161）把"underspecified evaluation details"做成了**独立贡献**，我们把它写成了 confession。

---

## 3. 对 `TMLR_GAP_ANALYSIS_2026-11.md` 的独立核查

**过度自信 / 证据不足的三条**

1. **§0-6 "没有人做到数据前处理口径这一层"——被它自己的卡片推翻。** XFeat（CARDS_EVAL L152-161：Aachen 定位在发布检查点上也低于原文，归因 "underspecified evaluation details"）、ShapeNet-55（L104-113：发布检查点里存的 metrics 用的是另一套 validation protocol）、RegressionMSR（L115-124：实现偏离算法两个独立轴）——三条都是"评测/前处理口径决定数字"的同一层。可辩护的版本只有："没人对**渲染证书**做过，且没人证明过口径会改变**失效幅度**（而不只是绝对值）"。
2. **§2.3 "认证率 16% vs 12.2% ⇒ 被主动奖励"——统计上站不住。** 23/144 vs 228/1867，两比例 z≈**1.3**（p≈0.19），且认证是**申请制**（选择效应），分母还是标题匹配（报告 §7.1 自认标题级）。正确结论只能降到"没有证据表明评测类更难拿认证"。
3. **§4.1/A6 "DP-Splat 在同一篇论文里独立复现了我们的 C3"——轴不对。** 它对照的是"点空间预测 vs 全光栅化"两种**评测协议**（CARDS_3D L91-99、L272-275），不是 GT 光度前处理；且证据只到摘要级。写"protocol dependence 的独立先例"可以，写"复现 C3"一查就露。

**错的那一维：第 5 维（统计口径，"我们赢，代价 0"）。** 两个理由：(i) **比较类选错**——它拿已出卡的 5 篇 3DGS 当对照，而给分的审稿人来自 CP 池（CARDS_CP #15 BPCI、#9 17 模型 × 3 方法、#1 FDR 控制）；(ii) **与第 3 维自相矛盾**——第 3 维说"2 视角恢复"是硬伤风险，而那句话本身就是统计口径的一部分，同一句话不可能既"输且有硬伤"又"赢可正面主张"。正确判定是"**重采样纪律赢、推断 warrant 输，净平**"。（第 1 维的"空白已核实"也应降级为"标题级扫描无命中"，理由同 §7.1 自认的漏检。）

**只做 3 条，我选：A2 + A3 + (A8+A10 合并成一张表)。** A2 是唯一真正的硬伤修补（拆成"偏差校正/覆盖率保证"两句并引 Coppola & Mazo，CARDS_CP #15）；A3 用最便宜的文本动作把最大弱点换成有边界的适用区间；A8+A10 合并后是全文唯一能补上的"可复用交付物"（协议自由度 + 签发 checklist），正对维度 2。**不建议先做 A6**（见上第 3 条），A1 的部分语义 L704-706 已有、边际收益低于这三条。

---

## 4. 一条我们自己没意识到的弱点：Fig. 1 的"非线性"是阈值统计量的形状，不是剪枝的性质

正文把剂量—反应曲线的形状当作关于**压缩**的经验发现：L76-78 "the damage is strongly non-linear in the budget, and only the aggressive end is catastrophic"、L240-244、以及 Fig. 1 图注 L340-343 "the regime where compression is worth doing is exactly the regime where the certificate stops being informative"。但旧 q 下的覆盖率就是残差分布的 CDF 在 q 处的取值 F_edited(q)：只要编辑单调地把残差分布整体右移，**任何**这种编辑在 q 固定时都会给出"尾段平、穿过后陡"的加速形状。四组数（bicycle 1.0/4.9/22.1/60.0，flowers 0.8/3.6/10.8/40.8，stump 1.5/7.4/27.7/62.4，treehill 2.2/6.1/15.2/44.9）与"q 在 30–10% 处落进残差主体"完全一致，也与"被删基元越来越重要"完全一致——**这条曲线不能判别两种解释**，而正文读成了后者。更麻烦的是：这正是 §3.4 L515-520 自己给出的机制（覆盖率只数是否越过 q、对 q 以下的任何重排盲），于是同一现象在 §3.1 归因于剪枝、在 §3.4 归因于阈值，全文没有一处把两者缝合。

修补（文本 + 一列表，不动 GPU）：把 Fig. 1 的主张改成"编辑把残差分布右移，30% 处旧 q 已落进分布主体"；补报 q 的绝对值与 median r 的比值（Table 1 已有 median r 列，q 是存过的量），把"经验非线性"升级成"可预测的形状"；§3.1 末尾加一句指向 §3.4 的机制。这样 R1 的同义反复指控会从两处减到一处。

---

## 5. 口径核对（写进任何文档前先看这里）

- 30% 剪枝主口径 **10.8–27.7 点**（L223-226），不是 10.9–18.6pp（那是 App A L838 的 normalised 对照片）。
- 宽度代价 **53–122%**（L642-645），等价的"1.5–2.2× 更宽"（L99、L650）成立。
- "2–12 倍"已被 L506-513 撤回，**禁用**；正确说法是 0/36–36/36。
- 口径敏感度：stump 0.42×（=2.4× 衰减，L412/L417），对称缩放 1.04–1.17×。
- 小 nit（**需作者确认**）：L193-195 的 0.013–0.034 按 p(1−p)/σ² 反算得 **78–533**，正文写 77–508；只有取 σ=0.0133–0.0342 时才得 508。一个自带 437 条断言的稿子被审稿人用手算对不齐不划算，建议把 sd 的显示精度加到三位。
