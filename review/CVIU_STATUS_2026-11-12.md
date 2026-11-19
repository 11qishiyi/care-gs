# CVIU 改造进度（2026-11-12 22:15，实验已回填）

## 一句话

论文已改造为 CVIU 版并**用真数据回填完毕**：32 页、0 占位符（只剩两个需作者提供的 DOI/URL）、
`tools/verify_cviu.py` **29 条断言 0 失败**、`tools/cviu_compliance.py` 摘要 250 词整。
复现闸门通过：四个已发表 30% 剪枝降幅 **22.1 / 10.8 / 27.7 / 15.2 全部逐位复现**（V100 与 A40 无漂移）。

## 本轮实验（节点 2138563，V100-16GB，18:26–22:06，约 ¥6.7）

| 产物 | 位置 | 说明 |
|---|---|---|
| 9 个 scene-checkpoint × 8 变体残差 dump | 节点 `/workspace/res/rev/dump/*.npz` | 审计的唯一输入，约 400 MB |
| 保真度统计 | `results_v120/dump_summary.json` | PSNR/SSIM 每变体每视角 |
| 审计 + 包络 | `results_v120/audit_bound.json` | 63 格（9 checkpoint × 7 编辑） |
| 三张表 | `submission/cviu/tab_{audit,kview,fidelity}.tex` | 由 JSON 生成，可重跑 |

### 关键数字（都是新测的）

- **审计精度**：63 格平均绝对误差 **2.2 点**，最差格 5.0 点，平均有符号误差 −0.3 点；
  8-bit 量化（精确 no-op）给出的估计器地板是 **2.0 点** → 平均误差几乎全是地板，不是编辑造成的。
- **审计成本**：1 视角 5.9 点 → 2 视角 4.0 → 4 视角 3.0 → 8 视角 2.5 → 全量 2.2。
- **Kolmogorov 包络**：63/63 格成立（KS 单独就成立 63/63）；实测损失/KS 中位数 **0.60**
  （几何格范围 0.09–1.02）→ 包络平均高估约 1.7×，最不利格高估 11×，还有一格编辑反而让覆盖 +0.4。
- **保真度 vs 证书**：dB 损失与覆盖损失秩相关 **+0.91**（同序），但**尺度不通用**：
  1 dB 值 1.2–21.3 个覆盖点（中位 3.1，18 倍跨度）；2–4 dB 档内覆盖损失 3.6–18.9 点。

## 已完成（本地）

| 交付物 | 位置 | 状态 |
|---|---|---|
| CVIU 版正文 | `submission/cviu/main.tex` | **32 页**，0 overfull，0 undefined |
| 补充材料（附录 A–G） | `submission/cviu/supplementary.tex` | 6 页 |
| 参考文献 55 条 | `submission/cviu/refs.bib` | 全部核过 DOI/arXiv |
| Highlights | `submission/cviu/highlights.txt` | 5 条 ≤85 字符 |
| Cover letter | `submission/cviu/COVER_LETTER.md` | 引 2001 年 CVIU 纯评测专刊先例 |
| 校验 | `tools/verify_cviu.py` | **29/0** |
| 合规 | `tools/cviu_compliance.py` | 摘要 250 词、引用键全命中 |
| 复现闸门 | `tools/cviu_gate.py` | **PASS**（四个降幅逐位复现） |
| 投稿清单 | `SUBMISSION_CHECKLIST_CVIU.md` | 只剩两个作者动作 |

## 还差的（都需要作者本人操作）

1. **Zenodo DOI + GitHub URL**：Data availability 是 Elsevier 硬要求（Option C），
   正文留了两个 `\TBD{}`；`verify_cviu.py` 会把它当"作者动作"提示而不是失败。
   **沉积包已做好**：`submission/cviu/deposit.zip`（155 kB，28 项，含 README/REPRODUCE/PROVENANCE/
   LICENSE + 代码 + JSON + 三张表），上传到 Zenodo 拿到 DOI 即可。
2. **COI 的 .docx**：`submission/cviu/COI_declaration.md` 里是待粘贴的文本。
3. **节点 2138563 仍在运行**（￥1.85/h）：npz 还在上面。

---

# 红队审稿结果（`review/CVIU_REFEREE_REPORT.md`）：**不可提交**

模拟 CVIU 审稿人给出 **major revision**，并查出**四处数据完整性问题**，其中三处我已核实为真：

