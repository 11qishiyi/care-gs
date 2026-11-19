# CVIU 差距分析与改造方案（2026-11-12）

> 依据：`review/CVIU_SCOPE_2026-11.md`（官方要求 + CVIU 3DGS 全景）、`review/CVIU_GENRE_PRECEDENTS.md`（评测体裁先例 116 DOI）、`review/RELWORK_SWEEP_CVIU.md`（2026 新作 67 篇）。
> 对象：`submission/final/` v5（TMLR 版，20 页，494 断言，9 资产）。
> 结论先行：**可投，但必须做一次"贡献形态"改造**——把"测量"升格为"协议 + 估计器 + 可复用资产"，并把一个逻辑漏洞补成一个正向结果。三处改动，一处新实验轮次。

---

## 1 结论：CVIU 要什么，我们缺什么

| # | CVIU 的事实（证据） | 我们现状 | 判定 |
|---|---|---|---|
| 1 | **无页数/字数上限**，摘要 ≤250 词，Keywords 1–7，Highlights 3–5×≤85 字符，单盲，CRediT + COI + Data availability(Option C，必须 deposit) + GenAI 五件套【官方 Guide】 | 20 页 TMLR 版，匿名，无 Highlights/CRediT/Graphical Abstract | 格式层：**0 风险**，纯包装工作 |
| 2 | **7 天首决定 / 94 天审后决定 / 201 天接收**；7 天 vs 94 天的 13 倍差说明 **desk rejection 是主淘汰机制**（CVIU 148(2016) editorial：121 投 54 篇 out-of-scope 未送审） | 现摘要第一句是"资产会附带覆盖证书"，没有"非主流洞察"信号；标题是质问式 | **高风险**：首周生死线 |
| 3 | scope 唯一的新颖性措辞："papers offering insights that **differ from predominant views**"【官方】 | 我们的洞察恰好是"证书有效≠可用"，是非主流洞察 | **优势**，但必须写进前 85 字符 |
| 4 | 先例：**CVIU 84(1) 2001 专刊 "Empirical Evaluation of CV Algorithms"**，10 篇纯评测、无一提出新算法 | — | cover letter 第一段即可引用，**体裁合法性已证** |
| 5 | 体裁公约数（8 篇解剖）：**6/8 自带新 protocol 或新 metric**；贡献句一律 "present a comprehensive evaluation of…" / "systematically studies the impact of…" | 我们**没有命名过任何 protocol/metric**；`certificate_audit.py` 与 494 断言藏在附录 | **中高风险**：CVIU 接受"无新方法"，但不接受"无新协议/指标" |
| 6 | 3DGS 这条线 **6 篇**，唯一纯测量先例（v263 104575, 20 refs）**交付了 UnrealGaussianStat 数据集**；CVIU 这条线**没有"无新方法 + 无新数据集"的先例** | 我们无对外数据集，只有补充材料 zip | **中风险**：需把 dump 资产化 |
| 7 | 2026 年 CVIU **连发两篇 conformal prediction**（v273 104964 明确用 "valid coverage"；v271 104870） | 我们引了 VSCP/AURA，但没引 CVIU 自刊的这两篇 | **必改**：自引本刊近作是审稿人信号 |
| 8 | "calibration" 在 CVIU 命中的 52 篇几乎全是**相机标定** | 我们通篇用 calibration（conformal 语境） | **必改**：标题/摘要改用 conformal / coverage / certificate |
| 9 | 71 位编委**无人自报 uncertainty/probabilistic**；3D 相关：Jingyi Yu（IBR）、Arrigoni（MVD）、Daoudi（3D shape） | 我们主打"保形证书" | **中风险**：必须写成"3D 表示的可靠性/评测"而非"保形统计" |
| 10 | 评测类论文无需 user study（8 篇摘要 0 提），但 SSIM/LPIPS 是标配（同类 18 篇中 SSIM 14/18、LPIPS 13/18） | 我们只有 PSNR | **中风险**：需补 SSIM/LPIPS 列 |
| 11 | 统计检验在同类 18 篇里只有 4 篇做 CI/检验，**多 seed 0/18** | 我们 400 次划分 + 配对 bootstrap + 9 场景 | **优势**：应升为卖点而非附录 |

---

## 2 三个真实威胁（2026 新作，必须正面处理）

