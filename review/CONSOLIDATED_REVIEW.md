# TMLR 审稿意见（合并版）

> 稿件：*Certificates Do Not Survive Editing: A Measurement Study of Quality Guarantees for 3D Gaussian Splatting Assets*
> 版本：`submission/main.tex`（8 页，正文 6 页，3 图 5 表），`submission/main.pdf`
> 评审构成：Reviewer 1（conformal / 统计，`review/reviewer_stats.md`）＋ Reviewer 2（3DGS / 可信 ML / 定位，`review/reviewer_domain.md`）＋ 第三方证据审计（`review/audit_report.md`，逐数复核 229 条断言）＋ Lead 复核（`review/TMLR_REVIEW_v1.md`）
> 日期：2026-11-10

---

## 0. 判定

| 条目 | 结论 |
|---|---|
| TMLR 标准 #1：claims supported by accurate and convincing evidence | **No** —— 不是"实验不够"，而是**主张与它所引证据不是同一个量**（3 处系统性错配），且核心主张在已测的第二种编辑强度下方向反转 |
| TMLR 标准 #2：audience interest + clarity | **Borderline** —— 问题真、受众在，但标题把最不新颖的一半放在最前面，把最有趣的一半藏在摘要第二段 |
| 决定 | **Reject（当前形态）**；三位评审一致认为这是一篇**可救**的稿件，且都不主张加新方法/加场景 |
| 独立复现的一致性 | 三位评审**独立**发现了同一个头号问题（粒度混用），说明它不是误读，而是稿件层面的缺陷 |

**一句话**：这篇论文的**方法学骨架是好的**（400 划分 + 配对、fresh coverage 命中名义值、负结果诚实），但**它现在的头号数字是错的**，而且**它最想说的那句话被放错了位置**。修好这两件事，它可以是一篇 TMLR 会收的测量论文。

---

## 1. Summary（作者做了什么）

作者测量 split-conformal 质量证书在 3DGS 资产被编辑后是否仍然成立。协议：9 个场景（4 个官方发布 checkpoint + 5 个自训），每个留出视角渲染一次，再做 400 次随机 calibration/deployment 划分，报告覆盖率与配对降幅。结论三层：

1. 几何编辑（按不透明度剪到 30%）使覆盖率从名义 0.90 掉 10.9–18.6 个点；SH 阶数下降掉 0.2–2.0；8-bit SH 量化掉 0.00。
2. **头号主张**：覆盖率这个指标低估实际损失——覆盖率只掉 4.6 点，补丁重定位任务掉 16.8 点，四场景低估倍数 1.9–12.1×。
3. 三条实践规则 + 一个负面结果（用标定集自检是循环论证）。

写作上有一个值得肯定的决定：Table 1 把"主张—证据—反驳条件"并排列出，让评审可以逐条判定。

---

## 2. Claim-by-claim 证据核对

Lead 与审计员各自用 `research/results_v*/` 的原始 JSON 重算（`review/verify_claims.py`、`tools/verify_tex_numbers.py`：229 断言 / 188 MATCH / 19 MISMATCH / 22 NO_SOURCE）。

