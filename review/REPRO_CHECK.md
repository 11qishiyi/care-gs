# TMLR 投稿包复现性核验报告（REPRO_CHECK）

- 核验人：teammate `repro-final`
- 核验时间：2026-11-10 21:35–21:45（Asia/Shanghai）
- 核验对象：`D:\3dsg_1\submission\final\`（`main.pdf` / `main.tex` / `supplementary.zip`）
- 参照：`submission\main_v3.tex`、`tools\verify_tex_v3.py`、`results_v70\`、`research\results_v*\`、`SUBMISSION_CHECKLIST.md`
- 未改论文、未改原始数据；所有解压/编译都在 `D:\3dsg_1\_repro_tmp\` 里做

## 0. 结论速览

| 项 | 内容 | 判定 |
|---|---|---|
| 1 | 数字校验器（运行 + 是否校的是投稿 tex） | **条件 PASS**（205/0，但先前的路径指向是隐患；核验期间已被他人修正） |
| 2 | 补充材料自洽性（能否直接跑、数据覆盖、匿名） | **FAIL**（原样解压跑不起来；数据本身完整） |
| 3 | 图表可重建 | **部分 FAIL**（fig_three 可重建；fig_dose 包内既无脚本也无文件） |
| 4 | 论文 Reproducibility 段自述 | **FAIL**（"逐值断言"、"记录来源"、"单命令下载 archive" 均不成立） |
| 5 | PDF 与源一致（重编译） | **PASS** |
| 6 | `SUBMISSION_CHECKLIST.md` 与磁盘一致 | **基本 PASS**（3 处细节错） |

细分小项计数：**34 项检查 → 21 PASS / 13 FAIL**（FAIL 清单按严重性列在第 7 节）。

一句话：**"artifact → 论文数字" 这一段能复现（205 条断言 0 失败，图表和表格都能从 `results_v70/` 重算出来）；"补充材料 → 读者照着做" 这一段目前不能复现，一跑就崩，需要返工重打包。**

### 核验期间的并发改动（重要，影响结论时效）

核验窗口内投稿包被**其他写入者改过**，因此下表给出本报告结论对应的确切快照：

| 文件 | 大小 | 最后修改 | SHA-256（前 16 位） |
|---|---|---|---|
| `submission\final\main.tex` | 40 728 B | 21:37:16 | `16FABE334BA921FE` |
| `submission\main_v3.tex` | 40 728 B | 21:37:16 | `16FABE334BA921FE`（与上者**逐字节相同**） |
| `submission\final\main.pdf` | 328 503 B | 21:37:40 | 11 页 |
| `submission\final\supplementary.zip` | 182 084 B | 21:33:39 | 81 个文件条目 |
| `tools\verify_tex_v3.py` | 8 382 B | 21:38:54 | —（21:35 时是 8 262 B，只读 `submission\main_v3.tex`） |

我 21:35 拿到的 `final\main.tex` 是 40 638 B（SHA-256 `5895A3BD…`），21:37:16 被改成 40 728 B；同一分钟内 `main.pdf`、`main_v3.pdf` 被重编译。**本报告第 1、5、6 项的结论是在 21:43:42 的快照上复核过的**，第 4 项的"旧状态"证据（校验器只读 `main_v3.tex`）是 21:36 的实测。

---

## 1. 数字校验器

### 1.1 运行结果 —— PASS

```powershell
$py = "C:\Users\71736\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
cd D:\3dsg_1
& $py tools\verify_tex_v3.py
```

输出末三行（exit code = **0**）：

```
205 checks, 0 failures
ALL NUMBERS IN submission\final\main.tex MATCH THE STORED ARTIFACTS
```

- 断言条数 **205**，唯一期望串 **178**（同一条断言被重复检查 4 次的地方：`36/36` ×4、`-22.1` ×3、`-10.8` ×3 等）。
- 数据源：`results_v70/diag_*.json`、`results_v70/battery_*.json`、`results_v70/second_task.json`（+ 附录用的 `research/results_v22|v35|v52|v60`）。

### 1.2 投稿 tex 与源稿是否逐字节相同 —— PASS

```powershell
Get-FileHash D:\3dsg_1\submission\final\main.tex -Algorithm SHA256
Get-FileHash D:\3dsg_1\submission\main_v3.tex  -Algorithm SHA256
```

两者都是 `16FABE334BA921FEA03D1CE88989454C68EB550AB6E1C403061050CE02E19AFE`，**完全相同**；因此"校验 `main_v3.tex`"在当前内容上等价于"校验投稿 tex"。

### 1.3 校验器是否真的指向投稿文件 —— 先前 FAIL，现已修（但补充材料里的副本没修）

21:36 时的 `tools\verify_tex_v3.py` 第 17–18 行是硬编码：

```python
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "submission", "main_v3.tex")     # ← 唯一文本来源
```

我当时做了对照实验（在 `_repro_tmp\vt\` 里建等价目录树，用 junction 链接 `results_v70`、`research`）：

```powershell
# A：只把“投稿文件”改坏，保留 main_v3.tex 原样
#    把 final/main.tex 里 bicycle 的 -22.1 改成 -99.9
& $py tools\verify_tex_v3.py      # → 205 checks, 0 failures, exit 0   ← 完全没察觉
# B：只把 main_v3.tex 改坏
& $py tools\verify_tex_v3.py      # → 205 checks, 4 failures, exit 1
```

即：**当时校验器完全没有解析投稿用的那份 tex**，只因两份文件恰好同哈希才等价。21:38:54 之后工具被改成

```python
_final = os.path.join(ROOT, "submission", "final", "main.tex")
TEX = _final if os.path.isfile(_final) else os.path.join(ROOT, "submission", "main_v3.tex")
```

复核后 1.1 的输出已经变成 `submission\final\main.tex`，**该项现在成立**。
⚠️ 但 `supplementary.zip` 里的 `check/verify_tex_v3.py` 仍是 21:33 打包的旧副本（见 2.3），**包内那一份仍指向 `main_v3.tex`**。

**修法**：保持现在的 fallback 逻辑，并把"校验失败即 exit 1"写进 README；重打包 zip 时用 `tools\` 里的版本覆盖 `check\`（见第 7 节 A/B）。

---

## 2. 补充材料自洽性

解压：

```powershell
& $py -c "import zipfile;zipfile.ZipFile(r'D:\3dsg_1\submission\final\supplementary.zip').extractall(r'D:\3dsg_1\_repro_tmp\supp')"
```

zip 结构：**81 个条目、0 个目录条目、解压后 478 KiB**；顶层是 `calib/ check/ experiments/ figures/ results/ results_v70/ scripts/ tests/ README.txt`。

### 2.1 解压后能否"直接跑" `check/verify_tex_v3.py` —— FAIL（两处路径都断）

```powershell
cd D:\3dsg_1\_repro_tmp\supp
& $py check\verify_tex_v3.py
```

```
FileNotFoundError: 'D:\3dsg_1\_repro_tmp\supp\submission\main_v3.tex'      # ① zip 里根本没有 submission/
```

补上 tex 再跑（`copy final\main.tex supp\submission\main_v3.tex`）：

```
FileNotFoundError: 'D:\3dsg_1\_repro_tmp\supp\research/results_v60/vt_flowers.json'   # ② 目录名不对
```

原因：脚本读 `ROOT/research/results_vNN/…`，而 zip 把它打成了 `results/results_vNN/…`（少一层 `research\`）。README 里也完全没写这层约定。

**补齐这两处后**（复制 tex 到 `supp\submission\main_v3.tex`，把 `results\results_v*` 移到 `research\results_v*`）：

```
205 checks, 0 failures
ALL NUMBERS IN main_v3.tex MATCH THE STORED ARTIFACTS     # exit 0
```

→ **数据是完整的，坏的是目录布局**。这是本次最严重的"不改就复现不了"问题。

顺带：README 第 18 行教读者跑的是 `python check/verify_tex_v2.py`（旧稿校验器，152 断言），它读 `submission/main_v2.tex`，同样不存在：

```
FileNotFoundError: 'D:\3dsg_1\_repro_tmp\supp\submission\main_v2.tex'
```

`check/verify_tex_numbers.py`（52 KB 的老校验器）读 `submission/main.tex`，同样不存在。

### 2.2 `results_v70/` 是否随包、数据是否一致 —— PASS

- zip 根目录**有** `results_v70/`（9 个 JSON：4×`battery_*`、4×`diag_*`、`second_task.json`）。
- 与 `D:\3dsg_1\results_v70\` **逐个 SHA-256 相同**（9/9 IDENTICAL）。
- 路径全部是**相对路径**（`ROOT = check/ 的父目录`），没有写死盘符 —— 这点是对的。

### 2.3 zip 内 `check/` 脚本与仓库版本的关系 —— 内容旧/字节格式不同

| zip 内文件 | 大小 | 与 `tools\` 同名文件 |
|---|---|---|
| `check/verify_tex_v3.py` | 8 066 B | 与 21:35 版**行内容完全相同**（仅 LF vs CRLF 差 196 B）；**不含 21:38 的路径修正** |
| `check/make_fig3.py` | 2 812 B | SHA-256 与 `tools\make_fig3.py` **相同** |
| `check/make_figs_v2.py` | 6 664 B | SHA-256 与 `tools\make_figs_v2.py` **相同** |
| `check/make_tables_v70.py` | 2 918 B | 同 `tools\` 版本 |
| `check/verify_tex_numbers.py`、`verify_tex_v2.py` | — | 旧稿校验器，目标 tex 不在包内，**跑不了** |

### 2.4 `results/` 与 `results_v70/` 是否覆盖论文每个数字来源 —— 大部分覆盖，附录 D 漏

- 主表（表 1/2/4/5）、表 3 的口径对照、正文 Setup 数字：**全部**来自 `results_v70/`，已随包，205 条断言 0 失败 → 覆盖 ✓。
- 附录 C 五个 from-scratch 场景（"-0.8, +0.0, -0.2, +1.1, +3.2 点"、116k–241k primitives）：来自 `research/results_v35/*.json`，**随包** ✓。我独立重算核对：`bonsai -0.8 / counter 0.0 / garden -0.2 / kitchen 1.1 / room 3.2`，n = 116 674–241 376，与论文一致。
- **附录 D「两个方法论陷阱」三个区间未被任何校验器断言，且源文件不在包内**：

  | 论文写法（`main.tex:L635–639`） | 本机可查到的源 | 是否在 zip |
  |---|---|---|
  | over-covers `0.944–0.988` | `research\results_v17\cert_audit.json` clean 行 `cov_pix` = 0.949/0.988/0.944/0.965 → range **0.944–0.988**（完全对上） | ❌ 不在 |
  | interleaved 恢复到 `0.894–0.901` | `research\results_v52\many_splits.json` clean_mean（在包内），range 可重算 | ✓ 在 |
  | leakage 降到 `0.822–0.894` | `research\results_v24\cert_all.json` clean 行 `cov_pix` = **0.823**/0.828/0.894 → range **0.823–0.894**；`results_v28\cert_a0.2.json` 里有 `0.8224` | ❌ 不在 |

  → 除 2.1 的路径问题外，这里还有 **① 数字无断言（"每个数字"不成立）② 源 artifact 未发布（读者无法自查）③ `0.822` 与最可能的源 `0.823` 差 1e-3，需要作者确认是笔误还是另有所指**。

