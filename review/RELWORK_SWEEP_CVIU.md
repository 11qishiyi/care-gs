# 相关工作扫掠：改投 CVIU 前的 2026 年威胁面（Relwork Sweep, CVIU retarget）

> 对象：`submission/final/main.pdf` — "Valid but Unusable: What Coverage Certificates Miss When 3DGS Assets Are Edited"
> 扫掠日期：**2026-11-12**（16:40–17:10 Asia/Shanghai）
> 时间窗：**2026-01-01 → 2026-11-12**（arXiv `submittedDate`）
> 本文件的用途：① 找出可能 scoop / 削弱我们的 2026 年新作；② 精确对标"评测协议"竞品集；③ 列出 CVIU 审稿人会要、而我们目前没有的东西。

## 0. 检索口径与证据分级（先读这一节）

### 0.1 渠道状态（诚实记录）

| 渠道 | 状态 | 说明 |
|---|---|---|
| arXiv API (`export.arxiv.org/api/query`) | **可用** | 62 组 query 字符串（28 组主查询 + 20 组 scoop 导向 + 8 组评测方法学 + 6 组补充）。服务端 `submittedDate` 过滤不可靠（会漏/不过滤），因此**全部在客户端按 `published` 复核日期**，并要求题名或摘要与 3D 视觉词共现（splat / nerf / radiance / render / 3D / view synthesis / gaussian / reconstruct / mesh）。 |
| arXiv HTML 全文（`arxiv.org/html/<id>`） | **可用** | 18/18 取到，用于第 3 节的成分计数。 |
| `web_search` / `web_fetch` | 可用 | 用于 abs 页正文、NerfBaselines 评测协议细节、第三方索引。 |
| **OpenAlex** | **未取到（429）** | 无 API key，与同 IP 共享 $0.10/日预算。前几次 200 响应返回 `count=0`（限流降级），随后彻底 429。**本轮没有任何结论依赖 OpenAlex。** |
| **Semantic Scholar** | **部分未取到** | `paper/search` 端点全程 429；`paper/{id}/citations` 端点间歇可用，成功取到 1 条引用边（见 §1.5），其余为空或 429。 |
| Crossref | 可达 | 仅做过可达性探测，**本轮未系统检索**。 |

### 0.2 标记法

| 标记 | 含义 |
|---|---|
| **[A]** | 我**读了摘要全文**（arXiv API `summary` 字段或 abs 页正文） |
| **[T]** | **只看到标题与元数据**，未读摘要 |
| **[F]** | 取到全文 HTML，但只做**程序化统计**（关键词命中/计数），**未逐段人读** |

### 0.3 本轮最重要的三个判断

1. **没有同题论文。** 在 2026 年窗口内，**没有**任何工作测量"3DGS 资产被再编辑后，覆盖率/保形证书失效多少"，也没有工作把证书指标与下游任务成功率放在同一张表上。我们的核心位置仍然空着。
2. **但"覆盖率会大幅掉"这件事，2026 年已经有人替我们说了——在别的任务上。** `2607.02565` 在 gaze/head-pose 上报告 slice-conditional coverage 从名义 90% 掉到 **38.9%–57.5%（掉 30–50 个百分点）**。我们的头条数字是 10.8–27.7 点。**如果我们在引言里写"我们首次观察到 3D 视觉中覆盖率大幅失效"，会被这一篇直接否掉。**
3. **我们的第 (v) 条（自检是循环论证、永远返回 nominal）也有近邻**：`2611.10063` 在 CAD/LLM agent 上把"completion-claim calibration"做成了可测量，报告 **98% 声称完成、14.1% 静默错误**。机制同源（自检与被检对象共享同一信息源），域不同。

---

## 1. Task 1 — 2026 年可能 scoop 或威胁我们的工作

### 1.1 威胁分级总表