| # | 主张（tex 行） | 判定 | 依据 |
|---|---|---|---|
| C1 | Fresh 证书有效：0.894–0.901 vs 名义 0.900（L176–179） | **Yes（但近乎同义）** | 400 划分均值复算全对。注意自训场景 garden 是 0.956（高出名义 5.6 点，区间排除 0.9），全文未提。 |
| C2 | 剪 30% 掉 10.9–18.6pp，区间排除零（L159–162） | **Yes** | `many_splits.json`：−10.90/−18.57/−12.82/−11.69 逐位吻合。**但区间不是置信区间**（见 M4）。 |
| C3 | SH 3→1 掉 0.2–2.0；8-bit 掉 0.00（L201–202） | **No（符号错）** | 实测 bicycle/treehill/stump 是 **+1.02/+0.20/+1.00pp**（覆盖率上升，CI 在 0 以上），表里印成 −1.0/−0.2/−1.0；flowers 的 −2.0 与 quant8 的 0.00 无 artifact（`results_v53/edit_families.json` 是 0 字节）。 |
| C4 | **证书低估下游损失 1.9–12.1×**（摘要 L32–35、§3.3 L260–262、Table 4 L236） | **No** | 分子是**像素级**任务命中率，分母是**3D 体素级**覆盖率降幅。同粒度重算 = **1.02 / 1.16 / 2.47 / 1.54×**（1.0–2.5×），stump 上"低估"已不存在（11.7 vs 11.9）。Table 4 列名丢了 "3D voxel" 限定（作者自己的 markdown 版 L114 记得写）。 |
| C5 | 重签 2–4 视角可修复，代价 26–71% 更宽区间（摘要 L36–38、§3.4 L310–316） | **No** | ① n=all 列被删，而 flowers 0.8915 / bicycle 0.8764 **低于**名义值；四场景全部 coverage(n=2) > coverage(n=all)，"2–4 视角修复"其实是小样本分位数的保守过覆盖。② 26–71% 的 clean q 取自**第 0 次划分的单个值**、edited q 取 400 次划分**均值**（估计量错配），噪声地板达 ±18%（8-bit 量化这个"免费"编辑读出 +2.2/−18.1/+12.1/+0.4%，treehill 的 SH 截断让 q 掉 17%，物理不可能）。③ 两个数字不是同一 n 下的配置。 |
| C6 | 自检返回 0.900 而真值 0.768–0.864，高估 3.6–13.2 点（L335–337） | **Partially** | 数据只有 **2 个场景 × 2 个编辑强度**（`results_v58/selfcheck.json`），正文 4 个数字读起来像 4 个场景。且"自检"是恒等式（≡ 1−α），而被反驳的 §3.5（q 漂移）恰恰是可以用的 label-free 检测量——两节互相拆台。 |

---

## 3. BLOCKER（不解决就是 Reject）

### B1. 头号数字由两种统计粒度拼出来；Table 4 与 Table 2 对同一编辑给出互相矛盾的覆盖率降幅
Table 2 剪 30% 是 **像素级** −10.9/−18.6/−12.8/−11.7；Table 4 的 "Certificate drop" 是 **世界坐标体素级** −4.6/−6.1/−2.6/−6.1（`results_v60/vt_*.json` 字段 `voxel_prune30_drop_mean`）。同一场景、同一编辑、同一资产，两表相差 1.9–4.9×，全文没有一句话解释。图 fig9 的图例诚实写了 "3D voxel"，**表头、正文、摘要都丢了**。
→ 审稿人 30 秒内会写下："the two main tables report incompatible numbers for the same quantity"。
**修法**：Table 4 改三列（pixel / voxel / task），摘要头号数字只用同粒度比较并注明粒度。

### B2. 剪 50% 时方向反转，而这一档数据早就有、论文没写
| 场景 | 剪 50% 任务损失 | 剪 50% 像素覆盖率损失 | 判定 |
|---|---:|---:|---|
| flowers | −1.8 | −3.6 | 任务损失**更小** |
| bicycle | −2.8 | −5.4 | 任务损失**更小** |
| treehill | −11.7 | −4.5 | 任务损失更大 |
| stump | **+0.6（变好）** | −2.1 | 任务损失**更小** |
"证书指标系统性低估损失"在 3/4 场景的这一档上是反的，其中一档任务还变好了。审稿人自己算出来会认定为选择性报告。
**修法**：把两档都进主表，把主张从"低估 N 倍"改成**"覆盖率与任务效用不同调"**——方向不一致本身才是发现，而且更难被反驳。

### B3. §2 对覆盖率的定义与实现不符
原文（L132–137）："Coverage is a view-level quantity: the effective sample size is the number of views (16–25), not the number of pixels." 实现（`many_splits.py`）：`q = 分位数(cal 全部像素展平)`，`coverage = (dep 像素 ≤ q).mean()` —— **像素级比例**，视角只在重采样层面是单位。摘要又写成第三种说法（"the rendering error on a held-out view"）。
**附带机会**：按像素独立算，10⁶ 像素上 0.9 的抽样标准差是 3×10⁻⁴，实测划分间标准差 0.018–0.040；用 n_eff = p(1−p)/sd² 反推，**有效独立分数只有 56–277 个**——这恰好证明作者"方差由视角决定"的直觉是对的，只是写错了。把这套论证写进 §2，既修了定义，又白得一个亮点。

