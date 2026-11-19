# JVCIR 最佳科研实践：调研、差距、本轮落地的改动（2026-11-18）

> **这份文件回答三个问题**：① 最近投到 JVCIR 的东西长什么样（可核查的分布，不是印象）；② 我们和它差在哪、
> 差多少；③ 这一轮实际改了什么、由什么闸门保证不再退化。
>
> 证据来源与复现命令：
> - 语料统计（新，可复现）：`python tools/jvcir_survey.py` → `review/JVCIR_SURVEY_2026-11.md`
>   （OpenAlex，ISSN 1047-3203，2025-01-10 … 2026-11-10，`article` **514** 篇）。
> - 逐篇全文解剖（本轮新增 8 篇 2026 年 8–11 月论文）：下称 **A 组**（105015 / 104996 / 104978 / 104977）与
>   **B 组**（104966 / 104995 / 105024 / 105027）。
> - 期刊硬规则：`review/JVCIR_SCOPE_2026-11.md`、`review/JVCIR_EDITORIAL_REQUIREMENTS.md`。
> - 我方状态：`tools/verify_jvcir.py` 的 11 段闸门输出（本轮扩到 11 段）。

---

## 0 一句话结论

**我们的差距不在证据，在"体例的完成度"和"少数几处自相矛盾"；这一轮把后两件基本闭合了。**
语料上，JVCIR 2026 的 `article` 篇均参考文献中位数 **49（Q1 38 – Q3 58）**，标题用 `方法名: 说明` 的占 **35%**，
OA 占比 **25%**；同族的 3DGS 线 **11 篇全是训练/重建侧模块增量**，压缩线 **8 篇全是经典点云/视频编码工程**——
**3DGS 压缩在这个刊仍是空位**，而我们正好站在那个位置上。
逐篇解剖揭示的关键事实与旧稿的判断相反：**"Limitations 独立成节"并不是该刊的公约数**（8 篇里 2 篇独立成节、
1 篇并入 Discussion、5 篇没有），**图 1 = 框架图**才是（A 组 3/4、B 组 1/4 明确，另 1 篇用失败案例当图 1），
**图数 5–12**、**参考文献 30–62**、**代码/数据声明 8 篇里只有 1 篇写了**（而且写在摘要里）。

---

## 1 调研方法与它的天花板（先说清楚，免得被读成更强的主张）

| 证据 | 能支持什么 | 不能支持什么 |
|---|---|---|
| OpenAlex 全量（n=514） | 篇数、月度节奏、参考文献分布、OA 占比、标题命名体例、主题分布、同族论文清单 | **摘要词汇**：Elsevier 不向 Crossref/OpenAlex 交付本刊摘要（本窗口仅 33/514 有可解析摘要），所以"他们报不报 PSNR"这类问题不能从语料答 |
| 8 篇全文/半全文解剖（2026-08…11） | 图数、图 1 类型、小节骨架、Limitations 形态、代码/数据声明位置、是否有主观实验 | **表数**（Elsevier 把表渲染成 HTML，不生成图片资源；付费墙内看不到） |
| 期刊 Guide + Insights | 摘要 ≤250 词、Highlights 3–5×≤85 字符、关键词 1–7、Option C 数据沉积、单盲、首决中位 15 天 | 具体领域审稿人的口味 |

**本轮修正的一条旧结论**：`review/JVCIR_SCOPE_2026-11.md` §2.1 写"7/7 篇都有 Limitations and future work 独立节"。
按本轮 8 篇英文原文核对，**独立成节的是少数**（104996 有；105015 并入 §5 Discussion；其余 6 篇没有）。
结论不变（写 Limitations 不吃亏，且我们有两个预注册判据失败必须交代），但**它是加分项，不是门票**。

---

## 2 该刊的"最佳科研实践"清单（10 条，逐条给证据与我们的状态）

