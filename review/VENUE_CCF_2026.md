# CCF 目录（第七版，2026-03）与本文的适配（2026-11-12）

> 目的：回答"有没有 CCF 目录内、比 TMLR 更适合这篇论文的期刊"。
> 关键前提：现行目录是 **第七版（2026-03 公示/正式发布，ICLR 升 A、IJCAI 降 B、TMM 升 A）**，不是 2022 版。
> **TMLR 不在该目录内**（子代理逐条核对第七版全表；Lead 抽查未发现 TMLR 条目）。所以"继续投 TMLR"= CCF 计数为 0。

## 1. 相关期刊的 CCF 等级与"收不收纯测量稿"

| 刊物 | CCF 2026 | 收无方法/无数据集的测量稿？ | 官方周期 | 备注 |
|---|---|---|---|---|
| TPAMI | A | 否（要方法/理论突破） | 未取到 | 4 场景时代的旧判断仍成立 |
| IJCV | A | 边缘（survey/benchmark 需新洞察） | 未取到 | 先例多为 55 场景级大网格 |
| ACM TOG | A | 否（SIGGRAPH 式） | 未取到 | — |
| IEEE TIP | A | 边缘 | 未取到 | QA 类通常要新库/新指标 |
| **IEEE TVCG** | **A** | **是**（评估/不确定性是本刊常规体裁） | 初审≈3 月、见刊≈7 月 | 先例：uncertainty-visualization 综述与评估研究 |
| **IEEE TMM** | **A（2026 新升）** | 边缘（benchmark 稿常捆数据集+方法） | 未取到 | 升 A 后竞争会更激烈 |
| IEEE TCSVT | B | 边缘 | 未取到 | 3DGS 压缩主场，但要码流立场 |
| **CVIU** | **B** | **是**（comparison/empirical 是正规体裁） | 审后决定 94 天、投稿→录用 201 天 | 先例：IBims-1 深度方法比较、超分×伪装目标检测比较 |
| Pattern Recognition | B | 边缘（创新性压力最大） | 未取到 | 20 页起 |
| **CVMJ**（Computational Visual Media） | **B** | **是**（纯感知评估刚发过） | 首决 28 天、录用 93 天 | 先例：CVMJ 12(4) 2026 的 24 人感知评估；OA 由清华赞助 |
| The Visual Computer | C | 是 | 首决中位 3 天（多为 desk） | 兜底 |
| Computers & Graphics | C | 是 | 未取到 | 兜底 |
| JVCIR / MVA | C | 是 | 未取到 | 兜底 |
| JMLR | A | 否（只收 tutorial/survey 例外） | 未取到 | ML 方向目录内只有 JMLR 在 A |
| Machine Learning (Springer) / Neural Networks / TNNLS | B | 否/边缘 | 未取到 | 与"无定理测量"不匹配 |

**不在目录**（逐条核对）：TMLR、DMLR、IEEE TCI、JMIV。

## 2. 三个可选落点

1. **CVIU（B）— 改动最小的 CCF 落点**：把"四把尺子差 4–11 倍"从观察升格为方法论主张（给评测协议/选尺建议），其余几乎不动；场景数已从 4 扩到 9，超过该刊同类先例的规模。周期有官方数字可写进 cover letter。
2. **CVMJ（B）— 最可能最快被接收**：3DGS 主场、纯评估稿有直接先例、93 天录用、零 APC；需补一小段"编辑后可用性判据"叙事，可选加小规模用户验证。
3. **TVCG（A）— 唯一现实的 A 类**：需要加一个感知/从业者研究（"人看不出、证书已失效"正是它的落点）+ 更多编辑器/资产来源；周期最长。

## 3. 与 TMLR 的取舍

| 目标 | 选择 | 代价 |
|---|---|---|
| CCF 计数 + 最小改动 | **CVIU（B）** | 换 Elsevier 模板与叙事，实验已够 |
| CCF 计数 + 最快 | **CVMJ（B）** | 换模板 + 小段叙事；受众偏图形 |
| CCF A 类 | **TVCG（A）** | 加感知研究，周期 7 个月+ |
| 最可能接收（不看 CCF） | 现稿投 **TMLR** | CCF 计数为 0 |

> 注：本文件只做决策依据，不改论文。等级来自第七版目录的公开转载与子代理逐条核对；TMLR 缺席这一点建议投稿前再对一次 CCF 官网 PDF 原件。

---

## 4. CCF-C 类补充（子代理核对第七版官方 PDF，2026-11-12）

第七版目录的官方 PDF（P44–P47 图形学与多媒体、P54–P56 人工智能）逐条核对结果：

- **图形学与多媒体 C 类**：TVC、C&G、JVCIR、MTAP、SPIC、IET-IPR
- **人工智能 C 类**：MVA、Neurocomputing、PRL、IET-CVI
- **Journal of Electronic Imaging 不在目录里**（不是 CCF-C）
- **MTAP 仍在目录里，但 2024-10-22 被 SCIE Editorial De-listing**（2024-03 先 On Hold、曾入中科院预警）→ CCF-C 与 SCI 脱钩，国内评价基本不可用

| 刊 | 官方周期 | 同类"无新方法"先例 | 判断 |
|---|---|---|---|
| **Computers & Graphics** | 首决 1 天／送审后 42 天／**录用 91 天**／上线 12 天 | *3D reconstruction and precision evaluation of industrial components via GS*（2025） | **首选**：双盲、有 GRSI 复现徽章，一键复现脚本正好对口 |
| JVCIR | 首决 15 天／**录用 215 天** | *Evaluation of objective quality metrics for multidimensional video scalability*（2016） | 安全垫；大概率要感知指标 |
| The Visual Computer | 首决 3 天／录用未取到；2025 年 540 篇 | *Occluded person re-ID: taxonomic survey + reproducible empirical benchmark*（2026） | 备选；首决 3 天=秒拒多，署名说服力弱 |
| MVA | 首决 30 天 | *Evaluation of visual saliency algorithms in noisy images*（2016） | 需机器视觉应用锚 |
| IET Image Processing | 未取到（~6 个月，未核实） | 水下图像质量评估综述（2025） | 全 OA 需 APC |
| **MTAP** | 首决 34 天 | 色彩量化质量度量评估（2021） | **不投**：SCI 除名 |
| **SPIC** | 首决 15 天／送审后 198 天／**录用 436 天**；**官方录用率 9%** | 点云压缩质量评估（2024） | **不投**：最差性价比 |
| PRL | 录用 196 天 | GNN 重连经验评估（2025） | 要压成 letter + "方法/重要新应用"，易 desk reject |
| Neurocomputing | 录用 139 天；2025 年 2711 篇 | 3DGS 综述（2025） | 偏方法，会被要新算法 |

**C&G 版改造清单（实验不需重做）**：elsarticle 单栏 12–16 页；108 格扫描表进 supplementary；双盲去标识；
叙事改为"3DGS 资产管线中的质量元数据在编辑后失真"；cover letter 交代与 AURA/VSCP/DP-Splat 的差异；
`repro/run_all.sh` + 494 断言打包申请 GRSI 徽章。可能需要补的只有感知指标（LPIPS/SSIM 需重渲，约 20–30 分钟 GPU、¥3）。

> 本补充只用于决策，不改论文。周期与先例出处见子代理汇报（ScienceDirect journal insights / Springer journal pages / Crossref 年发文量）。