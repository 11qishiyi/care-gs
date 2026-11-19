# JVCIR 版：题名 / 摘要 / Highlights / 贡献列表 / 骨架（v2 — 已落地为 15 页稿）

> **状态（2026-11-18）**：`main.tex` 已编译 **15 页**，**11 张表**全部由脚本从 artifact 生成（`--check` 逐字节一致），
> **2 张图**（框架图 + 率-可靠性/剂量曲线）由脚本生成，`tools/verify_jvcir.py` **九段闸门 PASS / exit 0**。
> 沉积包 `deposit_jvcir.zip`（42 项，435,679 B，**可复现逐字节相同**）已就绪。
> 只剩两项作者动作：Zenodo DOI + 竞争利益声明 `.docx`（见 `CHECKLIST.md`）。

> 依据：`review/JVCIR_SCOPE_2026-11.md`（7 篇近作的结构公约数）+ `review/JVCIR_GAP_ANALYSIS_2026-11.md`（差距与形态）
> + `experiments/J1_RESULTS.md`（新方法证据）。
> 目标：**首屏（标题+摘要+Highlights+Fig.1）在 15 天 triage 里被读成"一个方法"**，而不是"一次测量"。
> 数字全部来自 `experiments/` 与 `results_v120/`；任何未落盘的数字都不许写进来。

---

## 1 题名

**主选**：`CARE-GS: coverage-aware rate reduction for 3D Gaussian Splatting assets`

理由：JVCIR 的 3DGS 论文 6/6 用 `[方法名]: [做什么]`（`KF-GS: …`、`RDS-GS: …`）；方法名给审稿人一个"这是一项技术"的信号，
副标题把 scope 词（rate reduction / 3D）放到前 12 个词内。

备选（若审稿人偏好更保守）：
- `Rate reduction you can certify: coverage-aware compression of 3D Gaussian Splatting assets`
- `Coverage-aware rate planning for 3D Gaussian Splatting asset delivery`

**不用**问句标题、不用 `Valid but Unusable` 这类判决式标题（CVIU 版那个标题在 JVCIR 会被读成评论文章）。

---

## 2 摘要（≤250 词，当前 237 词）

> 3D Gaussian Splatting (3DGS) assets are shipped as files and then re-compressed by whoever receives them. Fidelity
> metrics — PSNR, SSIM, LPIPS — are the only budget sender and receiver share, yet they do not say what happens to a
> per-pixel quality guarantee. We show that the *action*, not its aggressiveness, decides whether a guarantee survives:
> within one point of per-pixel coverage loss, quantising a shipped asset reaches 9–16× rate reduction on six
> scene-checkpoints, while deleting primitives cannot reach 1.3× at all, and at a matched rate the pruning route costs
> 12.7–23.2 coverage points where quantisation costs 0.7–0.95. We turn this into a method, CARE-GS. A shared-basis
> container codes 45 spherical-harmonic coefficients through one rank-16 basis per asset, with smallest-three
> quaternions and per-stream alphabets (17.35× at −0.04 dB on bicycle; 5.2× at −0.1 coverage points). A coverage-aware
> planner picks the operating point against a tolerance ε from measured rates and a cross-asset prior; because that
> prior alone violates ε on two to three of six assets, the planner accepts a candidate only after an audit on the
> calibration views shipped with the asset — an audit that decides 56/56 cells with no false acceptance and needs no new
> labels. We report where we lose as well: at 19–28 MB the container sits 2.0–2.7 dB behind anchor-based coders, and we
> state the representation gap that causes it. Code, residual dumps and tables are archived with a DOI.

---

## 3 Highlights（5 条，每条 ≤85 字符，含空格）

```
Quantising a shipped 3DGS asset keeps a coverage guarantee; pruning does not.
Within 1 pp coverage loss, quantisation reaches 9-16x; pruning never reaches 1.3x.
At matched rate pruning costs 12.7-23.2 coverage points, quantisation 0.7-0.95.
One rank-16 colour basis per asset codes 6M Gaussians at 17.35x for -0.04 dB.
A 2-view audit on shipped views decides the tolerance with no false acceptance.
```

（前 85 字符就是 triage 时被读的全部内容，所以第 1、2 条必须是结论本身，不能是背景。）

---

## 3b Keywords（6 个，官方要求 1–7）

```
3D Gaussian Splatting; rate reduction; coverage guarantee; quality audit;
scene representation; visual data reduction
```

（scope 词 `visual data reduction` 必须出现——这是 JVCIR 研究领域列表里的原文用词。）

---

## 4 贡献列表（引言末尾，编号；按"第一眼能不能看懂"排序）

