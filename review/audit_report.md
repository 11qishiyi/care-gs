# 证据准确性审计报告 — `submission/main.tex`

审计员：auditor ｜ 日期：2026-11-09 ｜ 工具：`tools/verify_tex_numbers.py`
对象：`submission/main.tex`（476 行，8 页，`main.pdf` 已编译）
纪律：本审计**只报告**。未修改论文、未修改 `research/code/`、未改动任何结果 JSON。

---

## 0. 结论摘要

**229 条断言，188 MATCH（82.1%），19 MISMATCH，22 NO_SOURCE。** 主表（Table 2）与摘要里的绝大多数区间
是干净的：400 划分主表的 9 个场景 × 覆盖/降幅/CI、Table 5(a) 修复曲线、Table 4 的任务命中率、
Table 5(b) 三个场景的准则对比、§3.5 自检数字、附录 A 的 10.3–12.9 与 5.5–15.4，全部能逐位复现。

真正会伤到论文的是 **3 个结构性问题**，而不是零散笔误：

1. **Table 4 的 "Certificate drop" 与 Table 2 的同一量差了 1.9–4.9 倍，而表里没说明**。
   Table 4 用的是 0.25-unit voxel 区域（`vt_*.json:voxel_prune30_drop_mean`），Table 2 用 64×64 图像块
   （`many_splits.json:drop_mean`）。用 Table 2 自己的数字算"下游降幅 / 证书降幅"，得到 **1.0–2.5×**，
   不是摘要与贡献里写的 **1.9–12.1×**。论文的第二号贡献（"证书指标低估下游损失 2–12 倍"）只在
   混用两套区域定义时成立。
2. **Table 3 的 SH 行把 3 个"覆盖率上升"写成了"下降"**。`results_v53/ef_*.json` 里 SH 3→1 的
   覆盖率变化是 **+1.02 / +0.20 / +1.00 pp**（bicycle / treehill / stump，CI 全部不含 0），
   Table 3 印的是 **−1.0 / −0.2 / −1.0**。只有 flowers 是真的下降（−1.99，单划分 `cert_v3.json`）。
3. **附录 C 的稳健性段落与磁盘上的工件大面积脱节**：α=0.10 的 −14.1 与数据的 −13.50 不符；
   "voxel 把幅度缩小 3–4×" 逐场景是 1.9–4.9×；半分辨率四个数与 "within 1.4 points" 在磁盘上
   **没有任何工件**，且用它自己印出的数字与主表配对，偏差是 7.5 个点。

另有 22 个数字**在磁盘上根本找不到支撑**（最集中的是 Table 5(b) 的 flowers 整行 7 个数、
SH 扰动幅度 3.4–4.1×10⁻⁴、"4000 steps / 6000 steps"、自训场景 PSNR 11–16 dB、半分辨率 4 个数）。
其中 5 个是 AURA 的外部引用数字（合理的外部依赖，但无法在盘上追溯）。

---

## 1. 汇总

| 项目 | 数量 |
|---|---|
| 断言总数 | **229** |
| MATCH | **188** |
| MISMATCH | **19**（归并为 **14 个独立问题**） |
| NO_SOURCE | **22**（归并为 **9 组**） |
| 覆盖的 tex 行 | 27–473（摘要、Table 1–5、§2/§3.1–3.5/§5/§6/§7、附录 A/B/C） |

复现：

```powershell
$py = "C:\Users\71736\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
& $py D:\3dsg_1\tools\verify_tex_numbers.py --show-sources --json-out D:\3dsg_1\tools\_audit_rows.json
# -> "229 checks, 41 failures (188 MATCH, 19 MISMATCH, 22 NO_SOURCE)"，exit 1
```

脚本设计：表格行按"去 LaTeX → 位置取数"解析，正文按短语正则定位，**每个数值都带 tex 行号 +
`文件:字段` 出处 + 容差**；容差 = 印出精度的半个末位（1 位小数 → 0.06，3 位覆盖率 → 0.0006，
整数百分比 → 0.55）。脚本对每个 NO_SOURCE 都在注释里写明"找过哪里"。

---

## 2. MISMATCH 表

严重度：**H** = 会改变论文结论/被审稿人当作造假线索；**M** = 会被要求更正；**L** = 笔误级。

