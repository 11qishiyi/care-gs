# Response to Reviewers — draft (for the OpenReview thread)

> 说明：这是给 `submission/main_v2.tex` 配套的逐条答复草稿。每条格式为
> **Concern → What we changed → Where to look**。英文可直接粘贴，方括号内为中文备注。

---

## R1 — Statistics / conformal prediction

**C1. "The headline number mixes two statistics: the numerator is a pixel-level task
measurement, the denominator is a voxel-level coverage drop. At matched granularity the
'under-reporting' collapses."**

Accepted, and this was the most consequential error in the previous version. The two
quantities are now reported side by side and never divided across granularities: Table 1
gives coverage loss at both the pixel and the world-space region level for the same prune,
and Table 3 lists the task loss next to both. The ratio paragraph now reads "1.0–2.5×
(pixel) or 1.9–12.1× (region)", states explicitly that the ratio's spread is six-fold at
region granularity, and concludes that the ratio is not a constant of the phenomenon. Figure
1(b) plots every (coverage loss, task loss) pair so a reader can check the pairing directly.
[中文：口径混用已修；比值降级为并列陈述，且给出逐场景点图。]

**C2. "The relation reverses at the milder edit and this was not reported."**

Correct, and it is now the centre of the paper rather than an omission. Table 3 adds the 50%
prune: coverage falls by 2.1–5.3 points in all four scenes while the task falls by less in
three (1.8, 2.8, 2.1 points) and *improves* by 0.6 points on one. Section 3.3 states the
consequence: coverage and downstream utility are not monotonically related, so "coverage
under-reports damage by a factor of k" is not a well-posed claim; the well-posed claim is
that the two quantities order assets differently.
[中文：把 50% 档的不单调性升格为主线之一，并据此改写主张形式。]

**C3. "Section 2 says coverage is a view-level quantity, but the estimator pools pixels."**

Rewritten. Section 2 now defines the score (per-pixel residual), the quantile (over pooled
calibration pixels, with the exact index), and coverage (fraction of deployment pixels below
the quantile), then separates the two roles of views: they are the unit of *resampling*, not
the unit of the estimate. We added the quantitative justification that was missing: the
split-to-split standard deviation of fresh coverage is 0.018–0.040, whereas a binomial model
on 2.9×10⁵ independent pixels would give 6×10⁻⁴, so the effective number of independent
scores is 56–277. That number is now reported in the setup and again in the limitations.
[中文：定义落地为"像素级估计 + 视角级重采样"，并补有效样本量推导。]

**C4. "The 400 splits are not independent replicates and the brackets are not confidence
intervals."**

Relabelled throughout: the brackets are split-to-split percentiles, and the text says they
quantify sensitivity to calibration-set composition conditional on the rendered view pool and
are not a CI for the scene. The abstract no longer says "paired confidence intervals".
[中文：全文改称 split-to-split interval，并明确其条件性。]

**C5. "The width-growth claim compares a single-split q against a 400-split mean q; the
'free' quantisation edit also shows double-digit growth, which reveals the noise floor."**

Accepted — that was an estimator mismatch, and we used the reviewer's own diagnostic to fix
it. All quantile growth is now paired: the clean and edited quantiles of the *same*
calibration set. Under that estimator the 8-bit SH edit — an exact no-op — gives 0% growth
in all four scenes, and the 30% prune gives +26% to +83% on the same views. The no-op row is
kept in Table 2 and Figure 2(b) precisely as the noise-floor control.
[中文：q 增长改为同划分配对；no-op 的 0% 增长原地保留为噪声地板。]

**C6. "Table 5a omits the n=all column, where coverage is actually below nominal."**

Restored. Table 4(a) now runs to n=all (0.892 on flowers, 0.876 on bicycle, 0.927 on
treehill, 0.902 on stump), and the text no longer claims "2–4 views restore coverage to near
nominal" without qualification: it says coverage returns to within three points of nominal at
any n ≥ 2, that the smallest calibration sets over-cover (0.971 on treehill), and that what
does not return is the width.
[中文：补回 n=all；把"2–4 视角能修复"改成"有效性任何 n 都回来，宽度回不来"。]

---

## R2 — Domain / positioning

**C7. "The first contribution is a corollary of exchangeability; AURA already discusses
distribution shift and per-scene re-certification."**

Accepted. "Editing breaks a conformal certificate" is now setup, not a contribution; the
title, abstract and contribution list lead with the decoupling (a certificate can be valid
and uninformative at once) and with the price of validity. Section 4 states AURA's
exchangeability caveat and its per-scene remedy explicitly, and positions our question as
what happens when the *asset* changes rather than the scene. We removed the claims that AURA
evaluates no downstream task and that a word search establishes the boundary — both were
inaccurate or beside the point.
[中文：删掉了不实的 AURA 断言与"数词论证"，改为正面陈述其 caveat 再分界。]

**C8. "The region granularity changes the headline by 3–4× and is buried in the appendix."**

Promoted to the main table (Table 1) and to the abstract, and Figure 1(a) makes the dependence
visual. The appendix retains only the definition of the two region types and the note that
any absolute "usable area" must quote its granularity.
[中文：区域粒度进主表 + 摘要 + 图 1(a)。]

**C9. "Rule (c) over-generalises from SH-only 8-bit to 'quantisation'."**

Narrowed to a mechanism statement with a boundary: an edit whose perturbation is orders of
magnitude below the residual is free (3.4–4.1×10⁻⁴ against a residual three orders larger),
and quantisation that moves positions or scales is geometric and must be treated as harmful.
[中文：规则 (c) 改成有条件的机制陈述 + 边界。]

**C10. "Related work is missing conformal-under-shift, the proxy-metric precedent, and the
provenance framing."**

