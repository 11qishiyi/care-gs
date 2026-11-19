# 数据沉积：用 GitHub 可以，但必须再挂一层归档 DOI

**结论先给：不是"能不能用 GitHub"，而是"只有 GitHub 不够"。**

## 1 官方要求是什么

JVCIR 的 Guide for Authors 指定 **Option C**，原文（[Guide for Authors](https://www.sciencedirect.com/journal/journal-of-visual-communication-and-image-representation/publish/guide-for-authors)）：

> "For this journal, Option C instructions from our research data guidelines apply. This means that you are
> **required to**: Deposit your research data in a relevant data repository. Provide a link to the dataset during
> the submission process. If sharing your research data isn't possible, make a statement explaining why…"

[Elsevier research data guidelines](https://www.elsevier.com/researcher/author/tools-and-resources/research-data/data-guidelines)
对 Option C 的措辞只有两句：**存入"relevant data repository"** + **给出链接**。
Elsevier 另外明确把 **"software, code, models, algorithms, protocols, methods"** 都算 research data
（JVCIR 的 Guide 也照抄了这句），所以我们这个包里**代码本身就是要沉积的对象**，不是附属品。

**GitHub 的角色**：它是代码托管，不是归档仓库——没有持久标识、可被 force-push、可被删除。
Elsevier 的数据引用格式要求**带 DOI 的 `[dataset]` / `[software]` 条目**（Guide 里给了 Mendeley Data 的示例），
所以"只给一个 github.com/... 链接"在 production 阶段最常见的结局是被要求补 DOI。

**正确做法（也最省事）**：GitHub 当开发仓库 + **Zenodo 归档 GitHub release 自动发 DOI**。
Zenodo 的 GitHub 集成会对每个 release 生成一个版本 DOI，并给一个"全版本 concept DOI"，
引用时用 concept DOI 最稳（后续补版本不换号）。

## 2 三步操作（约 15 分钟，作者本人做）

1. **建仓库并推代码**：把 `submission/cviu/deposit/` 下的 `code/`、`data/`、`tables/`、`README.md`、
   `REPRODUCE.md`、`PROVENANCE.json`、`LICENSE` 原样推到 GitHub（建议仓库名 `gs-coverage-audit`）。
2. **接 Zenodo**：登录 [zenodo.org](https://zenodo.org)（可用 GitHub 账号）→ 右上头像 → **GitHub** →
   **Sync now** → 在仓库列表里把该仓库的开关拨到 **ON**。
   参考：[Quick Guide: Linking a GitHub Repository to Zenodo](https://zenodo.org/records/20428659)。
3. **发 release 拿 DOI**：GitHub 仓库 → Releases → **Draft a new release** → tag 例如 `v1.0.0` → Publish。
   几秒后 Zenodo 会给这个 release 一个 DOI（形如 `10.5281/zenodo.xxxxxxx`），并在仓库页显示 badge。
   **把 badge 的 concept DOI 抄给我**，我写进正文与 Data availability 两处。

## 3 我会怎么在正文里写（拿到 DOI 后直接替换）

```
Data availability
The code, the per-view residual dumps, the derived tables and the reproduction scripts that
support this study are archived at Zenodo (DOI: 10.5281/zenodo.XXXXXXX) and maintained at
https://github.com/<user>/gs-coverage-audit.
```

并在参考文献里加一条 `[software]` 条目（Elsevier 支持 `[dataset]` / `[software]` 标签）。

## 4 如果暂时不想公开代码

Option C 允许"不能共享则写明理由"，但那句话会**印在正式文章里**，是本刊最显眼的一处减分。
备选：只沉积 **数据 + 表格 + 复现脚本**（把 `code/` 里的训练/渲染入口保留、把依赖私有数据的部分标注为需申请），
仍然给 DOI。**这比"on request"强得多**——后者在该刊属于不合规写法。

## 5 我们包里已就绪的内容（`submission/cviu/deposit.zip`，28 项，159 kB）

| 目录 | 内容 | 用途 |
|---|---|---|
| `data/` | `audit_bound.json`（56 格审计）、`dump_summary.json`（9 资产 × 8 变体逐视角残差摘要） | 论文每张表的原始输入 |
| `tables/` | `tab_audit.tex`、`tab_fidelity.tex`、`tab_kview.tex`、`highlights.txt` | 与正文逐位一致 |
| `code/experiments/` | `dump_artifacts.py`、`audit_bound.py`、`region_coverage.py`、`extend_eval.py`、`run_cviu.sh`… | 从 PLY 到残差到审计 |
| `code/tools/` | `verify_cviu.py`(29 断言)、`cviu_gate.py`(四场景复现闸门)、`cviu_compliance.py` | 自检三件套 |
| `code/repro/` | `run_all.sh`（data/dump/analyse/verify 四段可续跑） | 一键复现 |
| 根 | `README.md`、`REPRODUCE.md`、`PROVENANCE.json`、`LICENSE` | 评审可直接读 |

**注意**：JVCIR 版（压缩为主体）与 CVIU 版（审计为主体）如果都要沉积，建议**两个仓库两个 DOI**，
不要用一个 DOI 同时挂两篇——评审会认为是一稿多投的迹象。