### B4. 下游证据只有一个任务、阈值自选，而论文自己列的反驳条件没做
Table 1 明写这条主张 "would be refuted if ... **the gap disappears once the task threshold is varied**"（L101–103），全文没做。tol=2px、peak≥0.6、patch=32、search=±24 四个参数一个都没扫；patch 阈值对低纹理场景（treehill hit 0.589）可能已进饱和区。
**修法**：跑 (patch × search × tol × peak) 网格，报告"30% 剪枝下任务降幅 > 覆盖率降幅 的配置占比"。

### B5. 第一贡献是同义反复
"编辑使保形证书失效"是 exchangeability 前提的直接推论；Barber et al. 2023 甚至给了 coverage gap 的上界。懂 conformal 的审稿人 30 秒后写 "a corollary of exchangeability, not a finding"。**而且 AURA 自己已经写了**（`aura.txt` L1275-1280 "a distribution shift can violate it"、L1327-1336 "keep a small per-scene conformal set to restore the certificate"）。
**修法**：把"失效"降级为设置，主线换成"**证书有效 ≠ 资产可用**"：重签后覆盖率回到 0.88–0.97，同一批资产的补丁重定位仍比干净资产低 12–32 点。这条不需要任何新数据，但把论文从"复述定义"变成"测量一个反直觉的解耦"。

---

## 4. MAJOR

- **M1（诚信风险）§4 对 AURA 的两处断言不成立**：① "it evaluates no downstream task" —— AURA 有以 downstream 命名的 RQ3 与贡献 4（`aura.txt` L86、L128、L591、L1671）；② "We verified that the words edit, re-certify and invalidate do not occur" —— 字面属实但是**字符串论证**，AURA 用 exchangeability/violate/restore 把概念写足了。这种写法会把一次可以正面陈述的分界变成诚信质询。**必须换成概念陈述**（可直接改写的英文段落见 `review/reviewer_domain.md` §M1）。
- **M2 区域粒度不进主表**：像素级 −10.9–18.6 vs 体素级 −2.6–6.1（3–4× 差异）藏在附录 C。现实证书多为区域/载波级（AURA 就是 per-carrier），所以主表必须像素 + 区域并列，摘要必须带粒度限定。
- **M3 修复曲线是机械结果 + n=all 被删 + 估计量错配**（见 C5）。真正有信息量的是"恢复**原区间宽度**需要几个视角"或"固定宽度预算下覆盖率能到多少"。
- **M4 400 划分的推断被误标**：摘要称 "paired confidence intervals"，实际是同一批 16–25 个视角上的划分散布（split-to-split interval），不是场景级 CI。改称 + 一句限定即可。
- **M5 比值 1.9–12.1× 不是可外推量**：分母是 2.6–6.1pp 的小差值，比值对粒度、编辑强度、任务阈值全都敏感（跨 6 倍离散本身就是证据）。改用绝对点 + 方向/排序陈述。
- **M6 相关工作三缺口**：conformal under distribution shift（Barber 2023 必补；`tibshirani2019` 在 bib 里但正文 0 引用）、proxy metric vs downstream（Lacuna 笔记，作者已检索到却没引）、model cards/provenance（补 1–2 条即可，别展开）。3DGS 不确定性线**不要补**（会打开一场本文没打的仗）。
- **M7 缺图像质量表，工作点无法定位**：全文无 PSNR/SSIM 表；资产质量只有括号里 "16–20 dB"/"11–16 dB"；工作分辨率（实为 1/4）从未写明；而 3DGS 在 Mip-NeRF 360 上的常规量级是 25–27 dB。**每一位数都是残差分位数，残差尺度决定 q 的位置、决定"扰动比残差低三个数量级"这类论证**。必须给资产表（场景/基元数/视角数/分辨率/PSNR/SSIM/中位残差/q）并解释残差尺度的来源。（Lead 已定位一个可能根因：`normalize_exposure` 只归一化 GT 不归一化渲染，正在核实。）
- **M8 规则 (b) 存在目标视角泄漏**：`criteria_stats.py` 的 sensitivity 排序用了 `cal∪dep` 的 `views[:8]` 的 GT。规则 (b)（"用敏感度准则剪枝"）因此可能被污染；且 flowers 的 `crit_a.json` 缺失。必须只用标定视角重算。