| # | 实践 | 该刊证据 | 我们（本轮之后） | 判定 |
|---|---|---|---|---|
| P1 | **图 1 = 管线/框架图**，不是 teaser、不是结果图 | A 组 3/4、B 组 1/4；共 5/8 明确 | `fig1_framework.pdf`，第 1 页引言末尾 | ✅ |
| P2 | **5–12 张图**，其中至少一张"结果图"承载主结论 | 105015=5、104996=7、104978=12、104977=5 | 3 张 → **5 张**（新增审计判决图、dB≠coverage 图） | ✅ 本轮闭合 |
| P3 | **Highlights 4–5 条**，单句、不带引用、不带单位堆叠 | A 组 4/4 | 5 条，77–82 字符 | ✅ |
| P4 | **摘要 150–200 词、无引用、结尾落在有界的实证主张** | A 组 4/4 在 150–200 区间 | 239 词（硬上限 250 内，按信息密度刻意保留） | ⚠️ 合法但偏密，已记录为决策 |
| P5 | **关键词 3–4 个** | A 组 3–4 | 6 → **5** | ✅ 本轮收紧 |
| P6 | **实验节内用 run-in 小标题**（Dataset / Metrics / Implementation），不强行拆成独立编号节 | A 组 3/4、B 组 3/4 | `Assets and protocol / Metrics / Baselines / Reproduction` 四个 `\subsection` | ✅（比该刊更规整） |
| P7 | **参考文献 30–62**，且引该刊自己的簇（闭环） | 语料 Q1 38 / 中位 49；A 组 32–62；B 组 24–56 | 43 → **48**，其中**该刊 14 条**（3DGS 5 + 编码 5 + 质量评估 4） | ✅ 本轮闭合 |
| P8 | **代码/数据声明**：该刊多数不写；写了就是加分 | 8 篇里 1 篇（MJND-CPC，写在摘要里） | **Option C 全套**：沉积包 + 逐文件哈希 + 一键复现 + 闸门 | ✅（显著高于该刊中位） |
| P9 | **复杂度/时间轴**只在"速度是卖点"时报；报了就成卖点 | B 组 104995 报 FPGA 资源与 757 mW；其余不报 | `tab_cost`：编/解码墙钟 + 峰值显存 + 一次审计渲染 10.6 s | ✅ |
| P10 | **主观实验**只在"它就是贡献"时做（JND 数据集类） | B 组仅 105027 有主观标签；A 组 0/4 | 不做，写进 Limitations 并引该刊 JND 线 | ✅ 与刊例一致 |

**结构性结论**：JVCIR 不是"低标准刊"，而是**"完成度刊"**——它接受 modest improvement（105015 自认 systems-level）、
接受 objective-only（B 组 3/4）、接受无代码（8 篇里 7 篇），但**不接受"看起来不像一个方法"**。
我们的强项（400 次划分、配对 bootstrap、预注册、可复现闸门）在这个刊里是**超出中位**的；需要补的是**呈现层的完成度**。

---

## 3 数据化差距表（本轮之前 → 本轮之后）

| 维度 | 该刊参照 | 本轮之前 | 本轮之后 | 证据/闸门 |
|---|---|---|---|---|
| 图数 | 5–12（中位 ~6） | 3 | **5** | 闸门 §6 检查每个 `\includegraphics` 的 PDF+≥300 dpi PNG |
| 参考文献 | Q1 38 / 中位 49 | 43 | **48**（该刊 14） | 闸门 §11：`n_bib >= 2026 Q1`，值取自 `review/JVCIR_SURVEY_STATS.json` |
| 关键词 | 3–4 | 6 | 5 | 闸门 §1（1–7） |
| 图形摘要 | 1/8 有；Elsevier 鼓励 | 无 | **有**（`figures_j/graphical_abstract.pdf/.png`） | 不在正文，随投稿单独上传 |
| 段落重复 | — | §2.2 有一整段逐字重复 | 已删 | **闸门 §10 新增**：正文段落不得出现两次 |
| 数值自洽 | — | 摘要 `1.0–3.7 dB`、引言 `3.0–3.6 dB`、正文 `2.89–3.62 dB` 三套说法 | 统一为 **`0.96–3.62 dB`**（四个已发表编码器，bicycle，各自操作点）+ `6.25 dB`（stump/HAC） | **闸门 §10 新增**：正文引用的区间必须等于 `j3_ablations.json` 算出的区间 |
| 过度主张 | — | "两个配置相差 0.1 dB 却差 20 个覆盖率点"（无出处） | 改为实测 **0.10 dB / 6.2 点（stump）**，由 `fig4_decibel` 脚本算出并写进 `j5_fig_decibel.json` | **闸门 §10 新增**：该数字必须等于脚本产物 |
| 命名方法无引文 | — | EAGLES、LightGaussian 在正文被点名但无 `\cite` | 两条均补（DOI 已核） | 闸门 §4 无孤儿/缺失键 |
| 参考表显示 | — | 20 条 `author = {方法名}` 与标题重复，排版成 "KF-GS, KF-GS: …" | 已从 bib 删去重复的 author 伪字段 | `main.pdf` 目视 + bibtex 无 "empty author" |
| 引用完整性 | — | 无人核对 DOI/arXiv 是否指向同一篇 | **`tools/verify_refs.py`**：17 个 DOI 走 Crossref、22 个 arXiv id 走 arXiv API，标题 token 重合 < 0.6 即失败 | 闸门 §11 调它（`--net` 走网络） |
| 数据可用性 | Option C 硬门槛 | 两个 `\TBD{}`（Zenodo DOI / GitHub URL） | **仍是两个**——只能由作者上传后填 | 闸门 §2 只允许这两处 |

