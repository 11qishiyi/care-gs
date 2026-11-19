# TMLR 投稿包复现性核验（第二轮复查）REPRO_CHECK_v2

- 核验人：teammate `repro-final`
- 核验时间：2026-11-10 21:58–22:10（Asia/Shanghai）
- 对象：返工后的 `submission\final\`（`main.pdf` / `main.tex` / `supplementary.zip`）
- 只读核验；解压/编译都在 `_repro_tmp\supp2`、`_repro_tmp\build2`、`_repro_tmp\paperbuild` 里做；原文件未动
- 上一轮报告：`review\REPRO_CHECK.md`（本报告只列变化后的结论，旧问题仍存在处会标明"仍未修"）

## 0. 快照（本报告结论对应的确切状态，2026-11-10 21:59–22:10）

| 文件 | 大小 | 修改时间 | SHA-256（前 16） |
|---|---|---|---|
| `submission\final\main.tex` | 42 723 B | 21:56:00 | `1AC06BEF60306C53` |
| `submission\main_v3.tex` | 42 723 B | 21:56:00 | `1AC06BEF60306C53`（与上者逐字节相同 ✓） |
| `submission\final\main.pdf` | 352 052 B | 21:58:28 | 11 页，`pdfTeX-1.40.29` |
| `submission\final\supplementary.zip` | 194 866 B | 21:57:40 | 88 个条目 / 88 个文件 / 0 个目录条目；解压 524.7 KiB |
| `submission\supplement.zip` | 194 866 B | 21:57:40 | 与 `final\supplementary.zip` **同哈希**（打包脚本输出到前者，后者是拷贝） |

## 1. 结论速览

**33 个细分检查 → 21 PASS / 9 FAIL / 3 部分通过。**

| 项 | 内容 | 上一轮 | 本轮 |
|---|---|---|---|
| 1 | 数字校验器（含零配置可跑性） | 条件 PASS | **PASS（但零配置仍失败，需带两个参数）** |
| 2 | 补充材料自洽性 | FAIL | **大幅改善，仍 3 处断链** |
| 3 | 图表可重建 | 部分 FAIL | **PASS（两张图都能从解压材料重建）** |
| 4 | 论文 Reproducibility 段 vs 事实 | FAIL | **仍未修（该段文字一字未改）** |
| 5 | PDF 与源一致 | PASS | **提交包内 PASS；补充材料里的 tex 落后一版（新问题）** |
| 6 | checklist vs 磁盘 | 基本 PASS | **基本 PASS（页数构成、断言措辞 2 处需改）** |

一句话：**补充材料这次真的能跑起来了**（243 断言 0 失败，两张图可重建，匿名扫描干净），**剩下的问题集中在 3 个断链 + 论文那句话没改 + zip 里的 tex 落后投稿版一个词**。不需要整体返工，只需重打一次 zip + 改两句论文/清单文字。

---

## 2. (a) 解压后 reader 能否零配置跑通

### 2.1 校验器 —— 带参数 PASS，**零配置 FAIL**

```powershell
$py = "C:\Users\71736\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
& $py -c "import zipfile;zipfile.ZipFile(r'D:\3dsg_1\submission\final\supplementary.zip').extractall(r'D:\3dsg_1\_repro_tmp\supp2')"
cd D:\3dsg_1\_repro_tmp\supp2
```

| 调用方式 | 结果 |
|---|---|
| `python check/verify_tex_v3.py --root . --tex paper/main.tex`（README 教的方式） | **exit 0，`243 checks, 0 failures`**，末行 `ALL NUMBERS IN paper\main.tex MATCH THE STORED ARTIFACTS` ✓ |
| `python check/verify_tex_v3.py`（README **没写**、但"零配置"会这么跑） | **exit 1**，`FileNotFoundError: 'D:\...\supp2\submission\main_v3.tex'` |

原因：`check/verify_tex_v3.py` 无参时的默认 TEX 仍是 `ROOT/submission/final/main.tex` → `ROOT/submission/main_v3.tex`，zip 里没有 `submission/`。
→ **答：不是零配置；但 README 已明确写出带参命令，照 README 做可以跑通。**
**建议**（一行改动）：在 `if _args.tex:` 缺省分支里加 `paper/main.tex` 候选：

```python
_cands = [os.path.join(ROOT, "paper", "main.tex"),
          os.path.join(ROOT, "submission", "final", "main.tex"),
          os.path.join(ROOT, "submission", "main_v3.tex")]