| 威胁 | 论文 | 它占了什么 | 我们必须怎么改 |
|---|---|---|---|
| **T1** | *Coordinate Singularities Break Conformal Coverage*（arXiv 2607.02565, 2026-06） | 名义 90% 的 slice-conditional 覆盖实测塌到 **38.9/42.0/57.5/55.2%**（30–50 pp） | 任何"首次观测到大覆盖损失"的说法**已不成立**。我们只能说"编辑诱导的失效"，且必须引用它 |
| **T2** | *A Calibration Audit of Confidence in Feed-Forward 3D Reconstruction*（arXiv 2608.29705, 2026-08） | 7 backbone × 13 数据集，**审计 3D 重建可靠性信号**，含 coverage，量级偏差 ≥2.4× | "审计 3D 重建的可靠性"已被占；且其 **2.4×** 与我们的 **2.4×**（亮度归一化衰减）**纯属撞车**，必须在正文一句话切开 |
| **T3** | *Done Is Not Correct*（arXiv 2611.10063, 2026-11） | 自检不可信：98% 声称完成、14.1% 静默错误 | 我们 §"自检是循环论证"只是它的一个领域实例，**除非**我们把它推进到"构造性循环"（检查器与被检查共享同一残差源 ⇒ 恰好名义值）并给出**可运行的替代检查** |

> **T3 的处理正是本方案的核心**（见 §3）。

另外两条必须处理的近邻：
- **REFINE**（arXiv 2606.09074）：解析 Hessian field 预测逐基元删除误差 → 我们的 Fisher 准则必须**降级为对照**，不能作为贡献。
- **Mind the Gap**（arXiv 2607.01556）：SH 阶数**更高**在 3/9 场景伤害外推 → 与我们"SH 降阶几乎零代价"表面冲突，需一句"测的量不同"。

---

## 3 关键改造：把一个逻辑漏洞补成论文的正向核心

### 3.1 漏洞

现稿 §3.7 写：

> "the natural check is to re-run calibration and read off coverage. The check returns 1−α by construction … **A stale certificate is therefore not detectable from the calibration set alone**."

**这句话过强。** "重跑标定"返回名义值是对的（`q` 就是它自己重数的那些残差的分位数，循环）；但**另一个**检查不是循环的：

> 把**编辑后**的模型在**随证书一起交付的标定视角**上重渲染，数有多少残差落在**原封不动的旧 `q`** 之下。

旧 `q` 来自**未编辑**模型在同一批视角上的残差，所以它不是"重数自己"；而编辑只是模型的一个函数，不改变视角的交换性，因此这批视角在编辑后仍与部署视角可交换。**这个检查不是保证，但它是估计**——而且它只用交付物本身。

### 3.2 已有数据上的预验证（旧 archive，2 场景 × 10 编辑）

`research/results_v3/sc_{flowers,treehill}.json` 里的 `cal_self_cov` 就是它：

| 场景 | 审计估计 vs 真实事后部署覆盖 | 原始误差 | 以 no-op 编辑（8-bit SH）作基线校正后 |
|---|---|---|---|
| flowers（26 标定 / 35 部署视角） | 0.732 vs 0.723（prune30） | 平均 3.3 pp，最大 7.7 pp | **平均 0.8 pp，最大 5.2 pp** |
| treehill（21 / 28） | 0.749 vs 0.777（prune30） | 同上 | 同上 |

也就是说：**陈旧证书是可检出的，精度约 1 个百分点**，代价是一次重渲染。这比"不可检出"强得多，而且正是 CVIU 要的"可操作交付物"。

### 3.3 升级为三条可命名的贡献

1. **CAV（Certificate Audit on Vault views）——审计估计器。**
   给定义、伪代码、复杂度（一次前向渲染 + 一次 CDF 比较）、以及"需要交付标定视角 GT"这一**协议要求**（这正是 Data availability 政策要的东西）。
2. **Proposition 1（Kolmogorov 包络）。**
   设 `F`/`F'` 为干净/编辑模型在**标定视角**上的残差 CDF，`q` 为签发的分位数，则

   ```
   coverage_loss = F^dep(q) − F'^dep(q) = [F^cal(q) − F'^cal(q)] + (交换性松弛)
                 ≤ KS(F^cal, F'^cal) + slack
   ```

   因为 `F^cal(q) ≈ 1−α`。于是**发行方（有标签）在签发时就能预演整个编辑族**（自己剪一遍、渲一遍标定视角），把"稳定性包络"写进证书；**接收方（无新标签）只需一次重渲染就能核对包络是否被突破**。
   与 Usama & Qadir 的 "declared change envelopes" 概念呼应但对象不同（他们认证"改动位置"，我们认证"覆盖损失上界"）。
