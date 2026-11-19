# FINAL_REVIEW — *Valid but Unusable: What Coverage Certificates Miss When 3D Gaussian Splatting Assets Are Edited*

> 评审身份：TMLR 审稿人（conformal prediction / 统计方向）。
> 评审方式：冷启动通读 `submission/final/main.pdf`（11 页）与 `main.tex`，解包 `supplementary.zip` 到临时目录只读检查，并从 `results_v70/*.json` 独立重算数字（作者自带的 verifier 只作为线索，不作为判据）。全程未修改论文、代码、数据。
>
> **路径约定**：`results_v70/*.json` = 工作区里的主数字来源；`supp/results/results_v*/…` = `supplementary.zip` 内的早期战役结果；`scripts/…`、`calib/…`、`check/…` = zip 内的代码；`research/results_v*/` = 工作区里的更早战役。`main.tex` L 号指 `submission/final/main.tex` 的行号。

---

## 1. 判定

**REJECT**（若 TMLR 给 accept / accept-with-minor-revision / reject 三档，我选 reject；离 accept 的距离不是"再多跑一个实验"，而是"已有测量被选择性报告、关键口径未定义、且有三处论文陈述与作者自己的 artifact 相反"）。

- **TMLR 标准 #1（claims supported by accurate and convincing evidence）：不满足。** 8 条主 claim 中 2 条成立（剂量–反应、修复成本）、3 条部分成立（几何编辑、不同调、第二任务族）、3 条不成立（口径影响、阈值扫描、自检循环）（§2 逐条）。
- **TMLR 标准 #2（audience interest + clarity）：基本满足。** 选题对 3DGS × CP 交叉的读者有真实价值，写作清楚、组织紧凑，11 页可读；但 Setup 段缺一个致命定义（pruning criterion），摘要缺两个必标的口径（granularity、ground-truth convention），标题与实测现象的对应关系不严（§3）。

我给出的判定理由可以压缩成一句：**这篇稿子的测量本身大体可靠（表内数字我逐格重算过，5 个抽查数字全部对得上，drop 的 paired interval 也确实很紧），但它把至少三个"已有对照/已有正确口径"留在了自己的 artifact 里没上报，而这些对照恰好把三条主结论各削掉一半到三分之二。** 这不是"结论需要更强证据"，而是"现有证据在正文里被裁剪过"。

---

## 2. 标准 #1：逐条判定

| # | Claim（摘要/贡献条目） | 论文位置 | 判定 | 一句话理由 |
|---|---|---|---|---|
| 1 | 几何编辑失效：30% pruning 代价 10.8–27.7 点 | 摘要；§3.1 Table 1；贡献 1 | **部分成立** | 数字对，但 criterion 全文未定义；作者自己的 sensitivity(PUP-style) criterion 下量级小 3–6×（B3） |
| 2 | 剂量–反应：70/50/30/10% 单调非线性 | §3.1–3.2 Table 2, Fig.1 | **成立** | 四场景四点单调，paired interval 紧；仅 treehill 的 pixel/block 差 3.2×（M3） |
| 3 | 口径影响：attenuation up to 2.4× | 摘要；§3.3 Table 3 | **不成立（作为现象）** | 只报非对称 norm_gt；自有 norm_both / gain 两臂下 attenuation 消失或反转（B2） |
| 4 | 覆盖率与效用不同调 | §3.4 Table 4 | **部分成立** | 方向成立（3/4 场景在 50% 处反转），但证据质量弱：36 格伪重复（M1）、treehill 行由缺陷残差驱动（B1） |
| 5 | 阈值扫描：0/36–36/36 | §3.4；贡献 3 | **不成立（作为稳健性论证）** | 36 = 3 个近重复 config × 12 个嵌套阈值；无不确定性；本质是同一观测的数法（M1） |
| 6 | 第二任务族：factor of seven | §3.5 Table 5, Fig.2 | **部分成立（证据不足）** | 仅 2 场景、translation-only RANSAC、clean 端饱和到 0.93；且"factor"论证与 §3.4 自己的"not well posed"冲突（M2, M6） |
| 7 | 修复成本：validity 便宜、width 贵 | §3.6；App. B | **成立（有内部矛盾）** | q growth 53–122% 的 paired 数据可信；但 App. B 的"within three points（0.882–0.971）"自相矛盾（m5） |
| 8 | 自检循环不可用（label-free check 无用） | §3.7 | **不成立（数字层面）** | 逻辑对，但整段数字来自旧战役（v58，2 场景），与 Table 1/2 矛盾（B5） |

**展开说明（只写需要展开的）：**