---

## 5. MINOR（不逐条展开，见 `review/audit_report.md`）

- 摘要 "400 random splits per scene" 只对 4/9 场景成立；"the five self-trained models drop only 6.7 to −0.7" 符号与顺序都错（应为 −6.7…+0.7）；"no post-hoc correction avoids both" 是全称否定（weighted CP / ACI 都没试）。
- PUP 会议写错：ICCV 2025 → **CVPR 2025**。
- 规则 (c) 从 "SH-only 8-bit" 外推到 "quantisation" 越界（真实字节预算在位置/旋转/尺度，量化它们是几何扰动）；应改成有条件的机制结论 + 边界。
- Table 3 格式不统一（有的带区间有的不带）、L201 孤立 `*` 无表注；图 1 的 8-bit 组在视觉上不可见。
- 附录 C：α=0.10 的 −14.1 对数据 −13.50；"voxel 缩小 3–4×" 实为 1.9–4.9×；半分辨率 4 个数与 "within 1.4" 盘上无任何 artifact；§2 "16–20 dB" 实测 14.64–20.55；"107k–300k" 实测 198.5k–295.9k；附录 B "0.45–0.91 残差比" 实为 0.838–1.146、"0.822" 实为 0.828。
- Reproducibility 段的"104 assertions + 46 unit assertions"是工程自检不是科学证据，且 `verify_paper_numbers.py` 只校验 markdown 版；LaTeX 版 22 组数字无 artifact（详见审计报告）。
- 补充材料声称"随稿提供"，`submission/` 里实际没有打包。

---

## 6. 数字审计摘要（`review/audit_report.md`）

229 条断言：**188 MATCH / 19 MISMATCH / 22 NO_SOURCE**。主表（Table 2 的 47 个数、Table 5a 的 20 个、5b 三场景的 21 个）**逐位吻合**；问题集中在**跨表口径与符号**：
1. Table 4 的证书降幅与 Table 2 不是同一量（B1）；
2. Table 3 的 SH 行三处符号反了（C3）；
3. 附录 C 三处与工件不符；
4. NO_SOURCE 的 9 组（flowers 编辑族、SH 扰动 3.4–4.1e-4、训练步数、自训 PSNR、半分辨率四个数、"13.5 dB"、Table 5b flowers 整行）。
**审计员结论**：审稿人抽 20 个数，预计 6 个会被直接抓错；但"主结果没有造假，错在口径"。

---

## 7. 改到什么程度我会写 accept

| 优先级 | 动作 | 类型 | 状态 |
|---|---|---|---|
| P0 | B1 双粒度并列；摘要头号数字同粒度 | 改表 + 重算 | 待做 |
| P0 | B2 两档编辑强度进主表，主张改为"不同调" | 改表 + 改文案 | 待做 |
| P0 | B3 重写 §2（像素级分位数 + 有效样本量 56–277） | 重写一节 | 待做 |
| P0 | B5 换主线：标题/摘要/贡献改为"valid ≠ useful" | 重写摘要+引言 | 待做 |
| P0 | C3 符号、M1 AURA 断言、M8 泄漏、M7 PSNR 表 | 修正 | 部分需新测量 |
| P1 | B4 任务阈值网格 | **需 GPU** | 脚本就绪 |
| P1 | 第二下游任务（块匹配位移场）+ 剂量-反应（10/30/50/70%） | **需 GPU** | 脚本就绪 |
| P1 | PUP 剪枝下的覆盖率与下游（与规则 (b) 自洽） | **需 GPU** | 脚本就绪 |
| P2 | M2 主表加区域列；M5 比值降级；M6 相关工作重写 | 离线 | 待做 |
| P3 | 匿名补充材料 + LaTeX 数字自动校验接入 | 工程 | auditor 脚本就绪 |

**门槛表述**：P0 全做 + B4 网格 + 第二任务 + PUP，且新主张（覆盖率与任务效用不同调 / 有效证书 ≠ 可用资产）在**两种粒度、两种编辑强度**上都被数据支持 → 三位评审均表示会由 Reject 改为 **Accept**。若头号数字仍跨粒度、或 50% 那一档仍缺席 → 维持 Reject。