3. **发行配方（issuance recipe）。** "编辑后签发 / 声明准则与区域 / 附包络 / 附审计材料"四件套，每一条都有测量支撑，并给出 1.5–2.2× 的宽度代价。

> 这一改把论文从"我们发现证书会坏"变成"**我们给出一个能自查、能自证、能预演坏的证书格式**"。这就是 CVIU 的"insights that differ from predominant views"。

### 3.4 论文骨架（CVIU 版，目标 22–26 页）

1. Introduction（洞察句前置）
2. **The certificate and its audit**（对象定义 + CAV + Proposition 1 + 协议自由度清单）← 新增的方法节
3. Setup（资产/编辑/协议）
4. Results A：失效是几何专属，且是曲线（现有 Table 2/4）
5. Results B：**审计**（CAV 精度 + KS 包络紧致度 + k 视角曲线）← 新增
6. Results C：准则（Fisher 降为对照）、约定（2.4×）、区域粒度
7. Results D：效用解耦（四族任务）
8. Results E：修复与发行配方（含宽度代价）
9. Related work（补 CVIU 自刊 conformal 两篇 + T1/T2/T3 + REFINE + Mind the Gap）
10. Discussion / Limitations
11. 附录：区域粒度、修复曲线、两类陷阱、学习型匹配器、位深/优化深度/第五资产、工具与一键复现

---

## 4 实验清单（一轮 GPU 即可闭环）

现有 npz 已随节点清理消失，必须重跑一次 `dump_artifacts.py`。**一次 dump，五项新分析全部落地**：

| 项 | 做法 | 为什么必须 |
|---|---|---|
| E1 | 9 资产 × 8 变体（clean/prune50/prune30/pup30/shdeg1/quant8/quant6/quant4）的**逐视角残差 dump** | CAV/KS 包络只能从逐视角残差算；现只有 2 场景的旧 JSON |
| E2 | 同一次渲染里算 **SSIM + LPIPS**（每变体每视角） | CVIU 标配（14/18、13/18） |
| E3 | `audit_bound.py` 跑全量 → CAV 误差、KS 紧致度、k 视角曲线 | 新贡献的主表 |
| E4 | 4 个 released 资产的**单独子表**；5 个自训资产标注为压力测试 | 回应"为什么 5/9 是自训" |
| E5 | 导出 **数据资产包**（残差 dump + 变体清单 + 审计脚本 + 复现脚本），Zenodo DOI | Data availability Option C 强制；也是"无新方法"稿的先例形态 |

成本估计（沿用历史口径）：A40 单卡约 3–5 小时，¥8–15。**除 E5 外全部落在 CPU**。

---

## 5 风险与对策

| 风险 | 概率 | 对策 |
|---|---|---|
| 7 天 desk reject（判"无新方法"） | 中 | 标题/摘要/Highlights 前 85 字符直接给洞察；cover letter 引 84(1) 专刊；CRediT 里明写"protocol 与 audit 工具是第一贡献" |
| 被判 out of scope（无 3D/render 字样） | 低 | 靠 "Data structures and representations" + "Shape" 两条；标题保留 3D Gaussian Splatting |
| 找不到 uncertainty 对口编辑 | 中 | 全文改称 "reliability / validity of a 3D representation's shipped guarantee"，把保形放在方法层而非卖点层 |
| 与 T1/T2/T3 撞车被判增量 | 中 | 正文设一小节"what is already known"，逐条切开；我们的差异在**编辑诱导**+**剂量曲线**+**可审计** |
| Fisher 被判非贡献 | 高 | 降级为"对照准则"；贡献改为"准则本身就是变量" |
| 数据集太小太弱（5 自训资产 18–26 dB） | 中 | 4 个 released 单独成表；自训明确写成 stress test；统计功效（400 splits × 9 场景）当主角 |
| 2.4× 与 T2 撞车被误读 | 中 | 正文一句话显式切开（T2 是量级偏差，我们是亮度归一化导致的幅度衰减） |

---

## 6 里程碑

| 阶段 | 内容 | 依赖 |
|---|---|---|
| M1 | 差距分析 + 方案（本文件） | 完成 |
| M2 | GPU 轮：dump 9×8 + SSIM/LPIPS | **需用户批准租机** |
| M3 | CPU 分析：CAV / KS 包络 / k 视角 / 统计 | M2 |
| M4 | elsarticle 重写（含 250 词摘要、Highlights、Graphical Abstract、CRediT、Data availability） | M3 |
| M5 | 校验器改造（494 → CVIU 版断言）、补充材料、Zenodo 资产包 | M4 |
| M6 | cover letter + 投稿清单 + 内部红队复审 | M5 |