- **Claim 1 的部分成立**：Table 1 四行与 `battery_*.json` 完全一致（我重算：−22.08/−10.84/−27.71/−15.17）。问题不在数字，在"pruning 是什么"从未定义。`main.tex` 全文没有出现 opacity / criterion 的定义（唯一出现 "opacity" 的是 Related Work 里 AURA 的 baseline 与 Limitations 里"未测 pruning criteria"这句）。真实代码是 `argsort(-opacities)[:k]`（`scripts/many_splits.py`、`scripts/certificate_audit.py`）。这是一个**最粗暴的 baseline**，而作者自己的 `scripts/criteria_stats.py` 已经实现了 sensitivity 版 pruning 并跑出了结果（`results_v54/crit_b.json`, `crit_c.json`）。同一 30% 预算下：bicycle 18.57 → 5.60，stump 11.69 → 1.99，treehill 12.82 → 3.87（同 30%、同 400 splits、同为 norm_gt 口径，仅 criterion 不同）。也就是说"30% 代价 22 点"这句话在论文引用的压缩文献真正使用的 criterion 下会变成"5.6 点"。这不是 scope 限制，这是主结果的 criterion 依赖性。
- **Claim 3 不成立**：见 B2。`norm_gt` 是把 GT 每图缩放到 mean=0.40 而 render 不动（`calib/colmap_io.py::normalize_exposure`）。`results_v70/diag_*.json` 里还有 `norm_both`（对称 mean-match）与 `gain`（per-image scalar gain）两臂，覆盖率下降分别是 −23.10/−12.70/−29.36/−15.70 与 −23.98/−16.99/−27.43/−13.08；相对 raw 的比率是 **1.03–1.17× 与 0.86–1.57×**，而不是论文报告的 0.42–1.01×。作者自己的代码注释写着 `norm_gt ... <- what the paper does today`，并解释"normalising only the GT can turn a mild exposure difference into a large residual"——即作者本人知道这一臂是把曝光差放大成残差。用这一臂去论证"convention 值得 2.4×"，在真评审里会被直接判为 strawman。
- **Claim 8 的失败是技术性的**：`supp/results/results_v58/selfcheck.json` 只有 flowers 与 treehill 两个场景，值分别是 prune30_actual 0.7894 / 0.7684、prune50_actual 0.8644 / 0.8534。§3.7 的"0.768–0.864"是 treehill@30% 与 flowers@**50%** 的拼接，却被写成"after a 30% prune"。以正文 Table 1/2 的口径重算，30% prune 后的 stale coverage 是 **0.6215/0.6776/0.7501/0.7921**，over-prediction 是 **12.2–27.8 点**，不是 3.6–13.2 点。方向（自检无用）没错，但这一段现在的数字既不是正文口径、也不是同一 edit strength，属于"用旧战役的极端值撑一个新段落"。

---

## 3. 标准 #2：audience interest + clarity

**有兴趣，且我认为这批读者真实存在**：做 3D asset 分发/压缩的人需要一个"这份资产还能不能信"的答案；CP 社区关心"保证在模型被改写后还剩多少"。第 3.4–3.7 节的负结果（coverage 不跟踪 utility、自检循环）是这个领域里少见的、说人话的坏消息，值得发表。

**但 clarity 有 5 个具体失分点**（不是文笔问题，是读者会读错）：

1. **"certificate" 从未与文献中的对象对齐。** 摘要的定义（per-pixel `|r|` 的 marginal 分位数）是作者自己构造的；Related Work 里 AURA 的对象是 per-carrier reliability 的 mean-unreliability bound on the retained set，VSCP 是 view-structured interval。标题 "What Coverage Certificates Miss" 会让读者以为在评价这两个方法，实际一个都没跑。这是**读者预期管理**问题，也是 B4 的核心。
2. **标题与实测现象不匹配。** "Valid but Unusable" 描述的是**重新校准之后**的 certificate（valid 但宽 1.5–2.2×）；而论文的主现象是 coverage 掉到 0.62–0.79，即 **invalid**，不是 "valid but unusable"。两个现象都存在，但标题取了后者、正文主表和摘要主打前者，读者会一直错位。
3. **摘要每个数字都缺两个必要口径**：granularity（"10.8–27.7" 只在 pixel 下成立，block 下是 4.7–33.2）与 convention（captured，而非 normalised）。
4. **Tables 4–5 的操作点选择不对称**：local task 给了 3×4=12 格扫描、正文还反复引用"36 格"；registration 只给一个固定 2 px 阈值、一个 translation 模型。读者会怀疑"factor of seven"是在给弱指标留面子。
5. **Table 2 的 PSNR 列藏着一个反例**：SH degree 3→1 让四个场景的 PSNR 全部变好（−0.07/+1.16/+0.39/+2.44 dB），正文却解释成 "truncating high-order coefficients smooths the render"（smoothing 不会让 PSNR 系统性上升）。这是表格与解释不一致，且**其实是支持论文论点的免费证据**（图像指标变好、证书变差），被浪费了。

---

## 4. 软肋清单

分级：BLOCKER ×5、MAJOR ×6、MINOR ×9。每条给（a）原文位置（b）真评审里会怎么写（c）最小修法 + `[离线可改]` / `[需要新测量]`。

### BLOCKER

#### B1. Table 1 的 treehill 9.4 dB 工作点撑不住，而且"no protocol repairs"是错的

**位置**：`main.tex` L186（Table 1 treehill 行）、L203–206（"treehill is the weakest asset in the archive (9.4 dB, a brightness offset between render and capture that no protocol repairs)"）、L549–552（§5 重复同一句）。

**为什么会失分**：三点叠加，每一点都是审稿人会写进 review 的原句。
1. 残差剖面不是一个 offset。treehill 的 median residual 是 0.0310（≈30 dB 的典型像素），mean 0.1035，但 PSNR 9.4 dB 反推 rms = 0.338。这意味着**约 11% 的像素承载了几乎全部误差**（若这些像素 r≈1，MSE≈0.11 → PSNR≈9.6 dB，与实测 9.4 吻合）；一个 per-view brightness offset 会把 median 也抬起来，不会留下 30 dB 的中位像素。审稿人会写："'a brightness offset between render and capture' 与 Table 1 三列数字不符；请给出 per-view error map 或残差直方图。"
2. "no protocol repairs" 与作者自己的数据相反。`results_v70/diag_treehill.json` 里 `gain` 臂（per-image scalar exposure fit，即 Mip-NeRF 360 系列的标准评测口径）把 treehill 从 **9.415 → 16.502 dB**，`norm_both` 抬到 12.295 dB。正确说法只能是 **"no label-free protocol repairs it"**；而这句话是有意义的，因为它把"9.4 dB 是渲染链缺陷还是标签口径"这个真问题带出来了。
3. 四个工作点全部低于同一资产的公开数字（archive 自己报 bicycle 25.2 dB，这里 22.2；另外三个场景的公开 3DGS 值约为 flowers ≈21.5 / treehill ≈22.5 / stump ≈26.6 dB，这里 16.8 / 9.4 / 23.9——这三个数是我按 3DGS 原文的 Mip-NeRF 360 表给出的参考量级，未在本地 archive 中核对，见 §8）。而且是在 1/4 分辨率下渲染——通常分辨率降低 PSNR 会**升**。审稿人会写："在解释 2.7–13.1 dB 的系统性差距之前，所有 coverage 结论都建立在一条未验证的渲染链上。"
4. 更棘手的是位置：treehill 恰好是贡献 3（36/36）、贡献 1 的高端、以及"不同调"叙事的极端行。**如果一个场景的渲染是坏的，它就不能同时是最强论据。**