Added Barber et al. (2023) and now actually *use* Tibshirani et al. (2019) to explain why
weighted conformal does not apply without deployment labels; added the industrial proxy-metric
note; added model cards / datasheets as the framing for an artefact whose claims expire.
We deliberately did not add the 3DGS-uncertainty line, which would open a comparison we do not
run.
[中文：补三处相关工作并说明为什么有一条故意不补。]

**C11. "No image-quality table; the 16–20 dB working point cannot be located."**

Acknowledged as a limitation rather than papered over. Every table now carries the median
absolute residual of the asset (0.047 on flowers to 0.153 on stump), Section 5 states that
this is above the 25–27 dB regime reported for these checkpoints at full resolution, that our
renderer compares against archive ground truth without per-image exposure compensation, and
that all claims are about *changes* measured on identical views and renders, not about
absolute coverage levels. We flag the exposure convention as the first thing to check in a
follow-up. [中文：明确写进 limitations，并把"只主张变化量"讲清楚。]

---

## Cross-cutting

**C12. "Nineteen reported numbers do not match the stored artifacts; the SH row has three
sign errors."**

All fixed. The SH row now reports the measured signs (+1.0 / +0.2 / +1.0 points, all
interval-bearing) and the single-split flowers cell is marked as such; the appendix alpha
mean is −13.5 (not −14.1), the region-factor claim is 1.9–4.9× (not 3–4×), and the
unverifiable cells (half-resolution sweep, the non-fine-tuned compact control, the
sensitivity-versus-opacity comparison, the "104/46 assertions" phrasing) are removed rather
than patched. A checker now runs 152 assertions directly against the LaTeX source and exits
non-zero on any mismatch; it is shipped in the supplement.
[中文：19 处逐条修正；无法追溯的数字删除而非硬凑；新增对 LaTeX 源的校验器。]

**C13. "The sensitivity-pruning rule has target-view leakage."**

The rule is withdrawn. Section 5 explains why: the ranking used ground truth from views that
also appear in deployment, which biases the comparison in favour of sensitivity pruning, so
no number from that experiment is quoted until it is rerun with calibration-only supervision.
[中文：撤掉规则 (b) 并写明原因，不留半信半疑的数字。]

**C14. "A single downstream task with hand-set thresholds, and the paper's own refutation
condition was never tested."**

Not yet addressed, and we say so in two places rather than hiding it. Section 3.3 and Section
5 name the missing tests — a second task family and a sweep over the four task thresholds —
and the claim is stated so that it does not depend on them: the decoupling is claimed as an
ordering failure across scenes and edit strengths at the reported setting, not as a
threshold-independent constant.
[中文：唯一未解决项，明确写出，并把主张限定到不依赖它的形式。]

---

## What is in the revised package

| Item | File |
|---|---|
| Revised manuscript (9 pages, 2 new figures) | `submission/main_v2.pdf`, `submission/main_v2.tex` |
| Anonymised supplement (66 files: operators, drivers, per-scene JSONs, tests, checker, figures) | `submission/supplement.zip` |
| Number checker against the LaTeX source (152 assertions) | `tools/verify_tex_v2.py` |
| Figure regeneration from artifacts | `tools/make_figs_v2.py`, `figures_v2/` |

---

## Round-3 update (new data, two reviewer items now closed)

**C11 / M7 (working point) is now resolved rather than acknowledged.** We re-ran the whole
measurement on four released 40k checkpoints taken from a public 3DGS output archive, with the
archive's own held-out ground truth. The checkpoints render at 16.8-23.9 dB under the captured
convention, and the 16-20 dB figure of the first version was an artefact of normalising each
ground-truth view to a common brightness: the same asset drops from 22.2 to 17.1 dB (bicycle)
and from 23.9 to 13.9 dB (stump) under that convention. The convention also **attenuates the
measured invalidation by up to 2.4x** (stump: -11.7 vs -27.7 points), which is now a section of
the paper (Section 3.3) and a reproducibility warning for this literature. All tables now carry
PSNR, median residual and the convention.

**C14 / B4 (single task, hand-set thresholds) is now addressed.** The revised paper sweeps
P(patch size) x P(search radius) x tolerance x peak threshold: 36 cells per (scene,
configuration), 108 cells per scene. Two facts come out. The task is damaged at 30% pruning in
**36/36 cells on both scenes**, so the effect is not a threshold accident. But the task loss
exceeds the pixel coverage loss in **18/36 cells on bicycle, 12/36 on flowers, 0/36 on stump and 36/36 on treehill** --- which
is exactly why we no longer claim a multiplier and instead claim an ordering failure, with the
reversal at the milder prune shown explicitly (Section 3.4, Table 4).

**Dose-response (new evidence for C2).** Pruning to 70/50/30/10% costs 1.0/4.9/22.1/60.0
coverage points on bicycle and 0.8/3.6/10.8/40.8 on flowers: the damage is concentrated in the
last doubling of compression, which is the practically relevant regime.

**A second task family is now measured (round 4).** A global geometric registration front-end
(Harris corners, patch descriptors, ratio test, RANSAC translation, inlier ratio at 2 px) gives
a third answer on the same assets: at 30% pruning it loses **3.9 points on bicycle and 2.6 on
flowers**, where local matching loses 27.3 and 11.1 and the certificate loses 22.1 and 10.8.
At 10% pruning all three collapse together (60.0/76.3/31.1 and 40.8/60.7/28.4). The three
yardsticks therefore differ by up to a factor of seven at the same edit, which is the strongest
form of the claim we can defend: coverage is not a conservative or an anti-conservative stand-in
for a task -- it is a different functional, and the direction of its error depends on the task.