---

## 4 我们比该刊中位强的地方（同样要钉住，否则下一轮会被"防御性写作"改掉）

1. **统计严谨度**：8 个 scene-checkpoint、400 次随机划分、配对 bootstrap、固定诊断设置下复评；该刊同族论文 0/11 报置信区间。
2. **可复现闸门**：`tools/verify_jvcir.py` 11 段，含"表逐字节重生成""每个数字能在 artifact 找到出处""正文与 artifact 数值一致"。
   该刊 8 篇里 1 篇给代码链接。
3. **诚实差距表**：`tab_gap` 是**算出来的**（0.96–3.62 dB / 6.25 dB），不是叙述的；审稿人不必替我们发现。
4. **两条预注册判据失败**照实报告（J4 的 C2/C4），并据此撤回一个细主张、补一个 caveat。
5. **视角级测量**：干净模型上名义 90% 的逐像素保证只覆盖 72% 的视角——这是把"逐像素 ≠ 视角"从引用变成实测。

---

## 5 本轮实际落地的改动（可核查）

| 改动 | 文件 | 验证 |
|---|---|---|
| 删除 §2.2 重复段落 | `submission/jvcir/main.tex` | 闸门 §10 `70 paragraphs`，无重复 |
| 摘要：`1.0–3.7` → `0.96–3.62`，并修掉一处缺主语病句 | `main.tex`（abstract） | 闸门 §1（239 词 ≤250）+ §10（区间=artifact） |
| 引言/§2.1 的 gap 区间统一 | `main.tex`（§1 Scope、§2.1） | 闸门 §10 |
| §2.2 的 "20 个覆盖率点" → 实测 `0.10 dB / 6.2 点` | `main.tex`（§2.2）+ `j5_fig_decibel.json` | 闸门 §10 |
| 新增 **图 3**（审计 vs 先验，56 格）+ 图注 | `tools/jvcir_fig_audit.py` → `figures_j/fig3_audit.*` | 闸门 §6；`j5_fig_audit.json` 记录 2.04 pp / 3.42 pp / 0 vs 4 误放行 |
| 新增 **图 4**（dB≠coverage，双面板）+ 图注 | `tools/jvcir_fig_decibel.py` → `figures_j/fig4_decibel.*` | 闸门 §6/§10 |
| 新增 **图形摘要** | `tools/jvcir_fig_graphical.py` → `figures_j/graphical_abstract.*` | 不在正文；随投稿上传 |
| 参考文献 43 → 48（EAGLES、LightGaussian、该刊 3 条质量评估线） | `submission/jvcir/refs.bib` + `main.tex` §2.2/§5.9 | 闸门 §4/§11 |
| 删掉 20 条重复的 `author` 伪字段 | `refs.bib` | bibtex 无 empty author；目视参考表 |
| 关键词 6 → 5 | `main.tex` | 闸门 §1 |
| **引用完整性工具** | `tools/verify_refs.py` → `review/REFS_VERIFY.json` | 48 条全过（17 DOI + 22 arXiv） |
| **语料统计工具** | `tools/jvcir_survey.py` → `review/JVCIR_SURVEY_2026-11.md` + `JVCIR_SURVEY_STATS.json` | 可 `--refresh` 重跑 |
| **闸门扩到 11 段** | `tools/verify_jvcir.py`（新增 §10 prose、§11 refs；§6 动态发现图） | `PASS — every automated JVCIR gate`，20 页 |