| # | tex 行 | 论文写的 | 数据算的（出处） | 差异 | 严重度 |
|---|---|---|---|---|---|
| M1 | 238–241 (Table 4) | 证书降幅 −4.6 / −6.1 / −2.6 / −6.1 | −10.9 / −18.6 / −12.8 / −11.7（`many_splits.json:drop_mean`，与 Table 2 同一量） | 1.9–4.9× 不一致 | **H** |
| M2 | 218 + Table 3 | SH 行 4 格全为负：−2.0/−1.0/−0.2/−1.0 | 覆盖率实际变化 −1.99/+1.02/+0.20/+1.00 pp（`cert_v3.json`、`ef_*.json`） | 3/4 格符号方向相反 | **H** |
| M3 | 119 (§2) | released 检查点 16–20 dB | 14.64 / 17.52 / 17.82 / 20.55 dB（`results_v11|v12/*_r0.5.json:rows[clean].psnr`） | 下界差 1.4 dB | **M** |
| M4 | 122 (§2) | 自训模型 107k–300k 基元 | 198,521–295,914（`results_v62/*_base|small.json:n`；v35 最小也有 116,674） | 下界差 91k | M |
| M5 | 185 (§3.1) | 自训降幅 "6.7 to −0.7" | −6.7 … +0.7（Table 2 自训五行） | 两个端点符号都反了 | L |
| M6 | 218 (§3.2) | SH 只移动 "1–2 points" | 0.20–1.02 pp（`ef_*.json`） | 下界差 0.8 | L |
| M7 | 446 (App B) | 部署/标定残差比 0.45–0.91 | 0.838–1.146（`results_v17/cert_audit.json:dep_med/cal_med`） | 区间完全不重叠 | **M** |
| M8 | 453 (App B) | 泄漏后覆盖 0.822 / 0.823 / 0.894 | 0.8231 / 0.8281 / 0.8942（`results_v24/cert_all.json`） | 0.822 vs 0.828（2↔8 颠倒） | L |
| M9 | 459 (App C) | α=0.05 均值 −8.1 | −8.04（`results_v28/cert_a0.05.json`，四场景均值） | 0.06（四舍五入应为 −8.0） | L |
| M10 | 459 (App C) | α=0.10 均值 −14.1 | −13.50（`many_splits.json:drop_mean` 四场景均值） | 0.60 | **M** |
| M11 | 395 (§5) / 467 (App C) | voxel 把幅度缩小 3–4× | 逐场景 2.37 / 3.02 / 4.92 / 1.90（`many_splits` / `vt_*.json`） | 区间 [1.9, 4.9]；只有"端点配对"才给 3.0–4.2 | **M** |
| M12 | 353 (§6) / 473 (App C) | 四个模块 46 条 unit assertions | 静态 `ok(` 调用点 **48**；本机实际执行 **36**（两个文件因缺 torch 无法运行） | 46 既非 48 也非 36 | L |
| M13 | 326 (§3.4c) | 量化后"覆盖率与区间宽度都不变" | 宽度增长 flowers +2.2%、bicycle **+12.1%**、treehill **−18.1%**、stump +0.4%（`widths.json:q_quant8_growth_pct`） | 最大 |18.1%| | **M** |
| M14 | 463 (App C) | 半分辨率 "within 1.4 points of the quarter-resolution values" | 用它自己印的 −12.8/−12.2/−20.3/−13.7 与主表 −10.9/−18.6/−12.8/−11.7 配对：最大偏差 **7.5** | 1.4 vs 7.5 | **M** |

> M1 补充：这不是算术错误，而是**两个量共用一个列名**。若审稿人按 Table 2 复算，比值是
> flowers 1.54×、bicycle 1.16×、treehill 2.47×、stump 1.02× —— 摘要"two to twelve times"
> 与贡献 2"1.9–12.1×"都不再成立。修法只有两种：Table 4 加一列注明区域定义，或把 Table 2 也换成 voxel。
>
> M2 补充：三格的 CI 全部严格在 0 之上（bicycle [0.57, 1.52]、stump [0.49, 1.51]），
> 即"SH 降阶让覆盖率**显著上升**"，论文写成了显著下降。这是全篇最容易被抓的一条。

---

## 3. NO_SOURCE 表