**最小修法**：
- Table 1 的 PSNR 列改成 `raw / gain` 两列，并在 caption 里说明 `gain` 是 label-using 的评测口径（只能用于 PSNR，**不能**用于 certificate 的 calibration/deployment，否则是标签泄漏——这一点论文目前完全没讨论，见 M5）。
- 把 §3.1 那句机制断言替换成残差剖面描述（median 0.031 / mean 0.104 / rms 0.338 → 约 11% 饱和像素），并把 treehill 的 36/36 结论改成"由残差场的长尾驱动"——**这其实是一个比现在更强的机制论点**：treehill 的 q 实际是在给渲染缺陷定价，而不是给模型误差定价，所以 coverage 对 edit 不敏感、task 反而崩。
- `[离线可改]`（PSNR 与 coverage drop 都在 `diag_*.json` 里）+ `[需要新测量]` 一张 per-view error map / hist（重渲染一次即可）。

#### B2. §3.3 的 "attenuation up to 2.4×" 是非对称预处理的产物；能证伪它的对照就在作者自己的 JSON 里

**位置**：摘要 L33–35；Intro L72–78；Table 3 与 §3.3 L311–326（尤其 L320–321 "The attenuation is scene-dependent (0.42× to 1.01×)"）。

**会怎么失分**：审稿人会写——"你的 Table 3 只有两臂：`raw` 与 `norm_gt`。`norm_gt` 只动 GT、不动 render，这在你们自己的代码里被注释为 'can turn a mild exposure difference into a large residual'。在 `results_v70/diag_*.json` 里你们已经算了对称臂 `norm_both` 与标准评测臂 `gain`，覆盖率下降分别是 −23.10/−12.70/−29.36/−15.70 与 −23.98/−16.99/−27.43/−13.08，相对 `raw` 是 1.03–1.17× 与 0.86–1.57×。也就是说 attenuation 只存在于非对称预处理下，"2.4×" 是一个实现错误的效应，不是一个 convention 的效应。" 这一段是全文第二大卖点，被判 strawman 的代价比第一大卖点更大。

**最小修法**：把 §3.3 重写成三段：(i) `norm_gt` 是早期 pass 的预处理（label-free 但病态），报出它，明说它是 self-inflicted；(ii) 报 `norm_both` 与 `gain` 两臂，指出对称/标准口径下 attenuation ∈ [0.86, 1.57]；(iii) 结论改成一条**新约束**而非一条警告："certificate 只能用 label-free 口径；而 label-free 口径里对 GT 的每一种选择都在改变量级，所以 coverage 必须标注口径——但可用的口径集合比论文暗示的窄得多。"同时把 "sevenfold" 换成明确统计量（stump：median 6.72×、mean 4.75×、rms 3.18×；现在是取了最大的那个）。`[离线可改]`

#### B3. 主结论的 pruning criterion 全文未定义，而作者已跑过的 criterion 对照把量级削掉 3–6×

**位置**：§2 Setup（无 criterion）；§3.1/§3.2 Table 2（"prune to 70%"）；§5 L546–547（"… and a comparison between pruning criteria" 被列为**未**测量）。

**会怎么失分**：两句话同时成立，很致命。
- "pruning to 70% of the primitives" 没有定义保留规则。审稿人默认会以为是 PUP/LightGaussian 那类 sensitivity/Fisher 规则（这正是 Related Work 里你引的三篇在做的事），实际用的是 `argsort(-opacities)[:k]`——最简单的 opacity 阈值，恰好是**对证书最不利**的一类（按不透明度排序会优先删掉低不透明度的"填充"primitive，改变遮挡结构）。
- Limitations 说 pruning criteria 没测，但 `supp/results/results_v54/crit_{b,c}.json` 与 `scripts/criteria_stats.py` 就是那个测量：opacity30 vs pup30（同 30%、同 400 splits、同 norm_gt 口径）——bicycle 18.57→5.60、stump 11.69→1.99、treehill 12.82→3.87；q growth 71.2%→33.6%、25.9%→6.0%、42.6%→3.4%。flowers（从 run log 恢复）10.9→9.3。
  换句话说：**在被引压缩文献真正使用的 criterion 下，"coverage 掉 22 点"变成"掉 5.6 点"，"q 涨 71%"变成"涨 34%"。** 审稿人一旦发现这个，会把贡献 1 从"measured phenomenon"改判为"a property of the crudest pruning baseline"。

**最小修法**：(i) Setup 写明 criterion 并说明为何选它（作为最粗暴 baseline，便于与文献对比）；(ii) 把 pup30 列进 Table 2（或单独一张小表），把"geometric pruning breaks the certificate"改成"opacity-ranked pruning breaks it; under a sensitivity-ranked criterion the damage is 3–6× smaller but the direction and the q-growth survive"；(iii) 删掉 Limitations 里那句"未测量"；如果要在 raw 口径下进主表，pup30 需要在 raw GT 下重跑一次（一次 prune+render × 4 场景）。`[离线可改]`（比率与方向）+ `[需要新测量]`（raw 口径的 pup30 数值，工作量小）。