### 2.5 绝对路径 / 用户名 / 仓库名残留 —— PASS

```powershell
foreach ($p in @('D:\','C:\','Users','71736','3dsg','/home/','/root/','github','@gmail','@qq.com','.matpool','OneDrive')) {
  Select-String -Path (Get-ChildItem D:\3dsg_1\_repro_tmp\supp -Recurse -File -Include *.py,*.json,*.txt,*.md) -Pattern $p -SimpleMatch
}
```

**12 个模式全部 0 命中**（81 个文件全扫）。zip 内条目名也全是相对路径，无 `__pycache__`、`.git`、`Thumbs.db` 之类残留。PDF 侧同样干净：

```powershell
pdftotext -layout submission\final\main.pdf shipped.txt   # 3dsg/Users/71736/github/http/www./@/.com/.cn 全 0 命中
```

作者行是 `Anonymous authors` + `Paper under double-blind review` ✓。

### 2.6 README 与事实不符 —— FAIL（陈旧）

`README.txt` 至少 4 处过期：
1. 第 18 行复现命令写 `python check/verify_tex_v2.py`（152 断言）—— 现在的主力是 `verify_tex_v3.py`（205 断言）；
2. 第 13–14 行只说 `check/` 里有 `verify_tex_numbers.py` 和 `verify_tex_v2.py`，**没提 `verify_tex_v3.py` / `make_tables_v70.py` / `make_fig3.py`**；
3. 第 12 行 "`results/` … every number in the paper is derived from these" —— 主表数字实际来自 `results_v70/`；
4. 全文没有 mention `results_v70/`，也没写"脚本要在解压根目录跑"。