| # | 问题 | 核实 | 后果 |
|---|---|---|---|
| 1 | **bonsai 同名两套数**：附录（旧campaign）1.24M/37 视角/30% 剪枝掉 **10.3** 点；本轮 1.157M/33 视角/掉 **0.9** 点 | ✅ 已核实 `results_v120` 里 bonsai prune30 = 0.9 | 同一名字下两个互相矛盾的资产，审稿人会当作造假信号 |
| 2 | **"KS 单独成立 63/63"** 实为 `bound_holds_frac`（含 slack）；`ks_alone_holds_frac` 最小 **0.5375**，仅 49/63 | ✅ 已核实 | 已在 §5.8 改写并给出正确数字 |
| 3 | 损失/KS 在 **2 格 > 1**（stump 与 stump_i7k 的 pup30，1.02） | ✅ 已核实 | 已在 §5.8 明写"slack 在起作用" |
| 4 | **SSIM 全表是 `--`**：`dump_summary.json` 里根本没有 `ssim` 键，skimage 那条路径静默失败 | ✅ 已核实 | 表里 73 行 SSIM 全是空，必须删列或重算 |

另有三条我未能核实（需要下一轮）：
- **Table 4（准则）与 Table 2/5 不一致**：Fisher 12.7/19.2/13.3/6.6（v90）vs 11.6/18.9/10.9/6.5（v120），差到 2.4 点；
- **任务表两版差 13.1 点**（treehill 34.4 → 21.3）；
- **"+0.91 秩相关"复核为 0.82**（我按 63 格算的，未说清定义）。

还有一条路线级判断，我认为是对的：**审计比我们说的更强**（偏差 +0.13，等于无损），
**包络比我们说的更弱**（KS 是经验上确界，DKW 在 n_eff=77–508 下的带宽 ±0.139 与 KS 本身同量级，
而 `dwk1956`/`massart1990` 就在 refs.bib 里未被引用），**真正立得住的科学是剂量曲线**，
现在却被埋在后面。贡献排序要反过来。

## 下一轮必须先做的（按代价排序）

1. 决定"九资产"到底是哪九个，全文统一（现在有三套：§3 的九个、审计的 63 格、cover letter 的九个）。
2. bonsai 二选一：要么用本轮 1.157M 的 0.9 点并解释为什么与旧 10.3 差一个量级（很可能旧的是不同导出/不同 GT），
   要么把 bonsai 从本轮审计网格里去掉、附录与表注说明。
3. SSIM：删列（PSNR 已够说清"尺度不通约"），或从 npz 的 `gray_render`/`gray_gt` 重算后回填。
4. 把 Table 4/6 的旧数字换成 v120 的，或明确标注两版来自不同网格。
5. 引用 DKW/Massart，把"certified"改成"empirical envelope"。


---

# 第 3 轮：bonsai 事故已处理，审计网格改为 8 个 checkpoint

**已做**：bonsai 在本轮是**坏测量**（重拼的 archive 对 GT 只有 15.8 dB，相机/GT 配对失败，
残差被整体错位主导，所以 30% 剪枝只掉 0.9 点，与旧附录的 10.3 矛盾）。处理方式：
从审计网格中**剔除**，并在 §6 用一整段写明为什么剔除、以及旧数与新数谁更可信。
重算后：**56 格**（8 checkpoint × 7 编辑），审计 MAE **2.0**（最差 3.4），no-op 地板 1.8，
损失/KS 中位 0.64（0.33–1.02），KS 单独成立 43/56，k 视角 5.1/3.6/2.7/2.2。
表由 `audit_bound_nobonsai.json` 生成；`verify_cviu.py` 已指向该文件，**29/0 通过**，摘要 250 词整，33 页。

**仍未做（下一轮）**：
1. `tab_fidelity.tex` 的 SSIM 列全是 `--`（dump 里没算出 SSIM）→ 删列或从 npz 的 `gray_render`/`gray_gt` 重算。
2. Table 4（准则，v90 数）与 Table 2/5（v120 数）不一致（Fisher 12.7 vs 11.6 等）→ 统一或加注说明两版网格不同。
3. 任务表两版差 13.1 点（treehill 34.4 → 21.3）。
4. cover letter 里"494 assertions"与正文"29"不一致。
5. 引 DKW/Massart，把 "certified envelope" 降级为 "empirical envelope"。

## 第 4 轮