TEX = next(p for p in _cands if os.path.isfile(p))
```
这样 `python check/verify_tex_v3.py` 在解压根目录也能直接跑，README 那句"默认行为不变"也才真正不误导。

### 2.2 两张图 —— PASS（上一次的 fig_dose 缺口已补上）

```powershell
cd D:\3dsg_1\_repro_tmp\supp2
& $py tools\make_fig3.py          # exit 0
& $py tools\make_fig_dose.py      # exit 0
& $py tools\make_tables_v70.py    # exit 0
```

| 脚本 | 输出 | 与包内 `paper/` 对比 |
|---|---|---|
| `tools/make_fig3.py` | `figures_v2/fig_three.pdf` **16 241 B** | `paper/fig_three.pdf` 16 241 B —— 字节长度相同 ✓ |
| `tools/make_fig_dose.py` | `figures_v3/fig_dose.pdf` **19 109 B** | `paper/fig_dose.pdf` 19 109 B —— 字节长度相同 ✓ |
| `tools/make_tables_v70.py` | 12 行表格行，数字全部能在 `main.tex` 找到（12/12） | ✓ |

依赖只需 `numpy 2.3.5` + `matplotlib 3.11.2`，**不需要 torch**。上一轮"`fig_dose` 无脚本、无 PDF"的问题已修好。
包内 `tools/make_fig3.py`、`tools/make_fig_dose.py`、`check/verify_tex_v3.py` 与仓库 `tools\` 版本**内容 diff = 0**（仅换行符差异），不存在"包里是旧脚本"的问题。

### 2.3 其他可跑性

| 项目 | 结果 |
|---|---|
| `pytest tests` | **8 passed / 2 failed**：`test_voxel_cert.py`、`test_advise.py` 因 `ModuleNotFoundError: No module named 'torch'` 收集失败；`test_operators.py` 里 2 个 SH 用例也需要 torch |
| 说明 | README 写 "tests/ unit tests for the operators and the decision modules"，**没写需要 torch/gsplat**。建议加一句 "two modules need torch + gsplat (GPU node)"，或把它们移进 `tests/gpu/` |

→ **部分通过**：CPU-only 读者能跑 8 个用例，2 个模块必然红。

---

## 3. (b) Reproducibility 段 vs 事实

论文里这一段（`main.tex:L594–601`）与上一轮**逐字相同，没有改**：

> Every number that comes from our own runs is re-derived from stored artifacts by an automated check with one assertion per reported value, recording the source file and field; the check parses this LaTeX file rather than a separate draft. Two figures are quoted from the released archive itself (its own PSNR/SSIM summary) and are labelled as such in the text. The archive download, the rendering pass and the 400-split analysis are each a single command. Code, per-scene result files and the check suite are provided as anonymised supplementary material.

逐句核对：

| 子句 | 事实 | 判定 |
|---|---|---|
| "the check parses this LaTeX file rather than a separate draft" | 仓库侧 `tools/verify_tex_v3.py` 优先读 `submission/final/main.tex` ✓；但**包里那份解析的是 `paper/main.tex`，而它落后投稿版一个词**（见 5.2） | **部分 PASS** |
| "one assertion per reported value" | 243 条断言 / 212 个唯一 token；投稿 tex 有 **263 个不同十进制字面量，62 个从未出现在任何断言里**。典型漏网：表 2 pixel 列的置信区间上下界（`-62.1/-58.0`、`-68.3/-57.3`、`-48.7/-36.4`）、附录 B 的全集上界 `0.927`、附录 B 的 `n≥4` 阈值、§4 的 "two calibration views" | **FAIL** |
| "recording the source file and field" | 仍在 `check()` 里**没有实现**：函数签名是 `check(name, token)`，只打印 name+期望串，不记录来源文件/字段 | **FAIL（未修）** |
| 失败时非零退出 | `sys.exit(1)`；实测改坏一个数 → exit 1 + `FAILURES: [...]` | **PASS** |
| "Two figures … quoted from the archive … labelled as such" | `L119–120`："the archive's own evaluation reports 25.2 dB and 0.756 SSIM for bicycle" —— 确实标注 ✓ | **PASS** |
| "archive download / rendering / 400-split are each a single command" | download ✓ `experiments/fetch_hf_data.py`；400-split ✓ `scripts/many_splits.py`；**rendering ✗ README 教的 `experiments/node_run.py` 根本没打进 zip**（见 4.2） | **部分 FAIL** |

**建议改法（二选一，成本最低）**：
- 代码侧：给 `check()` 加 `src=` 参数并在输出里打印 `[results_v70/diag_bicycle.json:protocols.raw.drop_mean]`，补上表 2 CI 界与 `0.927` 的断言；
- 或文字侧：把 "with one assertion per reported value, recording the source file and field" 改成 "with 243 assertions against the stored per-scene artifacts（`check/verify_tex_v3.py`）；headline values in Tables 1–5 and §3.7 are pinned one-by-one, interval bounds are recomputed from the same files"。目前这句话是**唯一一处仍然与事实不符的 self-claim**。

---

## 4. (d) 仍然存在的断链（逐条，按严重性）

### 4.1 zip 里的 `paper/main.tex` 落后投稿版一个词 —— FAIL（必须重打包）

```powershell
Select-String -Path D:\3dsg_1\submission\final\main.tex        -Pattern 'level two|level three'   # → "a level two"
Select-String -Path D:\3dsg_1\_repro_tmp\supp2\paper\main.tex   -Pattern 'level two|level three'   # → "a level three"
```

- 投稿 tex / 投稿 PDF：`…at a level **two** orders of magnitude below the residual…`
- 补充材料 tex：`…at a level **three** orders…`
- 数据佐证：SH 量化扰动 3.4e-4 vs 残差 2.6e-2 ≈ 76× ≈ 1.9 个数量级 → **"two" 才对**，包里那份是改前的旧稿。
- 影响：读者用补充材料里的 `paper/main.tex` 重编译，**得不到投稿的 main.pdf**（`pdftotext` 逐行对比：10 行文本不同，全部集中在这一句）。数字不受影响（243 断言仍然通过），但"paper/main.tex = 投稿 LaTeX"这个承诺不成立。
- 根因：打包脚本 `tools/make_supplement.py` 的 `OUTZIP` 指向 `submission/supplement.zip`，`final/supplementary.zip` 是**手工拷贝**；本次拷贝发生在 tex 最后一次修改之前。
- **修法**：重跑 `python tools\make_supplement.py`，再把 `submission\supplement.zip` 覆盖到 `submission\final\supplementary.zip`；或者直接改 `OUTZIP = os.path.join(ROOT, "submission", "final", "supplementary.zip")` 消除这层手工拷贝。

### 4.2 README 指的 `experiments/node_run.py` 没打进 zip —— FAIL

```powershell
Test-Path D:\3dsg_1\_repro_tmp\supp2\experiments\node_run.py     # False
Get-ChildItem D:\3dsg_1\_repro_tmp\supp2\experiments             # 7 个文件，无 node_run.py
Get-ChildItem D:\3dsg_1\_push\3dsg\experiments\node_run.py        # 存在（staging 副本）
```

- README 第 41–44 行教读者跑 `python experiments/node_run.py diag/battery …`，→ `No such file or directory`。
- 根因：`tools/make_supplement.py:36` 的 `EXPERIMENTS` 列表**包含** `node_run.py`，但 `D:\3dsg_1\experiments\node_run.py` 不存在（只在 `_push\3dsg\experiments\` 里），打包循环 `if os.path.isfile(p)` **静默跳过**，于是 zip 里少了它、README 却照旧写着。
- **修法**：`copy D:\3dsg_1\_push\3dsg\experiments\node_run.py D:\3dsg_1\experiments\` 后重打包；同时把打包脚本的静默跳过改成 `print("MISSING", p)`，避免下次再漏。

### 4.3 README 的 "Absolute paths have been stripped from every file" 不成立 —— FAIL（轻）

```powershell
Select-String -Path (Get-ChildItem D:\3dsg_1\_repro_tmp\supp2 -Recurse -File -Include *.py) -Pattern '/data/' -SimpleMatch
```

- 命中 **24 处**，集中在 `experiments/build_archive.py`（`--models /workspace/data/models`、`--images /workspace/data/mip360`、`--archive /workspace/data/official`）与 `fetch_hf_data.py`。
- 这些是 Linux 容器内的绝对路径（不是作者机器路径），匿名性没问题，但与 README 那句绝对化承诺矛盾。
- 另注：`experiments/fetch_hf_data.py:20–21` 硬编码 `https://hf-mirror.com/...`（HF 中国镜像）指向公开数据集 `dylanebert/3dgs`、`nvs-bench/mipnerf360` —— 这是**有用**的信息（读者终于知道 archive 是哪来的），但镜像域名会暴露"作者在中国大陆"这类弱信号；如要彻底匿名，建议换成 `huggingface.co` 官方域名（两条 URL 的 dataset 路径相同）。
- **修法**：README 改成 "No author-machine paths remain; container paths (`/workspace/...`) are defaults you can override."

