# 3DGS 插件独立评审（awesome-gaussian-skills v0.9.12）

> 评审对象：`submission/final/main.pdf`（13 页，367,612 B）与 `submission/final/main.tex`
> 工具：DSH 插件 `awesome-gaussian-skills` 0.9.12（bundle `gaussian-skills-provider` + `gaussian-mcp-renderer`），
> 按 `skills/research-expert-team/SKILL.md` 的证据账本协议执行；知识库 `data/methods.json`
> （快照 2026-11-06，1066 条方法 / 26 类）与 `data/evidence-audit.json`（1066 条记录，959 条元数据已核）。
> 交叉核验：Crossref（DOI 解析）、arXiv abs 页、CVF Open Access、Semantic Scholar。
> 性质声明：这是"用插件知识库与协议做的结构化审阅"，不是同行评审；角色名只用于组织检查项。

---

## 一、结论（3 行）

**可提交**（在本文所列修改之后）：插件知识库没有找到任何"测量证书在编辑后失效"或"证书与下游任务解耦"的先行工作，
论文的贡献边界在其 1066 条方法索引内成立；实验与数字无需重跑。
但插件驱动的引文完整性检查抓到 **2 处元数据错误（LightGaussian、EAGLES 的标题与发表处均写错）**、
**2 篇缺失的直接近邻**（可证明剪枝 coreset、学习掩码剪枝）、**1 处未加限定的优先权措辞**——已全部修掉并重新验证。
插件自带的 3DGS 渲染 MCP（`3dgs-renderer`）当前不可用（`tsx` 未安装 → stdio 服务启动即退出），
且本轮没有留下本地检查点，因此**未做重渲染式的独立复算**；这是本次评审的边界，不是通过项。

## 二、证据账本（关键论断）

| 论断（类型） | 一次来源 | 位置 | 核验范围 | 判定 |
|---|---|---|---|---|
| 3DGS 证书类工作只有 AURA、VSCP、Manifold-GS 三个近邻（文献陈述） | 插件 `methods.json`（1066 条，2026-11-06）；Crossref/arXiv | §1、§4 "Certificates for splat assets" | 词面检索 `conformal/certif/coverage/exchangeability` | **支持**（4 条证书类记录：AURA 不在库内、VSCP、Manifold-GS、coreset 剪枝）；边界：库不完整 |
| "两个问题（失效幅度、证书量是否有用）尚未被一起测量"（优先权陈述） | 同上 + 最近邻全文摘要 | §1 第 3 段 | 只在插件库内做有界检索 | **部分支持** → 已改为 "to our knowledge" |
| AURA 的描述（per-carrier 可靠性、split-conformal、LOD 阶梯、AUC 0.58–0.72 vs 0.37–0.53、四场景、exchangeability 提醒） | engrXiv DOI 10.31224/7689（Crossref 解析：Krishi Attri，2026-07-25） | §4 第 1 段 | 摘要逐项比对 | **支持**（数字与限定均与原文一致） |
| LightGaussian 引用为 "compact representation, CVPR 2024"（文献事实） | arXiv:2311.17245 / 插件库 `metadata=checked` | 参考文献 | 标题+发表处 | **矛盾** → 已修（NeurIPS 2024，正确标题） |
| EAGLES 引用为 "continual level-of-detail, arXiv 2024"（文献事实） | arXiv:2312.04564 / 插件库（ECCV 2024） | 参考文献 | 标题+发表处 | **矛盾** → 已修（ECCV 2024，正确标题） |
| PUP 为 CVPR 2025（文献事实） | CVF Open Access（Hanson et al., pp. 5949–5958） | 参考文献 | 作者/标题/年份 | **支持** → 补页码 |
| 三条剪枝准则是"全部被测准则"（范围陈述） | 插件库 Compression 类 63 条 + `LinearMask-GS` | 表 3、§5 "What is not measured" | 词面检索 `importance.*prun` | **部分支持** → 局限段补学习掩码一族并引文 |
| 压缩侧的"保证"不覆盖证书（文献陈述） | arXiv:2607.02721（Mousa & Maalouf，coreset 定理） | §4 "Compression" | 摘要 | **支持** → 补引文并写明区别 |

## 三、角色发现

**R1/R2 — 最近邻与贡献边界。** 插件 1066 条索引里与本文最近的只有：VSCP（view-structured conformal）、
Manifold-GS（"certified" 指几何/拓扑）、AURA（per-carrier conformal + certified LOD）、
以及压缩侧唯一带"可证明"的 coreset 剪枝。四者的保证都指向**资产本身**（渲染目标、几何、载体可靠性），
没有人测量"签发后编辑"对覆盖率的影响，也没有人把覆盖率与下游任务并排测。
因此本文的差异是**有界且可被反驳的**："在 4 个已发布检查点、400 次划分、三类编辑、四族任务上，
证书的失效幅度与任务排序"——插件库内没有同题工作。建议（已执行）在正文把这一句写成可反驳的形式。

**R3 — 关键审阅。** 本轮没有新增"必须补实验"的指摘。插件库中"评估类"工作（E3VS-Bench、Fake3DGS 等）
是基准/检测方向，不构成对本文测量设计的反驳。表 3 新增的第三准则（opacity×volume 每个场景最差）
与库内"importance pruning"族一致（LinearMask-GS 的动机即"importance ranking 不稳"），不冲突。