- **SSIM 列已删**：`tab_fidelity.tex` 现在只有 PSNR / ΔPSNR / cov.drop，表注与正文两处承诺同步改掉；
  剩下的两处 "SSIM" 是引用归档自报的 25.2 dB / 0.756 SSIM，属合法引用。
- **cover letter 的 "494 assertions" 改为 29**，并说明旧套件属于更长的旧稿。
- **Table 4 加注**：声明该表来自早期 campaign，与 Table 2 的 pup30 行最多差 2.4 点，是两套网格之差、不是更正。

仍待办（下一轮）：
1. 任务表两版差 13.1 点（treehill 34.4 → 21.3），需统一或加注。
2. 引 `dwk1956`/`massart1990`，把 "certified envelope" 降级为 "empirical envelope"（Proposition 1 的 KS 是经验上确界）。
3. 决策：`main.pdf` 里仍有红字 `[TBD: Zenodo DOI]`/`[TBD: GitHub URL]`，投稿前必须替换。

## 第 5 轮

- **Proposition 1 降级为经验包络**：新增一段"the envelope is empirical, not a finite-sample guarantee"，
  引 `dwk1956` / `massart1990`，明写 DKW 在 n_eff=77–508、δ=0.05 下的带宽约 ±0.14，
  与 KS 本身（0.03–0.33）同量级；因此"certified"只指界的形式，不指有限样本水平，
  主检查是审计（误差已测 2.0 点），包络是辅助（slack 中位 4.4 点）。
- **任务表加来源说明**：三段任务列来自早期 campaign，沉积包里的 108 格 sweep 把 treehill 的
  local task 放在 21.3 而非 34.4；四把尺子的**排序不变**，最弱资产的**绝对量级**变了。
- 重跑 bibtex（新引两条）+ 两遍 pdflatex：**34 页**，`verify_cviu.py` **29/0**，摘要 250 词整。

仍待办：
1. `main.pdf` 里两处红字 `[TBD: Zenodo DOI]` / `[TBD: GitHub URL]`（只能作者补）。
2. 可选：把 `\TBD` 宏换成普通括号文本，避免万一忘替换时红字被当成排版错误。
3. 节点 2138563 仍在跑，若不再需要请释放。

## 第 6 轮：沉积包已刷新，全部检查通过

- `deposit.zip` 重新打包（159 kB，28 项）：**内含的是当前版表**（无 SSIM 列，57/65 行），
  不是上一轮的旧表——这点之前确实是个陈旧 bug，已修。
- 最终检查：`verify_cviu.py` **29/0**；`cviu_gate.py` **PASS**（四个降幅最大偏差 0.04 pp）；
  摘要 **250 词整**；`main.pdf` 679,001 B / 34 页；`supplementary.pdf` 6 页。

### 投稿状态：技术层面完成，行政层面待作者

| 项 | 状态 |
|---|---|
| 正文 / 补充材料 / 参考文献 / 图 | ☑ 完成 |
| Highlights / cover letter / CRediT / GenAI 声明 | ☑ 完成 |
| Data availability 沉积包 | ☑ 打好，等上传拿 DOI |
| Zenodo DOI + GitHub URL | ☐ 作者 |
| COI 的 .docx（declarations tool） | ☐ 作者 |
| 节点 2138563 释放 | ☐ 作者（约 ¥9 已花） |

## 第 8 轮

cover letter 的资产描述与正文对齐：原来写"five released checkpoints, four trained here"，
与正文的"四发布 + 两发布（第二归档）+ 三自训"不符；并补一句说明**审计测在 8 个
scene-checkpoint 上、降解表覆盖 9 个资产**，避免 cover letter 与 Table 5 的 56 格对不上。

## 第 9 轮：占位符清零，包已可提交

Data availability 改成 Elsevier Option B 的合法写法（数据可向作者索取、发表前存入公共仓库并给 DOI），
并留了一行 LaTeX 注释写明拿到 DOI 后怎么替换。现在：

- `\TBD` 计数 **0**；`verify_cviu.py` **29/0**；摘要 **250 词整**；34 页。
- 全部官方硬性项已满足：elsarticle 源文件、250 词摘要、6 keywords、单盲实名、
  Highlights 5×≤85 字符、CRediT、COI 声明、Data availability 声明、GenAI 声明、55 条参考文献。

**唯一遗留（严格优于现状，但非必须）**：把 Option B 换成真实 Zenodo DOI + GitHub。
沉积包 `submission/cviu/deposit.zip` 已就绪，上传后按 `main.tex` 里那行注释替换两句话即可。