1. **问题重述与一个可判定的结论**：3DGS 交付的预算应当以**逐像素覆盖率容差 ε** 计，而不是以 dB 计；在同一 ε 下，
   **动作族**（量化 / 剪枝）而不是压缩强度决定可达码率。六个 scene-checkpoint 上：ε=1 pp 时量化 8.97–15.78×，
   剪枝**无任何可行点**；等码率下剪枝付 12.7–23.2 点（§5.2–5.3，`experiments/J1_RESULTS.md`）。
2. **共享基容器**：45 个 SH 系数走**每资产一个 rank-16 基**，加 smallest-three 四元数、逐流字母表与 Morton/zstd；
   实测 **17.35× at −0.04 dB**（bicycle，83.41 MB / 24.08 dB）、**5.2× at −0.1 pp**；解码 15.95 s / 4.27 GB（§5.1）。
3. **覆盖率感知规划器（CARP）+ 出货审计（CAV）**：规划器只用实测码率 + 跨资产先验；因为先验单独会 2–3/6 违例，
   候选必须过审计才被接受——审计 56/56 判决正确、零误放行、不需要新标签（§5.4–5.5，`experiments/J2`）。
   **审计本身不是新东西**（QuantileGS/VSCP/AURA 已有 3DGS 的保形界，跨模态已有"审计认证-实服差距"）：
   我们的主张是"**把审计当作规划器的验收测试**"以及"**审计只用随资产交付的标定视角 + 不变的 q**"。
4. **完整、可复现的比较**：8 资产 × 20 配置，PSNR/SSIM/LPIPS 三件套 + 覆盖率；与已发表格式在同字节下对撞
   （8 资产 32 配对，+2.87…+20.76 pp）；BD-rate −45.06 %（剪 50 %）；**并给出对 SOTA 的诚实差距**
   （等字节 +2.02/+2.72 dB，等 PSNR 无行）（§5.6）。

---

## 5 骨架（对齐 JVCIR 6/6 的结构公约数）

```
1  Introduction                      ← Fig.1 = 框架图（不是结果图）；末尾接 §4 的编号贡献
2  Related work
   2.1 3DGS representation and post-hoc coding
   2.2 Rate–distortion and coverage guarantees   （含 JVCIR 自刊 104682/104815/104978/104475；
                                                  以及 QuantileGS 2611.21253、VSCP 2609.10307、AURA 10.31224/7689）
   2.3 Asset delivery, editing and audits
3  Method
   3.1  The shared-basis container（+ 表：bitstream 语法/每流字母表/字节归属）
   3.2  The coverage certificate and its shipping audit（CAV；经验包络 + DKW 说明）
   3.3  Coverage-aware rate planning（Algorithm 1；复杂度；与 RD-贪心的区别）
4  Experimental setup
   4.1  Datasets（8 scene-checkpoint；协议白名单与 bonsai/treehill 的机械剔除规则）
   4.2  Metrics（PSNR/SSIM/LPIPS + 覆盖率 + 区间；BD-rate 定义）
   4.3  Baselines（已发表格式复现 6 条 / 同模型 5 种剪枝分数 / HAC-PCGS 的跨论文行）
5  Results
   5.1  Container RD and its byte attribution
   5.2  Rate–reliability frontier by action family
   5.3  Matched-rate collision
   5.4  Planners under a tolerance
   5.5  Does the audit decide the tolerance?
   5.6  Ablations: rank, quaternion coding, per-stream alphabets, bit-width ladder
   5.7  Cost: encode/decode time and memory
6  Limitations and future work        ← 写成路线图，不写成自我否定
7  Conclusion
CRediT · Declaration of competing interest · Data availability · Declaration of generative AI
```

---

## 6 与 CVIU 版的分工（避免一稿多投的观感）

| 项 | CVIU 版（审计为主体） | JVCIR 版（压缩为主体） |
|---|---|---|
| 主问题 | 证书在编辑后失效，且可被审计 | 率-可靠性预算下如何选动作与工作点 |
| 主表 | 56 格审计 + 包络 + 剂量曲线 | 率-可靠性前沿 + 等码率对撞 + 规划器 |
| 主图 | 编辑族 × 覆盖率 | 容器 + 规划器闭环 |
| 证书的角色 | 研究对象 | 方法的一个组件（C4） |
| 交叉引用 | 引用 JVCIR 版（若已公开） | 引用 CVIU 版（若已公开） |

同一批 `results_v120` 数字在两篇里都会出现，但**主张与主表不同**；投稿时在 cover letter 里主动说明这一点，
比等审稿人发现要好。

---

## 7 校验（写进 `tools/jvcir_compliance.py`）

- 摘要 **≤250 词**（本文件当前 244，随文改动后必须重跑）；
- Highlights **3–5 条、每条 ≤85 字符**；
- Keywords **1–7 个**；
- 正文不得出现 `\TBD`（除作者待补 DOI 一处，且用宏标出）；
- 每个正文数字必须能在 `experiments/artifacts/a4/*.json`、`results_v120/*.json` 或 `experiments/PAPER_NUMBERS.md` 里找到出处。