| # | 论文 | 日期 | 标记 | 威胁 | 具体威胁到我们哪一句 | 处理 |
|---|---|---|---|---|---|---|
| 1 | **Coordinate Singularities Break Conformal Coverage for Gaze and Head Pose** — [2607.02565](https://arxiv.org/abs/2607.02565) | 2026-06-29 | [A] | **高（表述层）** | "首次观察到 3D 视觉任务中 conformal 覆盖率大幅失效" | 必须引；把新颖性从我方"观察到失效"改为"**归因到资产编辑算子**+剂量-反应+准则依赖+协议依赖" |
| 2 | **A Calibration Audit of Confidence in Feed-Forward 3D Reconstruction Models** — [2608.29705](https://arxiv.org/abs/2608.29705) | 2026-08-30 | [A] | **高（框架层）** | "对 3D 重建的可靠性信号做 audit 是空白" | 必须引；他们 audit 的是**出厂的 confidence**，不是**签发后需存活的证书**；且无编辑、无下游任务 |
| 3 | **Done Is Not Correct: Measuring Silent Failures and Self-Verification Calibration When LLM Agents Take CAD Actions** — [2611.10063](https://arxiv.org/abs/2611.10063) | 2026-11-06 | [A] | **中高（claim v）** | "自检/自审是循环论证、恒返回 nominal 这一观察是新的" | 引为"自检校准已被证明系统性过度乐观"的先例，说明我们在 3DGS 上给出的是**结构原因**（标定集与部署集共享同一残差源） |
| 4 | **When Variance Is Not an Error Map: Calibrated Uncertainty for Radiative Gaussian Splatting in Sparse-View CT** — [2607.13682](https://arxiv.org/abs/2607.13682) | 2026-07-15 | [A] | 中高（claim iii） | "可靠性信号不跟踪真实误差"在 3DGS 上没人做过 | 必须引；他们给的是**机制**（72–96% 平方误差在独立训练的成员间共享），正好支撑我们"证书不跟踪任务效用"的解释 |
| 5 | **REFINE: Super-efficient 3DGS Pruning via Rendering-Free Primitive Importance** — [2606.09074](https://arxiv.org/abs/2606.09074) | 2026-06-08 | [A] | 中高（claim i） | "剪枝准则与预算同等重要"接近他们的主张 | 引；他们用 analytic Hessian field 预测**单primitive 移除的期望感知误差**，我们是测**证书损伤**——预测误差≠预测证书失效 |
| 6 | **Predictive Photometric Uncertainty in Gaussian Splatting for NVS** — [2603.22786](https://arxiv.org/abs/2603.22786) | 2026-03-24 | [A] | 中（最近的技术近邻） | "3DGS 缺少逐像素可靠性通道" | 引；他们是 post-hoc 逐像素**不确定度**，无 distribution-free 覆盖、无编辑、无任务对照 |
| 7 | **Adaptive Computation with Conformal Certification** — [2610.19189](https://arxiv.org/abs/2610.19189) | 2026-10-13 | [A] | 中（"conformal+剪枝"占位） | "没人把 conformal 用在剪枝/量化这类效率编辑上" | 引；对象是医学/天文 **2D 影像**，且是**重标定被适配的模型**取 risk guarantee，不是"出厂证书在编辑后静默失效" |
| 8 | **VEDAL: Variational Error-Driven Asynchronous Learning for 3DGS Pruning** — [2606.02346](https://arxiv.org/abs/2606.02346) | 2026-06-01 | [A] | 中 | "剪枝与不确定性耦合"是空白 | 引；他们**用**不确定性指导剪枝，不测剪枝**破坏**不确定性 |
| 9 | **EditBench3D: What Makes a 3D Scene Editable?** — [2609.14899](https://arxiv.org/abs/2609.14899) | 2026-09-14 | [A] | 中（Task 2 交叉） | "编辑后单轴指标会误导" | 引；40 场景×6 编辑=240 对，8 个编辑器，结论是 semantic fidelity 与其余三性质**弱相关** |
| 10 | **CleanGS: Pareto-Guided Post-Hoc Cleanup of 3DGS Scenes** — [2601.00913](https://arxiv.org/abs/2601.00913) | 2026-01-01 | [A] | 低中（盟友） | "出厂资产会被后处理"这一动机 | 引；他们**直接评测导出的资产**并引入 fixed-pose widened-field 协议——可借力 |
| 11 | **GaussFlaw: Fine-Grained Perceptual Diagnosis for 3DGS** — [2611.02767](https://arxiv.org/abs/2611.02767) | 2026-11-02 | [A] | 低中 | "全局指标无法定位伪影" | 引一句；他们做感知诊断数据集，不做覆盖率 |
| 12 | **From Splats to Silicon: Rethinking Computational Efficiency of 3DGS** — [2609.06157](https://arxiv.org/abs/2609.06157) | 2026-09-05 | [A] | 低中（Task 2） | 效率类评测的方法学 | 引；说明"报告指标与端到端收益脱节"已是 2026 年的公开议题 |
| 13 | **YUBI-Real2Sim: 3DGS Scene Verification for Reliable Policy Evaluation** — [2610.17521](https://arxiv.org/abs/2610.17521) | 2026-10-13 | [A] | 中（反向近邻） | 他们做 quality→task，我们做 certificate↛task | 必引且要**区分方向**：他们证明重建质量**会影响**策略评测；我们证明证书量**不预测**任务效用。二者不矛盾，但必须写清 |
| 14 | **VCURF: Virtual Camera-based Uncertainty of Radiance Fields** — [2610.04076](https://arxiv.org/abs/2610.04076) | 2026-10-02 | [A] | 低中 | 逐像素 UQ（NeRF+GS 通用） | 引；无覆盖保证 |
| 15 | **GaussTrace: Provenance Analysis of 3DGS Models** — [2606.10612](https://arxiv.org/abs/2606.10612) | 2026-06-09 | [A] | 低（术语圈地） | "asset + provenance" 词汇 | 引一句：溯源证明**来源**，不证明**精度** |
| 16 | **GuardMarkGS: Unified Ownership Tracing and Edit Deterrence for 3DGS** — [2605.12919](https://arxiv.org/abs/2605.12919) | 2026-05-13 | [A] | 低 | "出厂后可被编辑"动机 | 可与 #15 合并引一句 |
| 17 | **Position: 3DGS Watermarking Should Be Scenario-Driven and Threat-Model Explicit** — [2602.02602](https://arxiv.org/abs/2602.02602) | 2026-02-01 | [A] | 低 | 资产治理话语 | 可选 |
| 18 | **GETA-3DGS: Automatic Joint Structured Pruning and Quantization** — [2605.02086](https://arxiv.org/abs/2605.02086) | 2026-05-03 | [A] | 低（编辑算子证据） | 剪枝+量化是标准部署编辑 | 引，支撑"我们的编辑算子就是工业界实际会做的" |
| 19 | **When 3D Gaussian Splatting Recovers Real Surfaces** — [2608.30054](https://arxiv.org/abs/2608.30054) | 2026-08-30 | [A] | 低中（与 SH 结论互动） | SH 容量↑ → 可用 billboard 解释图像 → 几何失效 | 值得引：解释"为什么 SH 降阶对**误差**几乎零成本，却可能伤**外推**" |
| 20 | **Fisher Information 用于稀疏视角 3DGS** — [2606.20842](https://arxiv.org/abs/2606.20842) | 2026-06-18 | [A] | 低（削弱 Fisher 新颖性） | 我们把 Fisher 当三准则之一 | 引；Fisher 在 3DGS 里已不新，故 Fisher 只能是**对照准则**，不能当贡献 |
| 21 | **When Does Low-Bit Quantization Preserve the Decisions of Vector Search?** — [2609.09854](https://arxiv.org/abs/2609.09854) | 2026-09-09 | [T] | 低（类比） | 我们"8-bit SH 量化≈0 成本" | 可选类比引用；**未读摘要，引用前须核** |
| 22 | **Self-Auditing Parameter-Efficient Fine-Tuning for Few-Shot 3D Medical Image Segmentation** — [2603.05822](https://arxiv.org/abs/2603.05822) | 2026-03-06 | [T] | 低 | "self-audit" 一词 | 仅记录；未读 |

> 说明：上表 22 条中 20 条 **[A]**、2 条 **[T]**。第 21、22 条在正式引用前必须补读摘要。

### 1.2 三条最危险的，逐条说清

#### (1) `2607.02565` — Coordinate Singularities Break Conformal Coverage（2026-06-29）[A]
- **它做了什么**：证明 conformal 的保证依赖"误差在输出空间怎么量"。当输出在弯曲空间（球面 gaze、3D 旋转）而 score 定义在 yaw-pitch / Euler 这类平直坐标卡上时，坐标奇异点附近出现系统性几何畸变。
- **数字**：4 个数据集（ETH-XGaze、Gaze360、BIWI、AFLW2000-3D）；名义 90% 下 slice-conditional coverage 在奇异区掉 **30–50 个百分点**：ETH-XGaze 38.9%、Gaze360 42.0%（pitch>70°）、BIWI 57.5%、AFLW2000-3D 55.2%。
- **对我们的威胁**：**这是"3D 视觉里覆盖率可以掉 30–50 点"的现成先例，且幅度比我们大。** 审稿人会问："你们 10.8–27.7 点有什么好惊讶的？"
- **正确的应对**（不躲）：他们的失效源是**评分函数的坐标选择**（部署前就存在，与被测模型无关）；我们的失效源是**资产在签发之后被改动**（部署后才发生，且与改动预算单调相关）。一句话定位：
  > "Prior work shows that *how you score* can break coverage [2607.02565]; we show that *what you ship* can break it too, and that the damage is a function of the edit operator, its budget, and the ground-truth preprocessing convention."
- **不要写**："we are the first to observe large coverage loss in 3D vision"。这句现在是错的。

#### (2) `2608.29705` — A Calibration Audit of Confidence in Feed-Forward 3D Reconstruction（2026-08-30）[A]
- **它做了什么**：指出 feed-forward 3D 重建模型输出的 per-pixel confidence 本是训练损失里的权重，**从未被验证过能否当不确定度幅度用**。audit 7 个 backbone × 13 个数据集，按 4 个性质打分：误差排序、平均 error/uncertainty 比值、该比值随 confidence 的斜率、**implied error distribution 的 coverage**。
- **结论**：排序很好，但**幅度太小**；中位数情形下至少偏 **2.4×**，且模型越自信偏得越多；只有恰好在训练条件下才"尺寸正确"；在未见场景上表现为 overconfidence。
- **对我们的威胁**：①它把 "audit 一个 3D 重建可靠性信号" 这件事占了；②它**也报告 coverage**；③它的 **2.4×** 与我们"逐视角亮度归一化把失效衰减最多 2.4 倍"里的 2.4 **纯属巧合**——审稿人很可能误读为同一件事。**必须在正文显式消歧**（一个是 uncertainty 幅度偏差，一个是我们度量到的失效衰减因子）。
- **定位**：
  > "Concurrent work audits whether a *shipped confidence channel* can be read as an uncertainty magnitude [2608.29705]; we audit whether a *distribution-free certificate* survives edits to the asset it was issued for. Their audit is of a signal that is never re-issued; ours is of a guarantee whose validity is conditional on the asset staying fixed."

#### (3) `2611.10063` — Done Is Not Correct（2026-11-06）[A]
- **它做了什么**：LLM agent 写参数化 CAD 代码时，语法成功与语义正确解耦。发布 13 个规格任务（每条要求映射到 B-rep 的可机器检查性质）+ 评分 harness，量两个此前没人报的量：**silent-failure rate**（产物可渲染、明确声称完成、但至少一项语义检查失败）与 **completion-claim calibration**。
- **数字**：4 家厂商 4 个模型，每架构 156 次尝试；单发 agent **98% 声称完成、14.1% 静默错误**；换成"先测量再声称"的工具循环后静默失败降到 **3.2%**。
- **对我们的威胁**：我们的 (v) 条（label-free 自检恒返回 nominal）在**现象层**被它先说了。我们的独特之处只剩**机制**：自检用的标定集与部署集共享同一残差源，因此自检统计量在原假设下**恒等于** nominal —— 这是可证的循环，不是经验偏差。
- **定位**：
  > "Self-verification is known to be systematically over-optimistic when the checker shares information with the checked system [2611.10063]; we give the 3DGS instance of this circularity and show it is not merely biased but *exactly nominal by construction*."

### 1.3 分轴清单（供 Related Work 直接取用）

**(a) Conformal / certificate × 3D 视觉（2026 新增，除已知条目外）**

| 论文 | 日期 | 标记 | 一句话 |
|---|---|---|---|
| [2607.02565](https://arxiv.org/abs/2607.02565) | 06-29 | [A] | 坐标奇异点破坏 gaze/head-pose 的 conformal 覆盖 |
| [2610.19189](https://arxiv.org/abs/2610.19189) | 10-13 | [A] | 自适应计算（量化/剪枝）下的 conformal risk 认证，对象是 2D 科学影像 |
| [2610.03127](https://arxiv.org/abs/2610.03127) | 10-02 | [A] | RL-NAS 中交换性被破坏 → 用 online conformal（ACI）恢复"可调的覆盖" |
| [2607.00776](https://arxiv.org/abs/2607.00776) | 07-01 | [T] | prediction uncertainty → conformalized distance fields（运动规划） |
| [2609.12493](https://arxiv.org/abs/2609.12493) | 09-11 | [T] | "certified state estimation" 的可恢复性基准（不同义） |

> `2610.03127` 值得单独一提：它明确写出"conformal 的交换性假设被周边 RL 循环破坏"，并**用在线重标定修好**。这与我们"修便宜（有效性）但贵（宽度）"的结论是同一枚硬币，可作对照引用。

**(b) 3DGS / NeRF 的逐像素不确定性（2026 密集）**

| 论文 | 日期 | 标记 | 一句话 |
|---|---|---|---|
| [2603.22786](https://arxiv.org/abs/2603.22786) | 03-24 | [A] | post-hoc、逐像素、视角相关预测不确定度；per-primitive 通道；架构无关 |
| [2610.04076](https://arxiv.org/abs/2610.04076) | 10-02 | [A] | 虚拟相机渲染不一致 → 逐像素 UQ，NeRF/GS 通用黑盒 |
| [2607.13682](https://arxiv.org/abs/2607.13682) | 07-15 | [A] | **variance≠error map**：全volume Spearman 0.846 → 前景 0.108 |
| [2607.05522](https://arxiv.org/abs/2607.05522) | 07-06 | [A] | Bayesian 3DGS，NIW 后验，重渲染采样得预测不确定度 |
| [2607.10912](https://arxiv.org/abs/2607.10912) | 07-12 | [A] | DP 先验让基元数自适应；给 ELBO 单调性与截断误差界 |
| [2602.23574](https://arxiv.org/abs/2602.23574) | 02-27 | [T] | Evidential NeRF |
| [2604.01030](https://arxiv.org/abs/2604.01030) | 04-01 | [T] | 不确定性感知的可微优化（feed-forward 3DGS） |

**(c) 可靠性信号的 audit / calibration**

| 论文 | 日期 | 标记 | 一句话 |
|---|---|---|---|
| [2608.29705](https://arxiv.org/abs/2608.29705) | 08-30 | [A] | 7 backbone×13 数据集 audit confidence；幅度偏 ≥2.4× |
| [2611.10063](https://arxiv.org/abs/2611.10063) | 11-06 | [A] | 自检校准 + 静默失败率（CAD/LLM） |
| [2608.27178](https://arxiv.org/abs/2608.27178) | 08-27 | [T] | 医学分割的 performance–calibration trade-off |
| [2601.23107](https://arxiv.org/abs/2601.23107) / [2611.04912](https://arxiv.org/abs/2611.04912) | 01-30 / 11-03 | [T] | LiDAR-相机**外参**失准检测（"miscalibration" 的另一义，注意别混） |

**(d) 剪枝准则 / 移除误差预测**

| 论文 | 日期 | 标记 | 一句话 |
|---|---|---|---|
| [2606.09074](https://arxiv.org/abs/2606.09074) | 06-08 | [A] | REFINE：analytic Hessian field 预测移除某 primitive 的期望感知误差，免渲染 |
| [2606.02346](https://arxiv.org/abs/2606.02346) | 06-01 | [A] | VEDAL：变分自由能 + 预测误差门控的异步剪枝 |
| [2607.10912](https://arxiv.org/abs/2607.10912) | 07-12 | [A] | DP-Splat：复杂度由数据定，非人工 cap |
| [2605.02086](https://arxiv.org/abs/2605.02086) | 05-03 | [A] | GETA-3DGS：剪枝+量化联合自动化 |
| [2610.09343](https://arxiv.org/abs/2610.09343) | 10-07 | [T] | TileSkipper：region-adaptive tile 剪枝 |

**(e) 资产作为可编辑 / 可溯源对象**

| 论文 | 日期 | 标记 | 一句话 |
|---|---|---|---|
| [2606.10612](https://arxiv.org/abs/2606.10612) | 06-09 | [A] | GaussTrace：3DGS 溯源图 + 编辑模拟 + LLM 推理 |
| [2605.12919](https://arxiv.org/abs/2605.12919) | 05-13 | [A] | GuardMarkGS：水印 + 编辑威慑 |
| [2602.02602](https://arxiv.org/abs/2602.02602) | 02-01 | [A] | Position：3DGS 水印应场景驱动、威胁模型显式 |
| [2601.00913](https://arxiv.org/abs/2601.00913) | 01-01 | [A] | CleanGS：导出资产的后处理清理 + 直接评测导出资产 |
| [2611.01162](https://arxiv.org/abs/2611.01162) / [2610.11364](https://arxiv.org/abs/2610.11364) / [2608.17447](https://arxiv.org/abs/2608.17447) | 10-31 / 10-08 / 08-18 | [T] | 4DGS/3DGS 水印三连（SH 系数扰动、免训练、原生） |

**(f) 编辑基准与"编辑会改变什么"**

| 论文 | 日期 | 标记 | 一句话 |
|---|---|---|---|
| [2609.14899](https://arxiv.org/abs/2609.14899) | 09-14 | [A] | EditBench3D：40 场景×6 编辑=240 对，4 性质，8 编辑器 |
| [2609.14899] 的结论 | — | — | semantic fidelity 与 locality/consistency/preservation **仅弱相关** |
| [2611.02767](https://arxiv.org/abs/2611.02767) | 11-02 | [A] | GaussFlaw-80K：细粒度感知诊断数据集 |

### 1.4 明确的"没找到"（negatives，可作为我们贡献边界的证据）

这些是**查过且为空**的，写进论文比不写更有利：

| 检索式 | 窗口内结果 | 结论 |
|---|---|---|
| `all:"pruning" AND all:"uncertainty" AND all:"splatting"` | 4 篇（GOFusion、DL-SLAM、VEDAL、Denoising-GS） | **全部是"用不确定性指导剪枝/训练"，没有一篇测"剪枝是否破坏不确定性估计或证书"** |
| `all:"pruning" AND all:"calibration" AND all:"gaussian"` | 12 篇 | 无一与证书/覆盖相关；命中的是 tile 剪枝、量化、外参标定等 |
| `all:"asset" AND all:"quality metadata"` | **0 篇** | "资产质量元数据"这一表述在 arXiv 2026 窗口内不存在 → 我们的 framing 是新的 |
| `all:"distribution shift" AND all:"neural rendering"` | **0 篇** | 该组合是空白 |
| `all:"distribution shift" AND all:"gaussian splatting"` | 1 篇（无关：手语数据集） | 同上 |
| `all:"editing" AND all:"gaussian splatting" AND all:"certificate"` | 由 6 组 query 交叉确认 **无命中** | **我们的核心交叉点仍无人占** |
| `all:"self-audit" AND all:"3D"` | 2 篇（CAD/LLM、医学分割 PEFT） | 3DGS 上无 |
| `all:"conformal" AND all:"radiance field"` | **0 篇** | — |

**唯一必须承认的空白填补者**：`2607.02565`（见 §1.2）。除此之外，"编辑→证书失效"这条线上是干净的。

### 1.5 已知条目的"更新 / 谁引用了它们"核对

| 已知条目 | 是否发现更新的同族工作 | 引用核对 |
|---|---|---|
| VSCP `2609.10307` | 未发现 v2 或后续 | S2 citations 返回**空**（0 条）。⚠️ S2 图滞后，**不能据此断言"无人引用"** |
| Mind the Gap `2607.01556` | — | S2 取到 **1 条引用边**：[2610.17521 YUBI-Real2Sim](https://arxiv.org/abs/2610.17521)（2026-10-13）[A]。该文用 3DGS 做 real2sim 场景验证，指出"可靠策略评测所需的 3DGS 重建质量尚未被量化" |
| Doula & Mühlhäuser `2610.28937` | 同族新增：[2610.19189](https://arxiv.org/abs/2610.19189)（conformal+效率编辑）、[2610.03127](https://arxiv.org/abs/2610.03127)（交换性被 RL 循环破坏→在线重标定） | S2 citations 空 |
| Manifold-GS `2608.00214` | 未发现后续 | S2 citations 空 |
| AURA（engrXiv 10.31224/7689） | 未发现后续 | **未取到**（OpenAlex/S2 均不可用，engrXiv 无引用图接口） |
| NerfBaselines（NeurIPS 2025 D&B） | 见 Task 2 | **未取到** |

> **OpenAlex 缺失的代价**：无法做"谁引用了 VSCP / AURA"的全量正向核查。这是本轮最大的方法学缺口，**建议投稿前用机构 IP 或申请 OpenAlex 免费 key 重跑一次**（key 申请：`POST https://api.openalex.org/api-keys`）。

---

## 2. Task 2 — "评测协议"竞品集（精确对标）

### 2.1 总表

| 论文 | 精确主张（原文口径） | 测什么 | 场景/规模 | 碰不确定性/证书? | 留下什么没做 |
|---|---|---|---|---|---|
| **NerfBaselines**<br>[arXiv:2406.17345](https://arxiv.org/abs/2406.17345)<br>NeurIPS 2025 D&B | "even tiny differences in the evaluation protocols of various methods can artificially boost the performance of these methods. This raises questions about the validity of quantitative comparisons" [A] | PSNR/SSIM/LPIPS 在统一协议下重算；复现原论文数字（多数场景偏差 <1%）；把协议差异拆成可核查的因子：uint8 取整（≈±0.02 PSNR）、LPIPS 用 VGG 还是 AlexNet、是否用预降采样图像 | Mip-NeRF 360 / Blender / Tanks & Temples + 在线 leaderboard；**19 个方法**（其中 **12 个按官方说明装不上**）[F] | **无** | 无逐像素误差界；不涉及"资产被编辑/压缩之后"；无下游任务；无 distribution-free 保证；各数据集精确场景数未逐表核对（未取到） |
| **Mind the Gap**<br>[arXiv:2607.01556](https://arxiv.org/abs/2607.01556) | 标准 Mip-NeRF360 式"每隔 N 帧留出"的留出帧**两侧都有训练邻居**，因此度量的是 near-trajectory interpolation，不是空间泛化；提出 **matched-count paired protocol**（两臂训练图数相同，只改留出是"均匀铺开"还是"连续空间扇区"）[A] | 插值–外推差（**3–12 dB**，数倍于方法间常见差距）；对训练噪声稳健；在两个案例上**足以翻转方法排名**（多种子确认）；跨 3 个表示族（含非高斯 NeRF）持续存在；诊断为 diffuse/geometry-proxy 主导，**view-dependent color 占 38%**；与"到最近训练视角的角距离"单调相关 | **16 场景**（toolkit 标准化划分+baseline）；另有 10 场景/240 runs（采集规划）、6 场景（下游深度探针）、**9 场景**（SH 阶数分析）[F] | **无** | 无覆盖率/证书；"结构性"结论针对**你留出在哪**，不针对**资产变成了什么**；SH 阶数只做外推诊断，未与任何可靠性量挂钩 |
| **Martine**<br>[arXiv:2611.11602](https://arxiv.org/abs/2611.11602) | 现有多视图表面重建 benchmark 在视角覆盖、分辨率、光照上受限，或缺少精确 GT 与量化的 image-to-geometry 对齐，因而偏向特定方法 [A] | 受控采集下的**度量表面精度**；把"视角覆盖 / 分辨率 / 光照"作为显式轴 | **28 个物体**（26 个进入定量），含透明材质与细结构；其中 13 个物体 10 视角、4+3 个为 5 视角 [F] | **无** | 只测几何精度，不测渲染误差界；无编辑；无资产级证书 |
| **PIVOT**<br>[arXiv:2608.25401](https://arxiv.org/abs/2608.25401) | 现有 benchmark 用"对重建友好"的轨迹、优化过的位姿与内参、且留出视角来自训练轨迹本身，掩盖了机器人在实测位姿/可复用标定/结构不同相机路径下的真实表现 [A] | 把 pose / intrinsics / viewpoint 三因子**独立**拆开 | 多轨迹数据集 + 处理管线 + 评测框架；**精确场景数未取到**（摘要未给，HTML 正则未命中） | **无** | 同上；未涉及压缩/编辑后的资产 |
| **3DGS-SC**<br>[arXiv:2609.31756](https://arxiv.org/abs/2609.31756) | "高图像保真度是否意味着屏幕内容可读？"——保真度选型会失败 [A] | 整图保真 / 屏幕区保真 / **OCR 可读性** / 边缘保持，四层分离 | **10 个程序化场景**，固定多视划分、精确相机、屏幕掩码、文本标注 | **无** | 单一语义轴（屏幕文本）；不做不确定性 |
| **Underwater cross-regime**<br>[arXiv:2608.25483](https://arxiv.org/abs/2608.25483) | 3DGS 方法只在浅水/良像质条件下被验证过 [A] | 5 个有公开代码的系统在**同一协议**下跑：共享位姿、初始化、预算、评测器 | 多个公开水下数据集（不同浊度/照度/色衰减）+ 一个工业测量 [A]；精确场景数未取到 | **无** | 只给相对优劣，不做误差界 |
| **EditBench3D**<br>[arXiv:2609.14899](https://arxiv.org/abs/2609.14899) | 神经 3D 编辑常只用语义对齐评价，但"看起来对"可能改动了无关内容或跨视不一致 [A] | 4 性质：instruction fidelity / spatial locality / cross-view consistency / preservation；配对描述 + 留出相机 + 5 类编辑 | **40 场景 × 6 编辑 = 240 对**，8 个编辑器（NeRF/3DGS/hybrid/proxy）[F] | **无** | 评的是**编辑质量**，不是"编辑对某个已签发保证的影响" |
| **Calibration Audit**<br>[arXiv:2608.29705](https://arxiv.org/abs/2608.29705) | confidence 本为损失权重，从未验证能否当不确定度**幅度** [A] | 4 性质：误差排序、平均 error/unc 比、该比随 confidence 的斜率、**implied error distribution 的 coverage** | 7 backbone × 13 数据集 [A] | **部分（唯一一个碰 coverage 的）** | 无证书、无编辑、无下游任务；audit 对象是**不会被重签**的 confidence |
| **From Splats to Silicon**<br>[arXiv:2609.06157](https://arxiv.org/abs/2609.06157) | 效率收益被报在渲染/更新路径的不同点上，与端到端系统收益脱节 [A] | 把指标追溯到 Gaussian 选择、屏幕空间工作量、数据移动等环节 | 综述+方法学，未见统一实验规模（未取到） | **无** | 效率轴，非可靠性轴 |
| **CleanGS**<br>[arXiv:2601.00913](https://arxiv.org/abs/2601.00913) | 预训练 3DGS 会保留 capture 视角下不可见、reframing 后可见的 off-object 结构 [A] | **直接评测导出的资产**；提出 fixed-pose widened-field protocol | 未在摘要给出场景数（未取到） | **无** | 清理方法论文，不是评测论文；但"评导出资产"这一条我们要借 |

### 2.2 我们能站的位置（可直接改写进 Related Work）

三条硬事实：

1. **这一整个竞品集，没有一篇评测"资产被改动之后"的东西。** NerfBaselines 对齐的是**方法实现与协议**；Mind the Gap 对齐的是**留出几何**；Martine/PIVOT 对齐的是**采集条件**；EditBench3D 对齐的是**编辑质量**；3DGS-SC 对齐的是**语义轴**。**没有一篇把"证书"当成被评测对象。**
2. **但它们把"协议论文"的门槛抬高了**：matched-count 配对设计、多种子、跨表示族验证、诊断性归因（而不是只报一个差值）、公开 toolkit。我们现在的 400 次随机划分**在统计上比它们都强**，但**在"配对/受控"的叙事上弱**——我们改的是划分，不是受控因子。
3. **唯一正面冲突点是 coverage**：`2608.29705` 把 coverage 作为 confidence 的四个 audit 性质之一。我们必须引它，且必须说清"它 audit 的是信号幅度，我们 audit 的是保证在编辑下的存活性"。

建议的四句定位（英文，可直接用）：

> **vs NerfBaselines / Martine / PIVOT:** These works establish that *reported numbers* depend on protocol choices — implementation, holdout geometry, acquisition regime. We ask a different question: given a *guarantee* rather than a number, does the guarantee survive a change to the asset?
>
> **vs Mind the Gap:** [2607.01556] shows the standard holdout measures interpolation rather than generalization, a 3–12 dB effect that can flip rankings. Our finding is complementary in kind but opposite in sign of implication: the *certificate* is insensitive to some edits that hurt generalization (SH degree) and highly sensitive to others that barely move PSNR (pruning).
>
> **vs Calibration Audit [2608.29705]:** They audit whether a shipped confidence channel can be read as an uncertainty magnitude, and find it off by ≥2.4×. We audit whether a shipped *certificate* remains valid, and find it can be off by 10.8–27.7 coverage points. The two failures have different remedies: recalibration vs re-issuance.
>
> **vs EditBench3D [2609.14899]:** They show semantic fidelity is only weakly associated with locality, consistency and preservation — i.e. single-axis evaluation of *edits* misleads. We show the same for *certificates*: the coverage number is only weakly associated with downstream task success (4–11× disagreement).

### 2.3 一个必须处理的内部张力（审稿人会抓）

- **Mind the Gap 报告**："higher SH degrees hurting extrapolation on **3/9 scenes**"（bicycle、stump、treehill），且 view-dependent color 占插值-外推差的 38% [F]。
- **我们报告**：SH 降阶与 8-bit SH 量化对证书覆盖 **≈0 成本**。
- **这不是矛盾，但必须主动说明**：他们量的是**外推几何泛化**，我们量的是**留出视角上的逐像素误差覆盖**；两者对不同量的敏感度本来就不同。**如果我们不写这一段，审稿人会认为我们的 SH 结论与 2026 年最新协议论文冲突。**
- 另可借 `2608.30054` [A] 的机制解释：角容量无界时，错误的不透明 billboard 几何也能完美解释图像——所以**砍 SH 不一定增加渲染误差，但可能改变"哪种解被偏好"**。

---

## 3. Task 3 — CVIU 审稿人会要、而我们目前缺的

### 3.1 计数口径

- 样本：本轮扫到的 **18 篇** 2025-06 → 2026-11 的 3DGS/NeRF **评测 / 基准 / 协议 / 审计**类论文（含 NerfBaselines、Mind the Gap、Martine、PIVOT、3DGS-SC、EditBench3D、Calibration Audit、Splatwizard、GaussFlaw 等）。
- 方法：取 `arxiv.org/html/<id>` 全文 → 去标签 → 正则命中计数。**18/18 全部取到全文。**
- 口径警告：这是**关键词命中**，不是人读判据。命中≠做得扎实（例如"mentions uncertainty"里多数只是提一句）。表中已标注哪些是弱代理。

### 3.2 计数结果

| 成分 | 出现率 | 例子 | 我们的现状 | 补的成本 |
|---|---|---|---|---|
| **PSNR** | 15/18 | 几乎所有 | 有 | — |
| **SSIM** | 14/18 | NerfBaselines、Mind the Gap、PIVOT | **需确认是否进正文表** | 低（重算即可） |
| **LPIPS** | 13/18 | NerfBaselines（并明确 VGG vs AlexNet 的选择会影响可比性） | **大概率缺** | 低 |
| **标准 benchmark / 公开划分** | 12/18 | Mip-NeRF 360 / Tanks&Temples / Blender | 4 个公开 ckpt + 5 个自训练 | **中高**：审稿人会问"为什么只有 4 个公开资产" |
| **下游任务评估** | 10/18 | YUBI（quality→policy）、Mind the Gap（深度探针） | **强项（4 族任务）** | — |
| **per-scene / per-asset 表** | 9/18 | Mind the Gap、PIVOT、GaussFlaw | 需确认 | 低（9 场景逐场景表） |
| **代码发布（正文含 github）** | 7/18 | Splatwizard、Splats2Silicon、Underwater | **缺（CVIU 几乎必问）** | 中（要清理） |
| **运行时/效率分析** | 7/18 | Splats2Silicon、Splatwizard | 缺（重签成本可折算） | 低 |
| **ablation** | 6/18 | Mind the Gap、EditBench3D | 有（准则×预算） | — |
| **failure case 讨论** | 6/18 | Under-ice、EditBench3D | 缺（我们负面结果多，正好用） | 低 |
| **显式统计检验（CI / p 值 / bootstrap）** | 4/18（`ci/pval` 6/18） | Calibration Audit、VR 立体研究、YUBI、QA survey | **有 400 splits 但未形式化** | **极低，收益最高** |
| **多种子训练方差** | 3/18（显式写"3/5 seeds"的 **0/18**） | Mind the Gap、GaussFlaw、Underwater | 部分（400 划分≠训练种子） | 中（GPU 时间） |
| **用户研究 / 主观评测** | **1/18** | [2609.38525](https://arxiv.org/abs/2609.38525) VR 立体观看研究 | 缺 | 高；**但 1/18 说明不是硬门槛** |
| **limitations 段** | 13/18 | 普遍 | 有 | — |
| **appendix / 补充材料** | 9/18 | 普遍 | 有 | — |
| **算力/GPU 小时报告** | 3/18 | NerfBaselines、Splatwizard | 缺 | 低 |
| **license 声明** | 18/18 ⚠️ | — | — | **伪命中**：arXiv HTML 每页都有 license 页脚，此项作废，不构成证据 |

### 3.3 结论：CVIU 会问、我们最该补的四件事

按"审稿人提问概率 × 补齐成本"排序：

1. **统计检验形式化（最高优先，成本近零）**。我们已有 400 次随机标定/部署划分——这是竞品集里 18 篇只有 4 篇做到的东西。把它写成：bootstrap 95% CI + 配对检验（同一划分下编辑前后配对，用 paired bootstrap 或 Wilcoxon signed-rank）+ 报告效应量与 CI 宽度，而不只是点估计。**这一条能把"400 splits"从一句描述变成方法学优势。**
2. **代码与资产清单发布**。7/18 有 github；CVIU 的 reproducibility 期待比 TMLR 更硬。至少放出：9 个 ckpt 的哈希、编辑算子实现、划分生成脚本、评测算子。
3. **SSIM / LPIPS 两列**。不是为了证明我们更好，而是为了回答"你的编辑是不是只是把图变糊了"。预期叙事：**pruning 让 LPIPS 恶化有限，但覆盖率掉 10.8–27.7 点**——这正好强化"证书捕捉的是 PSNR 看不到的东西"。
4. **per-asset 表（9 场景 × 全指标）**。9/18 有；我们的 9 场景规模不大，但**必须逐场景可查**，否则"4+5 混合来源"会被质疑 cherry-pick。

**不建议补**：用户研究（1/18，成本极高，收益低）。若审稿人坚持，用"perceptual metrics + 明确的感知-证书对象区分"回应（我们已有这一段）。

### 3.4 一条针对"混合资产"的预判

竞品集里 12/18 使用标准公开 benchmark。我们 9 个场景中 5 个是自训练 BungeeNeRF。**审稿人大概率会问**：
- "自训练资产是否与公开 ckpt 同分布？"
- "结论在只用 4 个公开资产时是否成立？"

**建议预先在附录给出"仅 4 个公开 ckpt"的子集结果**，并报告子集与全集的效应量差异。这比被问到时再补强。

---

## 4. 对稿件的具体改动建议（按优先级）

| # | 改哪里 | 怎么改 | 依据 |
|---|---|---|---|
| 1 | Abstract / Intro 第一段 | **删掉**任何"首次观察到覆盖率大幅失效"的表述；改为"首次把失效**归因到资产编辑算子**，并给出剂量-反应、准则依赖、预处理依赖与任务解耦" | §1.2(1) |
| 2 | Related Work 开头 | 加一句"conformal 的失效源已被证明可以是评分函数本身 [2607.02565]，也可以是模型更新 [2610.28937]；本文补上第三类：**被签发的资产**" | §1.2(1)、既有 Doula 条目 |
| 3 | Related Work | **必须**新增 `2608.29705` 一段（audit confidence ≠ audit certificate），并**显式消歧两个 2.4×** | §1.2(2) |
| 4 | claim (v) 段 | 加 `2611.10063` 一句，并把我们的贡献从"发现自检撒谎"上移为"**证明它是构造性恒等**" | §1.2(3) |
| 5 | claim (iii) 段 | 引 `2607.13682`（variance≠error，共享误差机制）+ `2610.17521`（反向：quality→task 是有效的） | §1.1 #4、#13 |
| 6 | SH 结论段 | 加"与 Mind the Gap 的 SH 外推结论不矛盾"的说明 + `2608.30054` 的机制 | §2.3 |
| 7 | 剪枝准则段 | 把 Fisher 降级为**对照准则**，引 `2606.09074`（REFINE 才是"用准则预测移除误差"的强版本） | §1.1 #5、#20 |
| 8 | 实验节 | 加 bootstrap CI + 配对检验；加 SSIM/LPIPS 两列；加 9 场景逐资产表 | §3.3 |
| 9 | 附录 | 加"仅 4 个公开 ckpt"子集结果 | §3.4 |
| 10 | 投稿包 | 放代码 + 资产清单 + 划分脚本 | §3.3 |

---

## 5. 检索边界（必须与论文的 limitation 一致）

1. **OpenAlex 未取到（429）**，**Semantic Scholar 大部未取到（429）**。因此：
   - 无法做"谁引用了 VSCP / AURA / NerfBaselines"的全量正向核查（仅取到 1 条：Mind the Gap ← YUBI-Real2Sim）；
   - 无法覆盖非 arXiv 的期刊/会议版本（**CVIU、TPAMI、IJCV、3DV、BMVC 的正式版**）。
   这对**改投 CVIU** 是实质风险：CVIU 自己 2025–2026 的相关文章我们本轮基本没扫到。**建议补一次 DBLP + Scopus/Web of Science 检索**（校园网 IP），关键词沿用 §1.4 的表。
2. arXiv 服务端 `submittedDate` 过滤不可靠，已改为客户端复核；因此"窗口内总数"不可信，本文件**不给出候选计数**，只给出经筛选后的条目。
3. 摘要级阅读 20 篇 + 全文本机器统计 18 篇；**没有一篇做了逐段精读**。任何"某篇的某个小节其实做了类似测量"的可能，本轮无法排除。
4. 仅英文公开文献；未检索中文期刊、专利、学位论文、工业技术报告。
5. 标记为 **[T]** 的 2 条（`2609.09854`、`2603.05822`）**在引用前必须补读摘要**。
6. 时间戳：arXiv API 覆盖到 **2026-11-12** 当日；11-12 当天的新提交可能尚未进索引。