#### B4. 被评价的"certificate"不是所对标文献的对象

**位置**：标题；摘要首句 L23–25；Intro L50–53；Related Work L489–505。

**会怎么失分**：审稿人（尤其是我这一方向）会写："AURA 的 certified object 是 retained carrier set 上的 mean unreliability bound；VSCP 是 view-structured interval；本文的 certificate 是 per-pixel `|r|` 的 split-conformal 分位数。三者不可互换。论文没有实例化任何一个已发表方法，却以 'What Coverage Certificates Miss' 为题，并在 intro 把这两条线并列为自己的对话对象。因此'certificate 在 edit 后失效'这一结论目前只对作者自定义的 certificate 成立。" 再叠加一句：*marginal coverage 不蕴含 conditional/task coverage* 是 CP 教科书结论（Vovk 2005；Lei et al. 2018；Angelopoulos & Bates 的 tutorial 都明写），§3.4 "Why" 段把一个已知事实当成新发现来解释，会被认为是 novelty 定位错误。

**最小修法**（三选一，我推荐 i+iii）：(i) 全文把对象改名为 "a marginal pixel-coverage certificate"，标题相应收窄（例如 *When a Marginal Pixel-Coverage Certificate Stops Meaning Anything*）；(ii) 实例化一个已发表 bound（AURA 的定义是 per-carrier，可在这四个 checkpoint 上重建，但需要新测量）；(iii) 加一个简短的形式化命题，说明"任何 split-conformal 量在 model edit 后 exchangeability 被破坏时 coverage 偏差可达 X"，把 self-check 的循环性从经验观察升级为论证。`[离线可改]`（i+iii）。

#### B5. §3.7 整段用的是旧战役的数字，且与 Table 1/2 矛盾；Reproducibility statement 的承诺被至少 4 处推翻

**位置**：§3.7 L475–485；Reproducibility statement L570–576；§3.4 L375–377；Table 4 flowers 30% 括号；App. B L613–616。

**事实**（全部可复核）：
| 位置 | 论文写 | 数据里是 |
|---|---|---|
| §3.7 | "after a 30% prune falls to 0.768–0.864 … over-prediction 3.6–13.2 points" | `results_v58/selfcheck.json`：treehill@**30%** 0.7684、flowers@**50%** 0.8644；按 v70 的 30% 数据应为 0.6215–0.7921、12.2–27.8 点 |
| §3.4 | "flowers $2.4$ coverage points and $2.3$ task points" | flowers 50% 的 coverage drop 是 **3.58**（Table 2 自己写 −3.6）；2.4 是 task loss（0.739→0.715） |
| Table 4 | flowers (32,±24) 30% 写 "(−11.0)" | raw = −11.06 → Table 5 的 −11.1 才对 |
| App. B | "within three points of nominal … (0.882–0.971)" | 0.971 比 nominal 高 **7.1** 点，同句后半段自己也承认 |

**会怎么失分**：审稿人写——"Reproducibility statement 声称 'Every number in this paper is re-derived from stored run artifacts by an automated check with one assertion per reported value'。我在正文找到四处不满足。verifier（`check/verify_tex_v3.py`）只断言表格里的数字，正文与 appendix 的散文数字没有被覆盖。这类问题单看都是笔误，合起来会让人不再相信任何一个我没重算的数。" 对 TMLR 来说这一条直接打 #1 的 "accurate"。

**最小修法**：把 §3.7 用 v70 重算（四场景 stale30 都有，一句话可改）；改 3.6；统一 −11.1；App. B 改成 "0.882–0.971（n=2 时最多高出 nominal 7 点，n 足够时 0.876–0.927）"；把 verifier 从"只查表"扩到"查散文数字"（这是可控工作量，且是作者已有的基础设施）。全部 `[离线可改]`。

### MAJOR

#### M1. "36 格"的口径：3 个近重复 config × 12 个嵌套阈值，伪重复、无不确定性
**位置**：§3.4 L381–388；贡献 3；Table 4 的 "> coverage" 列与 caption（"each is evaluated on the full 3×4 grid … (36 cells per scene)"）。
**会怎么失分**：我会写——"36 = 3 个 (patch,search) 配置 × 12 个 (tolerance, peak) 单元，而 12 个单元是同一份残差上的**嵌套阈值**（peak ∈ {0.3,0.45,0.6,0.75}，tol ∈ {1,2,4}），彼此完全依赖；3 个配置是同一渲染集上的近似重复（bicycle 三个配置各自都是 6/12，treehill 各自都是 12/12）。所以 'in all 36' 不是 36 次独立复现，而是一次观测的 36 种数法；'0/36 到 36/36' 传达的稳健性是虚假的。且该列没有任何不确定性（clean 与 pruned 是同一渲染集，差异是确定性的点估计）。"
**最小修法**：把 "36" 的构造拆开报：先给 3 个 config × 1 个主操作点（现在 Table 4 那样），再给"在 12 个阈值单元里有多少个单元保持同一符号"，并明确说明这 12 个是嵌套依赖的、不构成独立证据；正文所有 "36/36" 改成 "12/12 in each of the three configurations"。`[离线可改]`。