**R5 — 出版完整性（本轮的主要产出）。**
1. `lightgaussian2024` 标题与发表处均错（写成 CVPR 2024 + "compact representation"）；
2. `eagles2024` 标题与发表处均错（写成 arXiv + "continual level-of-detail"）；
3. `lacuna2026` 缺 URL 与"research note"性质标注；
4. AURA 的 DOI/作者已通过 Crossref 独立解析确认，补 "engrXiv preprint"；
5. PUP 补页码 5949–5958；
6. **知识库覆盖缺口**：PUP（CVPR'25）与 AURA（engrXiv）都不在插件的 1066 条库内——
   说明"库内查不到"不能当作"不存在"，这也正是插件协议要求的"有界检索不等于新颖性"。

**R6 — 论证一致性。**
- 优先权句 `have not been measured together` 未加限定 → 改为 `have, to our knowledge, not been measured together`；
- AURA 段的数字与限定与原文一致（0.58–0.72 / 0.37–0.53 / 四场景 / exchangeability 提醒），无需改；
- 压缩段原先把 PUP/LightGaussian/EAGLES 一句带过，未提"可证明剪枝"这一支 → 已补 coreset 与学习掩码，
  并明确"它们的保证约束的是剪枝对渲染目标的影响，不是签发后的证书"。

**R9 — 结果解释。** 与本插件无关（本文数字来自 `results_v70/v80/v90`，已由 405 条断言与独立审计覆盖）；
本次评审未改任何数字、未改任何表格数据。

## 四、已应用的修改（均已重编译并验证）

| # | 位置 | 修改 | 验证 |
|---|---|---|---|
| 1 | 参考文献 `lightgaussian2024` | 标题 → "Unbounded 3D Gaussian compression with 15x reduction and 200+ FPS"；CVPR → **NeurIPS 2024** | arXiv:2311.17245 + 插件库 |
| 2 | 参考文献 `eagles2024` | 标题 → "Efficient accelerated 3D Gaussians with lightweight encodings"；arXiv → **ECCV 2024** | arXiv:2312.04564 + 插件库 |
| 3 | 参考文献 `lacuna2026` | 补 "Research note" 与站点 `lacuna.tiptreesystems.com` | 网页原文 |
| 4 | 参考文献 `attri2026aura` | `engrxiv` → `engrXiv preprint`（DOI 已独立解析确认） | Crossref 10.31224/7689 |
| 5 | 参考文献 `hanson2025pup` | 补页码 5949–5958 | CVF Open Access |
| 6 | §4 Compression | 新增 coreset 剪枝（Mousa & Maalouf, arXiv:2607.02721）与学习掩码剪枝（Ryu et al., BMVC 2026, arXiv:2609.10095），并写明与本文保证对象的区别 | arXiv 摘要 |
| 7 | §5 What is not measured | "learned importance score" → "a learned mask [Ryu et al., 2026]" | — |
| 8 | §1 第 3 段 | 优先权句加 "to our knowledge" | — |
| 9 | 新增 2 条参考文献 | `mousa2026provable`、`linemask2026`（元数据逐项核过） | arXiv / BMVC |

重编译与打包结果：`tools/verify_tex_v3.py` → **405 断言、0 失败**；补充材料解压后零配置 **405/0**；
`tests/test_new_tools.py` 11 条全过；`SOURCE_DATE_EPOCH=1700000000` 双遍编译与投稿 PDF **逐字节相同**；
PDF 13 页、367,612 B、Overfull/Underfull 0/0。

## 五、未检查项与边界（插件协议要求显式声明）

1. **未做重渲染复算**：插件的 `gaussian-mcp-renderer` 以 stdio 启动
   （`node --import tsx ./mcp-server/src/index.ts`）。评审开始时插件包内未安装 `tsx`，服务启动即退出，
   DSH 侧显示 `server is disconnected`；评审过程中已在该包内 `npm install tsx --no-save`（4.23.15）并验证
   服务可启动：`[3dgs-mcp-renderer v0.8.0] 21 core + 13 experimental tools，renderer bridge :9842`。
   但本轮检查点只存在于**已释放**的租用节点上，本地没有 PLY，因此"用 3DGS 渲染器独立重算覆盖率"
   这一路径仍然不可行；需要重跑才能做，属下一轮算力任务。
   若 DSH 仍显示 disconnected，重启一次 DSH（插件进程在启动时拉起）或 `npm run build -w mcp-server`
   后把 patch 的 `args` 改为 `dist/index.js`。
2. **文献检索是有界的**：库快照 2026-11-06、1066 条、26 类，且不含 PUP/AURA 这类非 arXiv 或早期会议工作；
   "库内无同题"只说明**在本次检索范围内**没有先行工作，不构成全球新颖性证明。
3. **未核 AURA 全文**：只核了 Crossref 元数据与摘要级数字（AUC、场景数、exchangeability 提醒），
   未逐条核其证书定义与本文 §2 的对象是否严格同构——这一点已在正文用"不同对象"的措辞限定。
4. **未使用插件的其他技能**（`3dgs-code-reviewer`、`3dgs-visualizer`、`3dgs-training-debugger`）：
   本文没有训练/硬件代码路径，代码审查不适用；可视化的独立复算同样受第 1 条限制。

## 六、给作者的两条建议（可选，非阻断）

1. 若要进一步加强相关工作，可在"Certificates"段末尾补一句"三个证书对象（per-pixel marginal、per-carrier
   mean-unreliability、view-structured）不可互换"，插件库与三篇原文支持这一区分；本文已有此意，但分散在 §2/§4。
2. `Manifold-GS` 与 `VSCP` 的条目缺作者列表（只有标题）；若能确认作者，补上会减少"机器生成条目"的观感。