### 4.4 匿名/路径扫描：包本身就是干净的 —— PASS

对 85 个包内源文件（排除我自己产生的日志）扫 15 个模式：`71736`、`3dsg`、`Users`、`D:\`、`C:\`、`github`、`@gmail`、`@qq.com`、`OneDrive`、`matpool`、`_token`、`getenv` 等 **全部 0 命中**；只有 `/data/`（见 4.3）。zip 条目名全为相对路径，无 `__pycache__`/`.git` 残留。PDF 侧 0 命中。✓

### 4.5 附录 B 的 `n≥4` 与 §4 的 "two calibration views" 与 artifact 不符 —— FAIL（新发现，数字问题）

artifact（包内 `research/results_v22/cert_v3.json`，`edit=prune30`，`repair_curve[].n_cal`）：

| n_cal | bicycle | flowers | stump | treehill |
|---|---|---|---|---|
| 2 | 0.882 (−1.8) | 0.917 (+1.7) | 0.882 (−1.8) | **0.971 (+7.1)** |
| 4 | 0.901 | 0.917 (+1.7) | 0.930 (+3.0) | **0.969 (+6.9)** |
| 6 | 0.907 | 0.907 | 0.919 (+1.9) | **0.954 (+5.4)** |
| 8 | 0.901 | 0.898 | 0.902 | **0.936 (+3.6)** |
| 9（全集） | 0.876 (−2.4) | 0.892 (−0.8) | 0.902 | 0.927 (+2.7) |

（括号内为相对 nominal 0.90 的偏差，单位 points）

- 附录 B 现在写 "restores coverage to within three points of nominal **for n≥4** on all four scenes" → **不成立**：treehill 在 n=4/6/8 分别是 +6.9/+5.4/+3.6，**只有全集 n=9 才落到 +2.7**。
- §4（`L481`）仍写 "coverage returns to within three points of nominal **with two calibration views**" → 同样不成立（treehill n=2 是 +7.1），而且与附录 B 自己的 n≥4 口径互相矛盾。
- 上一轮我指出"7+1+2 那类口径问题"后，`n≥4` 是新加的限定，但**限定值本身没对着数据取**。
- 校验器只断言 `repair low/high = 0.876/0.971`，这两个阈值说法没有任何断言覆盖。
- **建议改法**：附录 B 改成 "three of the four scenes are within three points of nominal from n=2; treehill needs the full calibration set (nine views) to come within three points (0.927 at n=9, +6.9 at n=4)";§4 那句改成 "用两三个标定视角即可回到 nominal 附近（treehill 除外）"，或直接引 `results_v22` 的逐 `n_cal` 数值。

### 4.6 表 2 的置信区间上下界没有断言 —— FAIL（轻，属于 3.2 的一部分）

表 2 pixel 列写的是 `$-60.0\,[-62.1,-58.0]$` 形式，校验器只断言均值（`-60.0`）与 block 列的均值，**区间上下界（-62.1/-58.0、-68.3/-57.3、-48.7/-36.4 …）全都没断言**（全包 62 个未覆盖十进制里的大头）。表 1 的区间是有断言的（`drop30 lo/hi`），两处不一致。

---

## 5. (c) checklist vs 磁盘

`SUBMISSION_CHECKLIST.md`（21:33:17，我核验后未再改动）：

| 清单声明 | 磁盘事实 | 判定 |
|---|---|---|
| `main.pdf` 11 页 | `pdfinfo` → 11 ✓ | **PASS** |
| "正文 ~7 页 + 参考文献 1 页 + 附录 3 页" | 和 = 11 但拆分不对：正文实际写到 **p10 顶部**（§7 结束 + Repro 段在 p10），参考文献在 p10 中部（16 条），附录 A–D 从 p10 底部到 p11（≈1.3 页）。实际 ≈ 正文 9.5 / 参考 0.5 / 附录 1.3 | **FAIL（轻）** |
| "88 个目录项" | zip 88 个条目、88 个文件、**0 个目录条目**（用"目录项"计数没问题，但严格说没有目录条目） | **PASS（措辞可改"88 个文件"）** |
| "0.19 MB" | 194 866 B = 0.186 MiB ✓ | **PASS** |
| "243 条断言、0 失败" | 实测 243 / 0，exit 0 ✓ | **PASS** |
| "直接解析 `final/main.tex`" | 仓库侧 `tools/verify_tex_v3.py` 是 ✓（补材里那份解析 `paper/main.tex`，见 4.1） | **PASS** |
| 补充材料自测命令 `--root . --tex paper/main.tex` → 243/0 | 我原样复现 ✓ | **PASS** |
| "243 条断言把每个来自我们实验的数字钉到 artifact 的某个字段"（L15） | 62/263 未覆盖（见 3.2/4.6），"每个"过头 | **FAIL（轻）** |
| 补充材料 ≤100 MB、匿名 | ✓（见 4.4） | **PASS** |
| 主文件大小 | 清单里没再写 main.pdf 尺寸；实际 352 052 B（343.8 KiB，与 lead 说的 344 KB 一致） | 建议补回 "≈344 KB" |

---

## 6. (5) PDF 与源一致（复查结论）

```powershell
$env:PATH = "D:\texlive\2026\bin\windows;" + $env:PATH
# 用投稿 tex 重编（build2）
cd D:\3dsg_1\_repro_tmp\build2; pdflatex -interaction=nonstopmode -halt-on-error main.tex   # ×2
# 用补充材料里的 tex 重编（paperbuild）
cd D:\3dsg_1\_repro_tmp\paperbuild; pdflatex -interaction=nonstopmode -halt-on-error main.tex # ×2
```

| 检查 | 结果 |
|---|---|
| 投稿 tex 重编译 | exit 0，**11 页、352 052 B**（与投稿 `main.pdf` 同尺寸） |
| 未定义引用 / 警告 | `undefined` 0、`LaTeX Warning` 0、`Underfull` 2 |
| 文本一致性（投稿 tex ↔ 投稿 PDF） | `pdftotext -layout` 各 654 行，**0 行差异** ✓ |
| 包内 `paper/main.tex` 重编译 | 11 页 / 352 047 B，但与投稿 PDF **10 行文本不同**（"two/three orders"）→ 4.1 |
| 自包含性 | `final\` 内 `tmlr.sty`、`math_commands.tex`、两张图齐全；参考文献是手写 `thebibliography`，**不需要 `refs.bib`/bibtex** ✓ |

**结论**：提交包自身完全自洽（tex ↔ PDF 零差异）；不一致只发生在"补充材料里的那份 tex 副本"上。

---

## 7. 修复清单（按"不改就无法复现" / "影响观感"排序）

### A. 必须修（1 次重打包 + 2 处文字，就能全部清零）

1. **重打 zip 并从投稿 tex 打包**（修 4.1）：`python tools\make_supplement.py` 后覆盖 `submission\final\supplementary.zip`；顺手把 `OUTZIP` 直接指向 `final\supplementary.zip`。验收：解压后 `paper/main.tex` 与 `submission\final\main.tex` 内容一致（除换行符）。
2. **补 `experiments/node_run.py`**（修 4.2）：从 `_push\3dsg\experiments\` 拷到 `experiments\`，重打包；把打包脚本的静默 `isfile` 跳过改成打印 `MISSING`。
3. **附录 B 的 `n≥4` 与 §4 的 "two calibration views" 按 4.5 的实测表改写**（这是唯一还没被审稿人抓到、但一查就穿帮的数字问题）。
4. **Reproducibility 段**（修 3.2/3.3）：要么给 `check()` 加 `src=` 并补表 2 区间 + `0.927` 的断言；要么把 "one assertion per reported value, recording the source file and field" 降级为实际做到的表述。目前 62/263 未覆盖。

### B. 影响观感（可选，几分钟）

5. 校验器加 `paper/main.tex` 缺省候选，让"零配置"也能跑（2.1 的一行改法）。
6. README：补 "two test modules need torch/gsplat"；把 "Absolute paths have been stripped from every file" 改成不绝对的说法（4.3）；`fetch_hf_data.py` 的 `hf-mirror.com` 视匿名策略换回 `huggingface.co`。
7. `SUBMISSION_CHECKLIST.md`：页数构成改成 "11 页（正文 ≈9.5 页 + 参考文献 + 附录 A–D）"；L15 的"每个数字"改成"每个 headline 数字"；补 main.pdf 尺寸 ≈344 KB。

---

## 附：本轮实测命令清单

```powershell
$py = "C:\Users\71736\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"