#### M2. 第二任务族证据不足，且两个任务的操作点不对称
**位置**：§3.5；Table 5；Fig. 2；贡献 4；摘要 L39–41。
**事实**：只测 bicycle/flowers；RANSAC 只拟合 translation；clean 端 inlier ratio 0.927 / 0.829（接近天花板，per-view 值大量为 1.0）；registration 只有固定 2 px + ratio 0.85 + min_ncc 0.5 一个操作点，而 local task 有 12 格扫描；10% 时 registration −31.1 与 coverage −60.0、local −76.3 并不"converge"。
**会怎么失分**："一个 translation-only 的 ±8 px 匹配器，作用在**同一相机位姿**的 render/GT 对上，本质是评估全局平移是否稳定；它在 30% prune 下只掉 3.9 点，很可能是因为模型在 30% 时整体亮度/结构仍一致，而不是因为'注册前段对 edit 鲁棒'。要支持 'factor of seven' 是 task-class 效应，你至少需要 (a) 第三个场景，(b) 一个含旋转/尺度的模型，(c) registration 端的阈值扫描——现在 local task 有 12 格、registration 只有 1 格，比较不对等。"
**最小修法**：(i) 把 "factor of seven" 改成"在这个特定 front-end 与这个特定操作点上差 7×"，并删掉摘要里的无条件版本；(ii) 给 registration 补 4–6 个阈值点（inlier 阈值 1/2/3/4 px × min_ncc）——这是纯后处理，`[离线可改]`（per-view 数据在 `second_task.json` 里，但需要重算匹配层，属 `[需要新测量]` 的轻量版）；(iii) 至少补 flowers 之外一个场景 `[需要新测量]`。

#### M3. "两种 granularity 很接近"只用 bicycle 举例，treehill 差 3.2×
**位置**：§3.2 L269–273（"The two granularities agree closely (−1.1 vs −1.0, −25.3 vs −22.1)"）；App. A L602–608。
**事实**（Table 2 自己，我已逐格核对）：30% 处 pixel vs block = bicycle −22.1/−25.3、flowers −10.8/−11.1、stump −27.7/−33.2、treehill **−15.2/−4.7**；10% 处 treehill −44.9/−13.4（3.4×）。
**会怎么失分**："'the headline does not hinge on the region definition' 与 Table 2 不符：treehill 的 30% 效应在 block 下只有 pixel 的 1/3。而 treehill 正是 36/36 行的来源。摘要的 '10.8–27.7' 也只在 pixel 下成立（block 是 4.7–33.2），摘要没有标注。"
**最小修法**：把 L269–273 改成"bicycle/stump/flowers 一致（≤1.2×），treehill 例外（3.2×），原因是该场景残差是长尾型（见 B1）"，摘要与贡献里给数字加 "(pixel granularity)"。`[离线可改]`。

#### M4. "The certificate is correct when fresh" 的推断强度超过证据
**位置**：§3.1 L194–197（"This validates the protocol and the implementation (an off-by-one in the quantile index would show up here)"）；§2 L152–158（n_eff）。
**事实**：fresh coverage 的 split-to-split 95% 区间是 bicycle ±4.4、flowers ±2.6、stump ±5.5、treehill ±6.7 点（`clean_lo/clean_hi`），Table 1 没给；n_eff = 77（treehill）意味着这个区间宽度是结构性的，不是可以忽略的噪声。同时，400 splits 只重抽"哪些 view 进 calibration"，其区间是 conditional on the rendered view pool（§2 自己承认），不能支撑 "correct" 这种无条件说法。另外：off-by-one 在 n=2.6×10⁵ 像素分数上完全看不出来（1/2.6e5），这句辩解不成立。
**会怎么失分**："'0.898–0.902 vs nominal 0.900' 是在 ±2.6–6.7 点的区间里读三个小数位；n_eff=77 的场景里你无法区分 0.90 与 0.95。请把区间放进 Table 1，并把 'validates the implementation' 换成 'is consistent with nominal within the split-to-split interval'。"
**最小修法**：Table 1 增加 fresh coverage 的 [2.5, 97.5] 列；删掉 off-by-one 那句；把 "correct" 降级为 "consistent with nominal"。`[离线可改]`。

#### M5. 修复叙事内部有矛盾：2 个 view 就能修复 vs calibration 污染会掉 8 点
**位置**：§3.6 L456–463；App. B L610–618；App. D（traps）L637–639。
**会怎么失分**："你说 n≥2 时 coverage 回到 nominal 附近（还 over-cover 7 点），又说 calibration 里混入 training view 会让 coverage 掉到 0.822–0.894。如果 re-calibration 的样本量这么无所谓，为什么 composition 这么有所谓？两件事的答案其实是同一个（exchangeability 而不是样本量），但论文没有把它讲清楚，读者会读到矛盾。" 另外 App. B 自己承认"the repair is not informative about the asset"，那它为什么值得占一个贡献条目（贡献 5 的 'price of repair'）？需要把"width 才是信息载体"这层说得更硬。
**最小修法**：把 §3.6 重写成"validity 的恢复是构造性的（n≥2 即回归 nominal，over-cover 随 n 减小），因此不是发现；发现是 width：q 涨 53–122%（paired），且这个涨幅与 edit 强度单调"。把"2 views suffice"从贡献里降级到 appendix。`[离线可改]`。

#### M6. 摘要/贡献与 §3.4 自相矛盾；"ordering reverses" 在 treehill 上不成立
**位置**：摘要 L36–41；贡献 3/4；§3.4 L375–377（只举 bicycle 与 flowers）；§3.4 L385–388（"A claim of the form 'coverage under-reports damage by a factor of k' is therefore not well posed"）vs 摘要 "the choice of task moves the answer by a factor of seven"。
**事实**：50% 处 coverage vs task：bicycle −4.9 vs −3.1/−3.5/−1.8（反转）、flowers −3.6 vs −2.4/−2.3（反转）、stump −7.4 vs −1.9（反转）、**treehill −6.1 vs −12.1（不反转）**。所以 "the ordering reverses at a milder prune" 是无条件写的，实际 3/4。
**会怎么失分**："你在 §3.4 花了整整一段论证 'factor of k 的说法 not well posed'，然后在摘要和第 3.5 节用 factor of seven 当卖点。审稿人会要求你二选一。" 加上 "ordering reverses" 只举两个场景，第三个场景（treehill）反例被省略。
**最小修法**：摘要改成 "the ordering reverses on three of four assets at 50% pruning"，并把 factor-of-seven 限定量化（"for this specific registration front-end and operating point"）；或者删掉 §3.4 那段"not well posed"的强断言，改成"the ratio is not a stable constant"。`[离线可改]`。

