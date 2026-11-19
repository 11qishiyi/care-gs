# Appendix skeleton for the extension experiments (fill numbers from `results_v110/extend_tables.json`)

> 用途：等 GPU 节点上的 `region_*.json` 回来后，把这里的三块内容填进 `submission/final/main.tex`。
> 三块都是**附录**（主文只加一句指针 + Table 2 三行），以保证正文不超过 12 页。

## H.1 Bit depth: 8, 6 and 4 bits of SH quantisation

正文一句（放在 §3.2 的 8-bit 行之后）：
> We pushed the same storage edit to 6 and 4 bits; Appendix~\ref{app:bits} shows the certificate is insensitive across the whole range.

表格（每资产一行，pixel 与 64×64 block 两列，括号内为 2.5/97.5 配对分位）：

| asset | 8 bit | 6 bit | 4 bit |
|---|---|---|---|
| bicycle | {Q8_B} | {Q6_B} | {Q4_B} |
| flowers | … | … | … |
| stump | … | … | … |
| treehill | … | … | … |

结论句（只在数字支持时写）：
- 若三档都 <1 点：**"the precision edit is inert over a 16× range of storage budget, so the invalidation we measure is not a quantisation artefact"**。
- 若 4-bit 出现可观降幅：改成 **"…inert down to 6 bits; at 4 bits the store itself starts to cost {…} points, an order of magnitude below the geometric edit at the same budget"**（必须按实测写，不许夸大）。

## H.2 Optimisation depth: the same scenes at 7k and 40k iterations

动机一句：
> Our scope condition is "fully optimised asset"; the archive also ships the 7k-iteration checkpoint of each scene, which lets us test the condition inside the same scene instead of across pipelines.

表格（30% prune，pixel [2.5, 97.5]，block 括注）：

| asset | 40k (M primitives) | 7k (M primitives) |
|---|---|---|
| bicycle | {B40} | {B7} |
| … | | |

判据：
- 若 7k 降幅显著更小（例如 < 一半）：支持 *optimisation depth* 的读法 → 写 "the damage grows with optimisation depth on the same scene, consistent with the cross-pipeline evidence in Appendix C"。
- 若两者相当：**必须改写 §5 的 scope 句**，把"fully optimised"降级为"released checkpoints of this archive"，并在 limitations 里认领；**不许保留原判据**。

## H.3 A fifth asset (bonsai, 30k) and its 7k twin

一句动机：外部效度——第五个资产来自同一归档但不同场景族（indoor, portrait），且与 pipeline 内 7k 对照同源。

表格：prune 50% / 30% / quant8（pixel + block）。

判据：若 bonsai 的 30% 剪枝降幅落在 10.8–27.7 区间内 → "the fifth asset falls inside the range of the other four"；若超出 → 按实测写并说明（例如方向一致但幅度更大/更小），**不许把区间悄悄改成包含它**。

## 同步要改的三处
1. `submission/final/main.tex` 摘要：只在**不夸大**的前提下加半句（例如 "a fifth asset and 4-bit storage quantisation behave the same way"），**不改已发表数字**。
2. `tools/verify_tex_v3.py`：把新表的每个数字加进断言（来源 `results_v110/extend_tables.json`），并保证旧 437 条仍全绿。
3. `SUBMISSION_CHECKLIST.md` + `DELIVERABLES.md`：记录新实验与新的断言数。