# 解压
& $py -c "import zipfile;zipfile.ZipFile(r'D:\3dsg_1\submission\final\supplementary.zip').extractall(r'D:\3dsg_1\_repro_tmp\supp2')"
cd D:\3dsg_1\_repro_tmp\supp2

# (a) 校验器 + 两张图 + 表格
& $py check\verify_tex_v3.py --root . --tex paper/main.tex    # 243/0, exit 0
& $py check\verify_tex_v3.py                                   # exit 1（无 submission/，零配置失败）
& $py tools\make_fig3.py                                       # figures_v2/fig_three.pdf 16241 B
& $py tools\make_fig_dose.py                                   # figures_v3/fig_dose.pdf 19109 B
& $py tools\make_tables_v70.py                                 # 12 行，数字 12/12 命中 tex
& $py -m pytest tests -q                                       # 8 passed, 2 failed (no torch)

# (b) 投稿 tex 与包内 tex
Compare-Object (Get-Content D:\3dsg_1\submission\final\main.tex) (Get-Content .\paper\main.tex)   # 1 行不同：two / three

# (5) 重编译 + 文本比对
$env:PATH = "D:\texlive\2026\bin\windows;" + $env:PATH
cd D:\3dsg_1\_repro_tmp\build2; pdflatex -interaction=nonstopmode -halt-on-error main.tex   # ×2 → 11 pages
pdftotext -layout main.pdf ..\reb2.txt
pdftotext -layout D:\3dsg_1\submission\final\main.pdf ..\ship2.txt
Compare-Object (Get-Content ..\reb2.txt) (Get-Content ..\ship2.txt)                        # 0 差异
```