### MINOR

| # | 位置 | 问题 | 修法 |
|---|---|---|---|
| m1 | §3.2 L262–264 | "perturbs the SH coefficients by 3.4–4.1×10⁻⁴ … **three orders of magnitude** below the residual"：3.4e-4 / 0.0258 ≈ 1.3×10⁻²，是**两个**数量级 | 改 "two orders"；`[离线可改]` |
| m2 | §3.2 caption / L462 | 8-bit SH 被称作 "an **exact** no-op"，正文同一段说它扰动了 SH 系数 3.4e-4，而 v55 旧实验里同一"no-op"的 width growth 是 2.2–12.1%（treehill 甚至 −18%）。"exact" 是过度断言，也是 noise floor 论证的弱点 | 改 "an approximate no-op (perturbation 3.4–4.1×10⁻⁴)"，并注明 noise floor 只对 pixel 粒度成立（block 粒度下 quant8 的 q growth CI 约为 ±0.1%）；`[离线可改]` |
| m3 | Fig. 1 (`fig_dose.pdf`) | 面板 (a) 标题与面板 (b) 标题在 0.95\linewidth 下相撞（"budget)" 压在 "(b)" 上）；(b) 纵轴无单位（数值是 %）；两面板重复 legend | 缩到 0.85\linewidth 或改成单栏元素；纵轴改 "conformal quantile growth (%)"；`[离线可改]` |
| m4 | Fig. 2 (`fig_three.pdf`) | 纵轴标签 "drop from fresh asset (points)" 顶部被裁；三根柱没有任何不确定性（Table 5 有 CI） | 加 `bbox_inches='tight'` 重导出；给 registration 与 coverage 也画 CI（数据都有）；`[离线可改]` |
| m5 | App. B L613–616 | "within three points of nominal … (0.882–0.971)" 与括号内 0.971（+7.1 点）矛盾 | 见 B5 修法；`[离线可改]` |
| m6 | App. A L602–608 | voxel 数字来自 `results_v60`（voxel clean coverage 0.894–0.896），却与 `results_v70` 的 norm_gt 百分比并列；跨战役比较没有说明；且"blocks sit between the two"在 2/4 场景不成立（block 比 pixel 更敏感） | 说明数据来源，或统一到同一战役；改 "sits between" 那句；`[离线可改]` |
| m7 | App. C L623–627 | "a released checkpoint compacted to 200k primitives and fine-tuned shows −10.3 to −12.9 points"：我在 `results_v61/v62` 里找不到这组数（200k no-finetune 是 +5.5…+15.4；`bonsai_ft` +3.9、`garden_ft` +17.8、`kitchen_ft` +4.6、`room_ft` +1.1）；"+3.2" 用了 room 的另一行 clean 值 | 指向具体 artifact 字段，或删除该句；**未核实** |
| m8 | §2 L116–118 | "cameras are sorted by image name, every eighth is a test view (22 on flowers, 18 on treehill)" 与 Mip-NeRF 360 官方图像数（164 / 150）不符（every-eighth 应得 21 / 19；bicycle 25 / stump 16 是对的）。若 test split 与 archive 发布的不同，则"archive 自己报 25.2 dB"这个比较不可比 | 说明 split 的来源（是否 `test_poses`），或直接给出可比数字；**未核实** |
| m9 | Supplement | `results_v70/battery_*.json` 与 `diag_*.json`（所有表的一级来源）在 supplement 里**没有生成脚本**，只有消费者（`check/make_tables_v70.py`、`check/verify_tex_v3.py`）；它们的生产脚本是工作区里的 `experiments/node_diag.py` 等，未随包发布。Reproducibility statement 说"the rendering pass and the 400-split analysis are each a single command"，但找不到那条命令 | 打包 `node_diag.py` / battery 生成脚本；`[离线可改]` |

---

## 5. 六个特别检查点的明确回答

**① Table 1 的 treehill 9.4 dB 会不会被质疑整条测量链？—— 会，而且这是我认为最容易被真审稿人一击致命的地方。**
不只是"这个场景太弱"，而是三重可验证的疑点：(a) 残差剖面（median 0.031 / rms 0.338）对应"约 11% 像素全错"，与论文给的"brightness offset"机制不符；(b) "no protocol repairs" 与作者自己的 `gain` 臂（9.4 → 16.5 dB）直接冲突；(c) 四个工作点都比同资产公开数字低 2.7–13.1 dB，且是在 1/4 分辨率下（本应更高）。审稿人的标准动作会是："先证明你的渲染链能在至少一个场景上复现 archive 的数字，否则所有 coverage 数字都是关于你的 renderer 而不是关于资产。" 这一条**必须**在 revision 里解决，且解决方式不是删掉 treehill（那会同时删掉 36/36 这个卖点），而是解释它 + 把机制说清楚。

**② "attenuation 2.4×" 是否被 Table 3 四行完全支撑？—— 作为"最大值"是，作为"现象"不是。**
四行比率 0.84 / **1.01** / 0.42 / 0.85：flowers 是 1.01×，即**完全没有** attenuation；真正 >2× 只有 stump 一行。摘要用 "up to 2.4×" 在字面上成立，但读者会读成"系统性地 attenuate 约 2×"，而正文自己的区间是 0.42–1.01×。更严重的是：作者自己的 `norm_both` / `gain` 两臂（同一 JSON）下比率是 1.03–1.17× 与 0.86–1.57×，attenuation 消失。所以这条 claim 现在既被自己的一行（1.01×）削弱，也被自己未报的两臂证伪。**结论：不成立，需重写（B2）。**