| 组 | tex 行 | 写的是什么 | 追不到的原因（已实际搜过） |
|---|---|---|---|
| N1 | 294（Table 5b flowers 行，5 条断言） | opacity +10.9 [9.3,12.6]、sensitivity +9.3 [6.8,11.6]、reduction 15% | `results_v54/` 只有 `crit_b.json`（treehill/stump）与 `crit_c.json`（bicycle），**没有 flowers 的准则工件**。15% ≈ 1−9.3/10.9 内部自洽，说明三个数是从同一处抄来的，但那一处已不在盘上 |
| N2 | 96（Table 1）、217（§3.2） | `mean |ΔSH| = 3.4–4.1×10⁻⁴` | 全盘 JSON 无任何 |ΔSH| 统计；`results_v20/cert_quant.json` 只存覆盖率，不存扰动幅度 |
| N3 | 122、435、436 | "6000 steps"、"4000 steps" | 没有任何结果 JSON 记录训练步数（`results_v35/v62` 无 step 字段） |
| N4 | 122 | 自训场景 11–16 dB | 五个自训场景**没有任何 PSNR 工件**（PSNR 只存在于 released 的 `compact.json`/`*_r0.5.json`） |
| N5 | 435 (App A) | 4000 步模型 "−0.8 to +3.2 points" | 无对应的 4000 步结果文件；该现象只在旧 markdown（`RESULTS_pruning_v1.md`、`ROUND35_scope_condition.md`）里出现 |
| N6 | 426 (App A) | 0.28M 模型 "13.5 dB"（0.28M 本身 ✓ = 278,955） | `ft200_audit.json` 不存 PSNR；`tail_prune.json:flowers/pup` 的 13.50 是另一个 pruner 的模型，不能挪用 |
| N7 | 463 (App C) | 半分辨率 −12.8/−12.2/−20.3/−13.7 与 "within 1.4" | 全盘无半分辨率工件（无 `half`/`res` 字段、无对应 results 目录） |
| N8 | 27（摘要）、335（§3.5） | 自训场景"400 划分"、自检"over 400 splits" | `results_v62/*.json` 没有划分维度（每变体一个文件，`n_dep=17`）；`results_v58/selfcheck.json` 无 `n_splits` 字段。Table 2 caption 自己写着自训行是 "single-split estimates" |
| N9 | 364–365、399（Related work / §5） | AURA：107k–130k carriers、24–35 views、AUC 0.58–0.72 vs 0.37–0.53 | 外部文献，盘上无副本 → **合理的外部依赖**，不计为错误，但审稿人若要求核对应提供原文 |

**"旧 markdown 有、JSON 已丢"的确证案例**：`research/results_v53/edit_families.json` 存在但
**大小为 0 字节**——它正是 flowers 的 SH/量化编辑族结果。这解释了 Table 3 为什么把 flowers 的
−2.0 标上 `^{\ast}`（单划分，退回 `results_v22/cert_v3.json` 才能复现 −1.985），也解释了
为什么全篇只有 flowers 的 SH 数字没有 400 划分支撑。

---

## 4. 表格与正文自相矛盾清单

| # | 位置 | 矛盾 |
|---|---|---|
| C1 | Table 2 vs Table 4 | 同一量（"30% 剪枝后证书降幅"）两处相差 1.9–4.9×，且 Table 4 未说明换了区域定义（见 M1） |
| C2 | Table 2 / Table 3 / Table 5b | **三套符号约定混用**：Table 2 负=覆盖率下降；Table 5b 正=伤害；Table 3 的 SH 行负号**不表示**覆盖率下降（3/4 场景实际上升）。读者无法跨表比较 |
| C3 | §3.1 (L185) vs §5 (L387) | 同一组自训降幅，一处写 "6.7 to −0.7"，一处写 "0.7–6.7"；数据是 −6.7…+0.7 |
| C4 | App C (L467) vs 它自己的两个区间 | 说 "3–4× 更小"，但括号里给的是 −2.6…−6.1（voxel）对 −10.9…−18.6（block）：端点配对 3.0–4.2×，逐场景 1.9–4.9× |
| C5 | App C (L463) | "within 1.4 points"，但它印出的 −20.3 与主表 −12.8/−18.6 无论怎么配对都差 ≥1.7（最大 7.5） |
| C6 | §2 (L140) vs App B (L453) | §2 说"四个场景"被泄漏拉低 8 点，附录只给三个数（0.822/0.823/0.894），工件也只有 3 个场景 |
| C7 | 摘要 (L27) vs Table 2 caption (L152) | 摘要："across nine scenes, 400 splits per scene"；caption："the five self-trained scenes are single-split estimates" |
| C8 | Table 3 (L201) | flowers 的 `^{\ast}` 在正文与 caption 里**从未定义**；而它恰好标记"这一格是单划分"——与 caption 的 "same protocol" 相抵 |
| C9 | §3.4(b) (L319–320) | 正文引用了 flowers 的 9.3 与 15%，但 Table 5b 的 flowers 行本身无工件（N1） |
| C10 | §3.4(c) (L326) vs `widths.json` | "量化不改变区间宽度"，bicycle 实测 +12.1%、treehill −18.1% |