复现全链：

```bash
python tools/jvcir_survey.py               # 语料统计（缓存命中则不联网）
python tools/jvcir_fig_audit.py            # 图 3 + j5_fig_audit.json
python tools/jvcir_fig_decibel.py          # 图 4 + j5_fig_decibel.json
python tools/jvcir_fig_graphical.py        # 图形摘要
python experiments/j3_ablations.py --check # 数字出处
python tools/jvcir_tables.py               # 12 张表
cd submission/jvcir && pdflatex main && bibtex main && pdflatex main && pdflatex main
cd ../.. && python tools/verify_jvcir.py    # 闸门（加 --net 连 DOI/arXiv 一起核）
python tools/make_deposit_jvcir.py         # 沉积包
```

---

## 6 仍未闭合的缺口（按"每 ¥ / 每小时换来的录用概率"排序）

| # | 缺口 | 为什么仍然重要 | 代价 | 建议 |
|---|---|---|---|---|
| G1 | **Zenodo DOI + GitHub URL** 两个 `\TBD{}` | Option C 是硬门槛；没有它稿子可能在技术审查就被退回 | 作者 10 分钟 | **投稿前必做**（步骤见 `review/DATA_DEPOSIT_GITHUB_ZENODO_2026-11.md`） |
| G2 | **定性渲染对比图**（GT / ours / HAC / PCGS 局部放大） | 该刊压缩类论文的默认配图；我们现在 5 张图里没有一张"看图就懂质量" | 一次 MatPool A100 轮（≈1 h，≈¥3）+ 归档重建 | 值得做；协议要先写死（同一视角、同一放大框、同一 GT 约定） |
| G3 | **第四个跨论文场景** | 现在只有 bicycle/stump 能对上 HAC/PCGS | 需其 checkpoint + 一次 GPU 轮 | 不做也不影响主张；做了可把"两场景"的限制降级 |
| G4 | 摘要 239 词（刊例 150–200） | 只是密度偏好，不是规则 | 改 30 分钟 | 保留：信息密度是 triage 的资产，硬上限是 250 |
| G5 | 与 PLEDGE 的**确定性逐属性界**同图对照 | 把"不同对象"变成"可同图比较" | 需其代码（未公开） | 写进 future work（已写） |

---

## 7 闸门现在强制什么（这是"最佳实践"真正落地的地方）

`python tools/verify_jvcir.py` → 11 段，任一失败 exit 1：

1. 合规（摘要 ≤250 词 / 关键词 1–7 / Highlights 3–5×≤85 字符）
2. 占位符（只允许 DOI/URL 两处）
3. 结构（每个 `\input`、每个 `\includegraphics` 目标必须存在）
4. 引文（每个 `\cite` 在 bib 里；bib 无孤儿条目）
5. 表（12 张表逐字节重生成一致）
6. 图（**动态发现**正文所有图；每张要 PDF + ≥1200 px 宽的 PNG）
7. 出处（`j3_ablations.py --check`：每个印出来的数字有 artifact）
8. 构建（PDF 比所有源文件新、≥8 页、无未定义引用）
9. 主张（16 个正文关键数字必须出现在承载它的表里）
10. **正文（新）**：不得有重复段落；正文引用的 gap 区间必须等于 artifact 算出的区间；dB/覆盖率主张必须等于图脚本产物
11. **参考文献（新）**：条数不得低于该刊 2026 年下四分位（现 38）；`tools/verify_refs.py` 结构检查（`--net` 时连 DOI/arXiv 一起解析）

**设计原则**：闸门只检查"能机械判定"的东西。它不评价文笔、不评价创新性，但它把"数字与正文不同步"这类**最容易被审稿人抓到的硬伤**
变成不可能——本轮它抓到的第一个问题就是 §2.2 那段重复。