**③ 36 格扫描的统计口径：每格独立吗？多重比较？—— 既不独立，也没有做任何 multiplicity 处理。**
36 = 3 个 `(patch, search)` 配置 × 12 个 `(tolerance, peak)` 单元。12 个单元是同一批残差上的嵌套阈值（peak 0.3 < 0.45 < 0.6 < 0.75，tol 1 < 2 < 4），因此覆盖率随单元单调、彼此完全相关；3 个配置是同一渲染集上的近似重复（我重算：bicycle 三个配置各自恰好 6/12，treehill 各自 12/12）。所以有效独立单元≈1（每个 scene 一个符号），"36/36" 的说法把一次观测放大成 36 次。另外这一列没有任何区间（clean 与 pruned 共用同一渲染集，差值本身是确定性的），所以也无从谈显著性。**修法：见 M1。**

**④ 第二任务只有 2 场景、单一 RANSAC 模型，够不够？—— 不够。**
三个具体缺口：(a) 场景数 2（且都是同一 archive、同一分辨率），无法支持"task choice moves the answer"这种族级断言；(b) translation-only + ±8 px，而两幅图来自**同一相机位姿**，模型近乎退化，clean 端 inlier ratio 已到 0.927/0.829（per-view 值大量为 1.0），存在天花板效应；(c) 操作点不对称——local task 有 12 格扫描，registration 只有 1 格，因此"factor of seven"里有多少是 task 差异、有多少是操作点选择，无法分离。补充一点：这个 registration 结果若用**相对**损失看是 4.2% vs 30%（仍然 7×），所以不是纯粹的天花板伪影——但这一点论文没有说，反而让读者更容易误判。

**⑤ 摘要里的每个数字是否都能在表里找到？—— 数字都能，但有 3 个必须加限定。**
逐项核过（详见 §6）：10.8–27.7 ✔（Table 1）、53–122% ✔（Table 1）、3.3 点与 0 点 ✔（Table 2）、"nearly sevenfold" ✔（Table 3，但只是 median）、"2.4×" ✔（Table 3 最大值，见 ②）、27.3 vs 22.1 ✔（Table 4/5）、0–36/36 ✔（Table 4）、3.9 vs 27.3 与 7× ✔（Table 5）。缺的三件事：(i) 所有 coverage 数字没标 granularity（pixel-only）；(ii) 没标 ground-truth convention；(iii) "the ordering reverses at a milder prune"（3/4 场景）与 "factor of seven" 是无条件表述，与正文 §3.4 自相矛盾（M6）。

**⑥ 有没有残留的防御性写作或过度断言？—— 防御性写作基本清干净了，剩下的是"过度断言"这一侧，共 6 处值得删/降。**
1. "This is a threshold effect, and the measurements above are its direct signature."（§3.4 末）——机制是**断言**的：全文没有测量"距离阈值的远近"，也没有 conditional coverage。建议改成 "is consistent with a threshold effect"。
2. "treehill is the weakest asset in the archive … and shows the same qualitative behaviour, **which is reassuring**"（§3.1）——一个自己都说渲染坏了的资产不能提供 reassurance；这句会招来"你在用一个坏场景给结论背书"。
3. 标题 "Valid but Unusable" 与主现象（invalid）错位（§3 第 2 点）。
4. "This validates the protocol and the implementation"（§3.1）——见 M4。
5. "Every number in this paper is re-derived … with one assertion per reported value"（Reproducibility）——有 4 处反例（B5）。
6. "a brightness offset … that **no protocol** repairs"（§3.1、§5）——只对 label-free 成立（B1）。
另外还有一处"隐性防御"：`The matcher is deliberately simple so that the number measures the render, not the matcher`——这句本身合理，但它回避了一个真问题：一个 NCC patch matcher 与任何真实下游任务（VO / SfM / 检测）的关系没有被验证过，而论文的第三条主结论完全建立在这条代理上。建议加一句明确的"external validity"限定，而不是用"deliberately simple"来自我保护。

---

## 6. 五个数字的独立核对（含方法与结论）

**方法**：用 `python 3.12 + numpy` 直接读 `D:\3dsg_1\results_v70\*.json` 重算；`n_eff` 用 σ=(hi−lo)/3.92 反推再 n_eff=p(1−p)/σ²；registration 的区间用 `second_task.json` 的 `per_view` 数组做 view-level paired bootstrap（20,000 次，percentile 法）。未采信论文或作者 verifier 的任何中间结果。

| # | 论文数字 | 位置 | 我从 artifact 重算 | 结论 |
|---|---|---|---|---|
| 1 | bicycle fresh cov 0.898；30% drop −22.1 [−25.2, −18.8] | Table 1 | clean 0.8984；drop −22.08，[−25.18, −18.81] | **一致** |
| 2 | stump PSNR 23.9（captured）/ 13.9（normalised） | Table 3 | `diag_stump`：raw 23.902 / norm_gt 13.858 | **一致** |
| 3 | bicycle 30% 行：0.626(−27.3)、0.615(−26.5)、0.664(−26.4) | Table 4 | `task_sweep[tol2_peak0.6]`：0.6264/−27.33、0.6148/−26.47、0.6636/−26.40 | **一致**（含一行 rounding：flowers 应为 −11.1 而非 −11.0） |
| 4 | bicycle registration −3.9 [−5.1, −2.7]（及 10% 的 −31.1 [−33.9, −28.1]） | Table 5 | 点估 −3.89；paired bootstrap [−5.12, −2.75]。10%：−31.13，[−33.88, −28.07] | **一致** |
| 5 | n_eff 77–508 | §2 | 77.0（treehill）/115.5（stump）/182.0（bicycle）/507.6（flowers） | **一致** |