---

## 5. 附录 A / B / C 与正文的一致性

**附录 A（机制）**
- "0.28M 模型" ✓ 与 `results_v47/ft200_audit.json`（n=278,955）一致；"10.3–12.9 points" ✓ 与
  `three_way.json`（10.27–12.94，400 划分）一致；"fresh coverage 0.900/0.898/0.900/0.900" ✓。
- "5.5–15.4 points" ✓ 与 `results_v61/*_nofinetune.json` 一致（5.51–15.36），**且与 §5 的同一句完全对得上**。
- "10.0–10.8 dB" ✓ 与 `compact.json:psnr_pruned`（9.996–10.803）一致。
- 问题：**13.5 dB 无工件**（N6）；**4000 步模型整段无工件**（N5）；"6000 steps" 无工件（N3）；
  "8 of 9 scenes" ✓（Table 2 计数）。§5 引述附录 A 的 −5.5/−15.4 与附录一致 ✓。

**附录 B（两个陷阱）**
- "0.944–0.988 over-coverage" ✓ 精确复现（`cert_audit.json` 四个 clean 行：0.9494/0.9878/0.9442/0.9654）。
- "0.894–0.901 interleaved" ✓；"8 points below nominal" 的量级 ✓。
- 问题：**"mean residual ratio 0.45–0.91" 与同一工件的 0.838–1.146 完全不重叠**（M7）；
  **0.822 应为 0.828**（M8）；"four scenes" 与三个数不符（C6）。

**附录 C（稳健性）**
- α 扫描：−8.1（真 −8.04）≈ ✓ 但四舍五入应为 −8.0；**−14.1 与 −13.50 差 0.6**（M10）；
  −19.4 ✓（−19.39）。且 α=0.10 这一列只能来自 400 划分的 `many_splits.json`，`results_v28`
  里只有 0.05 和 0.20 两个文件——三列不同源，论文未说明。§3 正文没有引用 α 数字，故不构成正文-附录冲突，
  但与 "fresh coverage close to nominal at each level" 相比，α=0.20 的四场景均值是 0.787（名义 0.80）。
- 区域定义：−2.6…−6.1 ✓、fresh 0.894–0.896 ✓、逐场景比值 1.9–4.9×（M11）。
- 分辨率：**整段无工件**（N7），且自相矛盾（C5）。
- "104-item check" ✓ 与 `verify_paper_numbers.py` 实跑的 "104 numeric checks, 0 failures" 一致。
  **但该脚本解析的是 `PAPER_certificate_invalid.md`**，其主表是 0.899/0.914/0.859/0.903 与
  −11.4/−11.9/−20.6/−12.5，与 main.tex 的 0.901/0.899/0.894/0.900 与 −10.9/−18.6/−12.8/−11.7
  **是不同的表**。所以 §6 与附录 C 的 "Every number in this paper is re-derived … by a 104-item
  automated check" 在 main.tex 上**不成立**——这正是本脚本要补的洞。

---

## 6. 诚实结论：审稿人抽查 20 个数字，会抓到几个？

按"审稿人最可能抽查的顺序"取 20 个（摘要 → 主表 → 家族表 → 下游表 → 规则表 → 附录）：