---

## 3. 图表可重建

环境：`python 3.12.14` / `numpy 2.3.5` / `matplotlib 3.11.2`，**不需要 torch**（两个脚本只读 JSON + 画图）。

### 3.1 `tools\make_fig_dose.py` → `fig_dose.pdf` —— 本地 PASS / **包内不可重建 FAIL**

```powershell
cd D:\3dsg_1\_repro_tmp\supp          # 解压后的材料目录（脚本用相对路径 results_v70）
& $py D:\3dsg_1\tools\make_fig_dose.py
```

```
wrote figures_v3/fig_dose.pdf
bicycle  [1.0, 4.9, 22.1, 60.0]  [4.0, 23.0, 105.0, 325.0]
flowers  [0.8, 3.6, 10.8, 40.8]  [4.0, 17.0, 53.0, 192.0]
stump    [1.5, 7.4, 27.7, 62.4]  [7.0, 32.0, 122.0, 303.0]
treehill [2.2, 6.1, 15.2, 44.9]  [19.0, 50.0, 108.0, 229.0]
```

exit 0，产出 `fig_dose.pdf` **19 347 B**，与投稿 `final\fig_dose.pdf` **字节长度完全相同**（哈希不同仅因 matplotlib 内嵌 `CreationDate`）。

**但：`supplementary.zip` 里既没有 `make_fig_dose.py`，`figures\` 里也没有 `fig_dose.pdf`**（只有 `fig_decouple.pdf`、`fig_repair.pdf`、`fig_three.pdf`）。我 grep 了包里全部 81 个文件，`fig_dose` 零命中 → **读者拿到补充材料无法重建论文的这张图**。

### 3.2 `tools\make_fig3.py` → `fig_three.pdf` —— PASS

```powershell
cd D:\3dsg_1\_repro_tmp\supp
& $py check\make_fig3.py          # 用 zip 自带的副本
```

exit 0，输出 `figures_v2/fig_three.pdf` **16 241 B**，与投稿 `final\fig_three.pdf` 字节长度相同；配对 bootstrap 结果 `bicycle prune30 -3.9 pp [-5.1,-2.7]`、`flowers prune30 -2.6 pp [-4.2,-1.1]`，与论文表 5 一致。

小瑕疵：`make_fig3.py` 把两条 coverage 值写成字面量

```python
cov = {'bicycle': {'30': -22.1, '10': -60.0}, 'flowers': {'30': -10.8, '10': -40.8}}
```

而不是从 `battery_*.json` 重算（我核对过，这四个值与 artifact 完全一致，所以**不是数值错误，是"图不是全量重算出来"的观感问题**）。

### 3.3 表格可重建（额外证据）—— PASS

```powershell
cd D:\3dsg_1\_repro_tmp\supp
& $py check\make_tables_v70.py
```

exit 0；吐出的 **12 行表格行中，每一行的每个十进制数字都能在 `final\main.tex` 里逐字找到（12/12）**。说明表 1/2/4 与任务扫描这两块是真正的"artifact → 表"。

---

## 4. 论文自述 vs 事实

`main.tex:L572–577` 原文：

> Every number that comes from our own runs is re-derived from stored artifacts by an automated check with one assertion per reported value, recording the source file and field; the check parses this LaTeX file rather than a separate draft. Two figures are quoted from the released archive itself (its own PSNR/SSIM summary) and are labelled as such in the text. The archive download, the rendering pass and the 400-split analysis are each a single command. Code, per-scene result files and the check suite are provided as anonymised supplementary material.

逐句核对：

| 子句 | 事实 | 判定 |
|---|---|---|
| "the check parses this LaTeX file rather than a separate draft" | `tools\verify_tex_v3.py` 21:38:54 之后确实优先读 `submission/final/main.tex` ✓；**但 21:33 打包的 `check/verify_tex_v3.py` 仍读 `main_v3.tex`，且它连 tex 都没随包** | **FAIL（包内）** |
| "one assertion per reported value" | 205 条断言 / 178 个唯一 token；`main.tex` 里有 **247 个不同的十进制字面量**，其中 **72 个从未出现在任何断言的期望串里**（例：附录 D 的 `0.944/0.988/0.894/0.901/0.822`、表 3 每场景的 `0.84×`/`0.85×`、`0.756` 等）。断言是"期望串是否是全文子串"，重复值会自动合并 | **FAIL** |
| "recording the source file and field" | `verify_tex_v3.py` 的 `check()` 只打印 name + 期望串，**不记录来源文件和字段**。真正记录 `src` 的是旧稿校验器 `verify_tex_numbers.py`（`rec(..., src="results_v17/cert_audit.json:cov_pix")`），而它读 `submission/main.tex`（不在包内，跑不了） | **FAIL** |
| 失败时是否非零退出 | 代码 `sys.exit(1)`；实测把 `-22.1` 改成 `-99.9` 后 `exit 1`、打印 `FAILURES: ['bicycle drop30', …]` | **PASS** |
| "Two figures are quoted from the released archive itself … labelled as such" | `L117–118`："the archive's own evaluation reports 25.2 dB and 0.756 SSIM for bicycle" —— 确实标注为 archive 自带评估，且不在 storage 里 | **PASS** |
| "The archive download … a single command" | 包里**没有任何下载脚本**，论文也没给出 archive 名称/来源（匿名取舍）。README 只写"archive 布局"，参数由人传 | **FAIL/未能验证** |
| "Code, per-scene result files and the check suite are provided" | 代码/结果在 ✓，check suite 在但按 2.1 跑不起来 | **部分 FAIL** |

结论：**这句话只有一半是真的**——"artifact → 数字"确实是自动的（205/0，可复现），但"逐值断言 + 记录来源 + 校验的就是这份 tex + 单命令下载"这四点，按投稿包现状都不成立。

---

## 5. PDF 与源是否一致

```powershell
$env:PATH = "D:\texlive\2026\bin\windows;" + $env:PATH
mkdir D:\3dsg_1\_repro_tmp\build
copy D:\3dsg_1\submission\final\* D:\3dsg_1\_repro_tmp\build\
cd D:\3dsg_1\_repro_tmp\build
pdflatex -interaction=nonstopmode -halt-on-error main.tex    # 第一遍
pdflatex -interaction=nonstopmode -halt-on-error main.tex    # 第二遍
```

| 检查 | 结果 |
|---|---|
| 编译是否成功 | PASS，两遍都 `exit 0` |
| 页数 | 重编译 **11 页**（328 503 B）；`final\main.pdf` **11 页**（328 503 B）；`main_v3.pdf` 也是 11 页 → **一致** |
| 未定义引用 | `undefined` 0 次、`LaTeX Warning` 0 条、`Overfull \hbox` 0 条、`Underfull` 2 条 → **干净** |
| 文本是否一致 | `pdftotext -layout` 双份各 631 行，`Compare-Object` **0 行差异** → 投稿 PDF 就是这份 tex 编出来的 |
| 依赖 | `final\` 自包含：`tmlr.sty`、`math_commands.tex`、`fig_dose.pdf`、`fig_three.pdf` 都在同目录；参考文献是 `thebibliography` 手写环境（`main.tex:L579–596`），**不需要 `refs.bib` / bibtex** |

`pdfinfo` 附注：`Page size: 612 x 792 pts (letter)`（TMLR 模板默认），`Producer: pdfTeX-1.40.29`。

---

## 6. 投稿清单 vs 磁盘事实

`SUBMISSION_CHECKLIST.md` 的每项声明：

| 清单声明 | 磁盘事实 | 判定 |
|---|---|---|
| `final\main.pdf` 11 页 | `pdfinfo` → 11 | **PASS** |
| "正文约 7 页 + 参考文献 1 页 + 附录 2 页" | 实际正文写到 **p9**（§5 Discussion + §6 Broader impact 在 p9），References 从 p9 末延续到 p10 上半，附录 A 起于 p10 末、D 止于 p11。且 7+1+2=**10 ≠ 11**，拆分本身自相矛盾 | **FAIL（轻）** |
| `main.pdf` 约 321 KB | 328 503 B = **320.8 KiB** | **PASS** |
| `supplementary.zip` **80 文件** | zip 条目 **81**，全是文件（0 目录条目）；解压 478 KiB | **FAIL（轻，差 1）** |
| zip 0.18 MB | 182 084 B = 174 KiB ≈ 0.18 MB | **PASS** |
| "205 条断言、0 失败" | 实测 205 / 0 | **PASS** |
| "`tools\verify_tex_v3.py` … 205 assertions against `submission/main_v3.tex`"（§五） | 21:38:54 起工具已改为优先 `submission/final/main.tex`，文档过期 | **FAIL（轻）** |
| "两张图都在同目录" | `final\fig_dose.pdf`、`final\fig_three.pdf` 都在 | **PASS** |
| "PDF 全文扫描无仓库名/用户名/URL" | pdftotext 扫描 11 个模式 0 命中 | **PASS** |
| "补充材料已去绝对路径" | 2.5 实测 0 命中 | **PASS** |
| 数据来源 "`research/results_v22|v35|v51|v52|v55|v58|v60`" | 校验器实际只用 **v22 / v35 / v52 / v60**；v51/v55/v58 是旧校验器用的 | **轻微不准** |

---

## 7. 需要修的具体动作

### A. 不改就无法复现（必须返工重打包）

1. **修 `supplementary.zip` 的目录布局，让 `check/verify_tex_v3.py` 一跑就过**（最严重）
   - 二选一：
     - (a) 打包时把 tex 放进 zip：`submission/main_v3.tex`（内容 = `final/main.tex`）；
     - (b) 改校验器为"接受 `--tex` 参数，默认依次找 `../final/main.tex`、`./main.tex`、`submission/main_v3.tex`"，找不到就 `exit 2` 并打印期望路径。
   - 同时把 `results/results_vNN/` 改成 `research/results_vNN/`（或把校验器里的前缀改成 `results/`）—— 二选一必须与 README 写法一致。
   - 验收命令：`cd <解压根>; python check/verify_tex_v3.py` → **205 checks, 0 failures, exit 0**。
2. **用 `tools\` 里的最新版本重打 `check/`**：现包内 `check/verify_tex_v3.py` 是 21:33 的旧副本（仍指 `main_v3.tex`），与论文第 4 节那句自述直接冲突。
3. **附录 D 三个区间**（`main.tex:L635–639`）
   - 补断言进 `verify_tex_v3.py`（源：`research/results_v17/cert_audit.json:cov_pix(clean)`、`research/results_v24/cert_all.json:cov_pix(clean)`、`research/results_v52/many_splits.json:clean_mean`）；
   - 并把这两个 JSON 加进 zip；
   - 或者删掉这三个区间（它们本来就是"附录补充证据"，删了不影响主结论）。
4. **确认 `0.822` 到底是 0.822 还是 0.823**：`results_v24/cert_all.json` clean 行是 `0.823/0.828/0.894`；`results_v28/cert_a0.2.json` 里有 `0.8224`。若取后者，论文该写 `0.822`；若取前者，应改 `0.823`。这条必须作者拍板，我不能替你改。
5. **`fig_dose` 的可重建性**：把 `tools\make_fig_dose.py` 放进 `check/`，把 `fig_dose.pdf` 放进 `figures/`（现在 `figures/` 只有 3 个 PDF，缺 `fig_dose`）。
6. **`README.txt` 重写**：复现命令改 `python check/verify_tex_v3.py`（205 断言）；明确"脚本在解压根目录下运行"、"主表数字来自 `results_v70/`、附录数字来自 `research/results_vNN/`"；删掉 `verify_tex_v2.py`（152 断言）这条误导。
7. **第 4 节那句自述要么改代码、要么改措辞**：建议保留"check parses this LaTeX file"（已成立），把 "with one assertion per reported value, recording the source file and field" 改成"with 205 assertions against the stored per-scene artifacts"，或真给 `check()` 加 `src=` 字段并打印。同时把 "The archive download … a single command" 改成与实际一致的说法（补充材料里没有下载脚本）。

### B. 影响观感（不改也能复现，但会被审稿人挑）

8. `SUBMISSION_CHECKLIST.md`：`80 文件` → **81**；页数构成 `正文约 7 页 + 参考 1 + 附录 2` → 与实际 11 页不符（建议改成"正文 9 页（含 discussion/broader impact），参考文献 1 页，附录 1–2 页，共 11 页"）；§五那句 `against submission/main_v3.tex` → `against submission/final/main.tex`。
9. `make_fig3.py` 里 4 个硬编码 coverage 值改成从 `results_v70/battery_*.json` 读，避免"图画出来和数字无关"的观感。
10. 校验器断言用"子串存在"判定，弱断言要收紧：`check("pixels per split", "2.6")` 只要全文任意位置出现 `2.6` 就通过（`2.65` 也会中）；`f"${h}/{n}$"`（`36/36`）四个场景共用同一个串，无法区分是哪个场景。建议改成"在指定 table 环境内匹配"或"带场景前缀的唯一串"。
11. 清单里"数据来源 v51|v55|v58"与实际断言来源（v22/v35/v52/v60）对齐。

---

## 8. 未能运行 / 局限（如实记录）

1. **没有重跑实验本体**：本机 Python 无 torch、无 gsplat、无原始 archive（`<archive>/output/<scene>/…`）。因此"archive → artifact"这一段（README 的 `scripts/many_splits.py --archive …` 400 划分）**未能运行**，只核了"artifact → 论文数字"。这条链路的可复现性仍是未知数，需要 GPU 节点才能验。
2. **`check/verify_tex_numbers.py`（52 KB 老校验器）未能运行**：它读 `submission/main.tex`，zip 里没有这个文件（仓库里有，是 28 KB 的 v1 旧稿）。
3. **附录 D 的 `0.822–0.894` 来源未 100% 锁定**：我按数值反查，最匹配的是 `research/results_v24/cert_all.json`（0.823/0.828/0.894），但 `results_v28/cert_a0.2.json` 里也存在 `0.8224`。老校验器的注释写"the first printed value 0.822 is a transposition of 0.828"，暗示这是笔误；但那是针对旧稿三值写法的注释，不能直接套到现在的区间写法。**结论：需要作者确认，我不做定论。**
4. **`research/results_v55/widths.json` 与本地同名文件逐字节不同**（内容键值与首条记录完全一致，仅序列化格式差异），未进一步追查；该校验器不用这个文件。
5. **核验期间投稿包被并发修改**（见第 0 节表），若之后 `final\main.tex` / `supplementary.zip` 再次变化，第 1、5、6 项的实测结论需按新哈希重跑。

---

## 附：可复现这套核验的命令清单

```powershell
$py = "C:\Users\71736\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"