**顺带核到的不一致（都不是这 5 个，但同样在正文里）**：
- flowers@50% coverage drop：正文 2.4 vs Table 2 / `battery_flowers` 的 **3.58**（2.4 是 task loss）。
- §3.7 的 0.768–0.864 与 30% 口径不符（B5）。
- Table 4 flowers s32 30% 的 (−11.0) vs Table 5 的 −11.1（raw −11.06）。
- App. B "within three points（0.882–0.971）"。
- Table 1 与 Table 2 的 block 列全部正确（我逐格核过 24 个 block/q-growth 值，均一致），说明"表内数字"这一层是可靠的——**问题集中在散文数字与统计口径，而不是表格本身**。

---

## 7. 如果要 accept，必须改到什么程度

假定作者选择修订后重投（TMLR 机制下这通常是新投稿），我会按下面顺序要求：

**A. 必做，且大多离线可改（1–3 天工作量，数据全在 `results_v70`）**
1. **报三个已存在的对照臂**：`gain` 与 `norm_both`（表 3），`pup30`（表 2 或新小表）。没有这三列，三条主结论都不能用现在的措辞。
2. **Setup 写明 pruning criterion**，Limitations 删掉"未测量 pruning criteria"那句。
3. **重写 §3.3**：承认 `norm_gt` 是病态的 label-free 预处理，把结论从"convention 值得 2.4×"改成"label-free 口径的每一种选择都在改变量级；标准（label-using）口径会恢复它，因此不能用于 certificate"。顺带把 label 泄漏这条限制写清楚——这是论文可以贡献的一个方法论点，现在完全没提。
4. **用 v70 重算 §3.7**，并把"0.768–0.864 / 3.6–13.2"改成四场景的 0.6215–0.7921 / 12.2–27.8。
5. **改散文数字**（3.6、−11.1、App. B、App. D），并把 verifier 扩到散文。
6. **摘要与贡献加口径标注**（granularity、convention），把 "ordering reverses" 改成 3/4，把 "factor of seven" 加上操作点限定。
7. **Table 1 给 fresh coverage 区间**；把 "correct/validates" 降级为 "consistent with nominal"。
8. **把 36 格拆开报**（12 格/配置），删掉 "in all 36" 的稳健性修辞。
9. **修 Fig. 1 / Fig. 2 的两处排版缺陷**；把 SH 3→1 的 PSNR 反常（四场景全变好）从"解释成 smoothing"改成"这是证书与图像指标脱钩的又一个证据"。
10. **打包 `node_diag.py` 与 battery 生成脚本**，让"single command"名副其实。

**B. 必做，但需要新测量（工作量中等）**
11. **treehill 的机制**：一张 per-view residual map / 直方图（证明是长尾饱和而非 brightness offset）。若确实是渲染链问题（例如 SH 高阶项的处理与参考实现不一致——注意四个场景 SH 3→1 后 PSNR **全部上升**，这本身是一个需要排除的签名），必须修好再报。
12. **pup30 在 raw 口径下重跑**（四场景，一次 prune+render）。
13. **registration 端补一个阈值扫描**，让两个 task 的操作点对称。

**C. 强烈建议（决定这篇稿子是"一个测量"还是"一个论点"）**
14. 把 §3.4 的"coverage 不跟踪 utility"升级为**有条件覆盖（Mondrian / 按 view 或按区域分组）的失败**，并给一个形式化命题（edit 后 coverage 偏差的可达界）。现在这一节停留在"我们测到两个量不同调"，这也是它最容易被判为 incremental 的原因。
15. 若有可能，实例化 AURA 那类 per-carrier bound，让标题的"certificates"复数站得住。

**做完 A+B 我会重新考虑；只做 A 我仍然会给 reject，因为 B1（测量链）与 B3（criterion 依赖性）触及结论本身。**

---

## 8. 未核实 / 我无法从现有材料判断的事项

1. `App. C` 的 "compacted to 200k + fine-tuned shows −10.3 to −12.9 points" 对应的 artifact 我没找到（`results_v61/v62` 里找不到这组数）；可能来自 `research/results_v*` 的更早战役，但我没有在该目录逐文件穷举，故标 **未核实**。
2. test split 的构成（"every eighth" 得到 flowers 22 / treehill 18）与 Mip-NeRF 360 官方图像数不符；需要作者说明 archive 的实际图像数与 split 来源。我未读到 archive 的文件清单，故 **未核实**。
3. App. A 的 voxel 数字与 `results_v60` 的对应关系（voxel clean coverage 0.894–0.896 vs 主表 0.899–0.902），是否同一 GT 口径，**未核实**。
4. `experiments/node_diag.py`（`diag_*.json` 的生产者）不在 supplement 里，我是在工作区读到它的；作者是否打算随包发布，**未核实**。
5. 我没有复现渲染（无 GPU/archive），因此"渲染链是否与参考实现一致"这一判断是基于 PSNR 差距、SH 高阶项反常、残差剖面三者的**间接**推断，不是端到端复现。这一点在 B1 里已按间接证据的强度措辞。
6. B1 里引用的 flowers/treehill/stump 公开 PSNR（≈21.5/22.5/26.6 dB）来自 3DGS 原文的 Mip-NeRF 360 表，是我按记忆给出的**参考量级**，没有在本地 archive 的 eval 输出里核对；bicycle 的 25.2 dB / 0.756 SSIM 是论文自己在 §2 引用的 archive 数字。审稿意见里这一条只用来指出"系统性差距"，不依赖其精确值。