| # | 抽查对象 | 判定 |
|---|---|---|
| 1 | 摘要 10.9–18.6 | ✓ |
| 2 | 摘要 0.2–2.0 | ✓（上界只靠单划分 `cert_v3.json`，需脚注） |
| 3 | 摘要 "8-bit SH 恰好为零" | ✓ |
| 4 | 摘要 4.6 / 16.8 | ✓ |
| 5 | 摘要 1.9×–12.1× | ✓（但与 Table 2 冲突，见 M1） |
| 6 | 摘要 26–71% | ✓ |
| 7 | 摘要 "nine scenes, 400 splits per scene" | ✗ 5 个场景是单划分 |
| 8 | Table 2 flowers −10.9 | ✓ |
| 9 | Table 2 fresh 0.894–0.901 | ✓ |
| 10 | Table 2 garden −6.7 / 0.956 | ✓（来自 `_base` 变体） |
| 11 | Table 3 SH bicycle −1.0 | ✗ 实际 +1.0（M2） |
| 12 | Table 3 quant 0.00 | ✓ |
| 13 | Table 4 treehill −31.7 | ✓ |
| 14 | Table 4 cert drop −2.6 | ✗ 与 Table 2 的 −12.8 冲突（M1） |
| 15 | Table 5a treehill 0.971 | ✓ |
| 16 | Table 5b stump +2.0 [1.1,2.9] / 83% | ✓ |
| 17 | §2 "16–20 dB" | ✗ 实测 14.6–20.6（M3） |
| 18 | §2 "107k–300k" | ✗ 实测 198.5k–295.9k（M4） |
| 19 | App A "5.5–15.4" | ✓ |
| 20 | App B "0.822/0.823/0.894" | ✗ 0.828（M8） |

**预计 6/20 直接被抓错（30%）**。若审稿人再翻到附录 C（α=0.10、3–4×、"within 1.4"）或去数
unit assertions，会到 **8–9/20**。其中真正致命的是第 11 与第 14 项：一个是符号方向反了、
一个是同一张论文里同一量两个值——这两类不需要跑代码就能被看懂。

反过来，**最值得强调的是主表是干净的**：Table 2 的 47 个数、Table 5(a) 的 20 个数、
Table 5(b) 三个场景的 21 个数、Table 4 命中率 20 个数，全部与 `results_v52/v53/v54/v55/v22/v60`
逐位吻合（容差 = 半个末位）。问题集中在**跨表/跨附录的口径与符号**，以及**旧版本数字残留**，
不是"主结果造假"。

---

## 7. 方法与未覆盖项

**做法**：先用 `glob`/`grep` 摸清每个 JSON 的字段语义（`v52`=400 划分主表；`v53`=编辑族；
`v54`=剪枝准则；`v55`=q 宽度；`v58`=自检；`v60`=voxel+下游任务；`v61`=未微调；`v62`=自训五场景；
`v22`=单划分+修复曲线；`v17`=块划分陷阱；`v24`=泄漏反例；`v28`=α 扫描；`v47/v48`=紧凑模型+PSNR），
再写检查。每条断言的容差、出处与 tex 行号都写进脚本；NO_SOURCE 一律附"搜过哪里"。

**未覆盖 / 未运行（如实记录）**

- **图（`fig1/fig2/fig9*.png`）未审计**：只审了图注里的数字；图片本身是否是当前数据的渲染没有核。
- **`main.pdf` 与 `main.tex` 未做文本级比对**（无 pdftotext 依赖）；若 PDF 是旧编译，本报告不覆盖。
- **单元测试只跑了两个文件**：`test_advise.py`（20 PASS，exit 0）、`test_downstream_task.py`
  （10 PASS，exit 0）。`test_operators.py` 跑到第 6 个 PASS 后 `ModuleNotFoundError: torch`（`test_quantize_sh`），
  `test_voxel_cert.py` 在 import 阶段即因缺 torch 失败。**所以"46 unit assertions"既不能确认也不能否证到
  具体数字，能确认的是静态调用点 48 个**。要真正跑通需 GPU 节点（本机 python 无 torch/scipy/cv2）。
- **外部文献数字**（AURA 的 107k–130k / 24–35 / 0.58–0.72 / 0.37–0.53）无法在盘上追溯，
  需要原文核对；本报告只标注为外部依赖。
- 有一条 MISMATCH 的**归因不确定**：M7（残差比 0.45–0.91）。若"mean residual ratio"指的是别的量
  （例如逐视角均值比而非中位数比），数字可能另有出处；我按最自然的读法（`dep_med/cal_med`）判定，
  并在脚本 note 里写明了这一点。

**建议的最小修复顺序**（供 lead 决策，本审计未改动任何文件）：
① 给 Table 4 的证书列加区域定义或改用与 Table 2 同口径的数字，并据此重算 1.9–12.1×；
② Table 3 的 SH 行改为无符号的"|Δcoverage|"，或在正文说明三场景为覆盖上升；
③ 附录 C 的 −14.1、3–4×、"within 1.4" 与半分辨率四个数整体重写或删除；
④ Table 5(b) flowers 行重跑或删除；
⑤ "46 unit assertions" 改为实跑能得到的数（或注明只在 GPU 机器上可跑）。