# 1) 数字校验 + 是否逐字节同一份
cd D:\3dsg_1; & $py tools\verify_tex_v3.py                       # 205 checks, 0 failures, exit 0
Get-FileHash submission\final\main.tex, submission\main_v3.tex    # 两哈希相同

# 2) 补充材料
New-Item -ItemType Directory -Force D:\3dsg_1\_repro_tmp\supp
& $py -c "import zipfile;zipfile.ZipFile(r'D:\3dsg_1\submission\final\supplementary.zip').extractall(r'D:\3dsg_1\_repro_tmp\supp')"
cd D:\3dsg_1\_repro_tmp\supp; & $py check\verify_tex_v3.py        # 原样：FileNotFoundError（见 2.1）

# 3) 图表
cd D:\3dsg_1\_repro_tmp\supp
& $py check\make_fig3.py            # figures_v2/fig_three.pdf  16 241 B
& $py D:\3dsg_1\tools\make_fig_dose.py   # figures_v3/fig_dose.pdf  19 347 B（包内无此脚本）
& $py check\make_tables_v70.py      # 12 行表格行，数字全部能在 main.tex 里找到

# 4) 重编译
$env:PATH = "D:\texlive\2026\bin\windows;" + $env:PATH
New-Item -ItemType Directory -Force D:\3dsg_1\_repro_tmp\build
Copy-Item D:\3dsg_1\submission\final\* D:\3dsg_1\_repro_tmp\build\
cd D:\3dsg_1\_repro_tmp\build
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex   # 11 pages, 0 undefined
pdfinfo main.pdf | Select-String '^Pages'
pdftotext -layout main.pdf reb.txt
pdftotext -layout D:\3dsg_1\submission\final\main.pdf ship.txt
Compare-Object (Get-Content reb.txt) (Get-Content ship.txt)   # 0 差异
```
