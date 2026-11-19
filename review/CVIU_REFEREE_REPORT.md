# Referee report

**Manuscript:** *Valid but Unusable, and Auditable: Coverage Certificates for 3D Gaussian Splatting Assets Under Editing*
**Venue:** Computer Vision and Image Understanding (Elsevier), research article, single-anonymised
**Author:** Tianji Su (Ningbo University)
**Referee:** CVIU referee, conformal inference × neural rendering
**Recommendation:** **Major revision** (reject-and-resubmit if the asset reconciliation in M1 cannot be closed)

**Files examined.** `D:\3dsg_1\submission\cviu\main.tex` (1265 lines), `supplementary.tex`, `refs.bib`, `highlights.txt`, `COVER_LETTER.md`, the three generated tables, `main.pdf` (32 pp.), `D:\3dsg_1\results_v120\audit_bound.json`, `D:\3dsg_1\results_v120\dump_summary.json`, and — for provenance — `results_v110\{selftrain_dump_summary,selftrain_provenance,baseline_table,extend_tables,task_sweep_4,task_sweep_extra_ref}.json`, `results_v110\region\region_barcelona_st.json`, `results_v90\derived\tables.json`, `results_v80\battery\bicycle.json`. Line numbers below are `main.tex` lines unless stated.

---

## 1. Recommendation and summary

The paper contains a real measurement, a real artifact trail, and one genuinely useful number. It also contains a headline range that its own appendix contradicts by 2.3×, an abstract inequality that its own table violates, a 63-cell audit table computed on a different set of nine assets from the one the paper describes, and a "certified" envelope with no finite-sample content. None of these is fatal individually; together they mean the manuscript cannot be accepted as written. They are, however, almost all fixable from the stored JSON plus rewriting, which is why this is a major revision and not a rejection.

**The paper in six lines (my words):**

1. A 3DGS asset can be shipped with a split-conformal per-pixel certificate: at level 1−α, a held-out pixel's rendering error is below a shipped quantile *q*.
2. The certificate describes the model at issue time, but recipients prune, quantise and merge the asset afterwards, so the paper asks what the guarantee is worth after a rewrite.
3. Measured on four fully optimised checkpoints (400 calibration/deployment splits each), a 30% opacity prune cuts coverage from ≈0.90 to 0.62–0.79 and inflates *q* by 53–122%; SH truncation costs ≤3.5 points and 8-bit quantisation is an exact no-op; the pruning *criterion* moves the damage as much as the budget.
4. The measured magnitude is protocol-dependent: a one-sided ground-truth rescaling attenuates the 30%-prune drop by up to 2.4×, symmetric rescaling does not.
5. The constructive proposal is an *audit* — re-render the edited asset on the calibration views the certificate ships and count residuals below the unchanged *q* — which needs no new labels and tracks post-edit coverage with ≈0.1-point bias (2.2-point MAE), plus a Kolmogorov envelope, loss ≤ KS(F,F′) + ε, that an issuer can pre-compute for a declared edit family.
6. The certified quantity does not transfer to four downstream task families: at a 30% prune the task loss exceeds the coverage loss in 0/36 to 36/36 threshold cells depending on the asset.

That summary is clean, so the contribution *is* statable. The problem is that the paper as written claims strictly more than lines 3, 5 and 6 support (M1–M4).

---

## 2. Desk-rejection risk

**Verdict: probably sent out — I put desk return at 20–25%, and almost all of that risk is mechanical rather than scientific.** CVIU does publish measurement/protocol work, §2 argues the genre precedent explicitly (the 2001 special issue, the 2025 image-quantity study), and the object is unambiguous 3DGS. An editor's seven-day scope call will not be defeated by "this is evaluation, not a method".

What *will* get it bounced or delayed:

- **Two red `[TBD: …]` markers survive into the PDF.** I decompressed the PDF streams and confirmed `Data availability` renders `[TBD: Zenodo DOI]` and `[TBD: GitHub URL]` in red (`main.tex:1236–1237`). Elsevier's submission check flags incomplete data-availability statements, and the paper's own "Released material" contribution is unsupported without them. This is the single highest-probability desk event and it costs ten minutes to fix.
- **The title does not say 3DGS.** "Valid but Unusable, and Auditable" reads as an HCI or software-engineering paper to an editor skimming a table of contents, and "Unusable" is not a term of art in this journal. The subtitle saves it only if the editor reads that far.

**The two sentences that decide it.** The strong one is the abstract's opening (`main.tex:42–44`):

> "A 3D Gaussian Splatting (3DGS) asset can ship with a distribution-free *coverage certificate*: with probability 1−α a pixel of a held-out view has rendering error below a threshold *q*."

That is concrete, correctly scoped, and unmistakably vision. Keep it.

The weak one is the envelope sentence (`main.tex:52–54`):

> "A *Kolmogorov envelope* bounds the loss from above — coverage loss ≤ KS(F,F′) between pre- and post-edit residual distributions — and an issuer can evaluate it *before* shipping by simulating the edit family, so the certificate declares how much damage it tolerates."

An editor who knows any conformal prediction will read this as (i) a statistics claim in a vision journal, (ii) a claim of a guarantee, and (iii) a claim the paper does not actually establish — the inequality as written omits the slack term ε that Proposition 1 carries and that the paper's own Table 5 violates in two cells (M2, M3). If the editor samples one sentence to decide "is this over-claimed?", it will be this one.

**Rewrite (envelope sentence).** Replace with:

> "The loss is also *boundable before shipping*: because an edit acts on the model and not on the view, the coverage drop on deployment views is at most the Kolmogorov distance between the pre- and post-edit residual distributions on the calibration views, plus a calibration/deployment slack. On pruning edits the bound is 1.7× loose at the median; its slack is 4.4 points at the median, and we report both."

**Rewrite (highlight 3, currently "A Kolmogorov envelope bounds the loss an edit can cause; issuers can pre-compute it").** Replace with:

> "Coverage loss is bounded by a Kolmogorov distance the issuer can pre-compute for a declared edit family."

**Rewrite (title, if the author will take advice).** "What a 3D Gaussian Splatting Coverage Certificate Is Worth After the Asset Is Edited" — keeps the object, drops the undefined noun, and puts "3D Gaussian Splatting" where an editor will see it.

---

## 3. Major issues, ranked

### M1. The paper describes one set of nine assets; the 63-cell audit is computed on a different set of nine. *(integrity; must be fixed first)*

**Claim as written.** `main.tex:302–320`: nine assets in three groups — four released Mip-NeRF 360 checkpoints (flowers, bicycle, treehill, stump), "two further released checkpoints from a second archive: bonsai (1.24M primitives, 37 held-out views) and amsterdam", and three BungeeNeRF assets trained by the author (barcelona, bilbao, chicago). Contributions bullet 3 (`main.tex:144–147`) repeats that composition. §5.8 (`main.tex:1038`) says the audit covers "nine scene-checkpoints times seven edits". The cover letter says "five released checkpoints, four trained here".

**Why a referee will not accept it.** `results_v120\audit_bound.json` has exactly 63 rows, and its nine assets are: bicycle, bicycle_i7k, bonsai, flowers, flowers_i7k, stump, stump_i7k, treehill, treehill_i7k — i.e. four released checkpoints, their 7k-iteration twins, and one bonsai. There is no amsterdam, no barcelona, no bilbao, no chicago anywhere in `results_v120` (I searched all six `results_v*` trees). Conversely the 7k twins are never listed as part of the nine in §3; they appear only in Appendix F as a depth control. So the sentence "nine scene-checkpoints times seven edits" is true of the artifact and false of the paper's own asset section, and the asset section is true of a different artifact set (`results_v110\selftrain_dump_summary.json` has barcelona/bilbao/chicago; `baseline_table.json` has amsterdam and a *different* bonsai). A referee cannot tell which nine assets the abstract's "nine assets" means, and the answer changes the headline by 2× (M2).

Worse, **bonsai exists in two incompatible versions**: §3 and Appendix F describe 1.24M primitives / 37 held-out views and a 30%-prune loss of 10.3 points; `dump_summary.json` has 1,157,141 primitives / 33 views, and `audit_bound.json` gives a 30%-prune loss of **0.9** points. Table 2 and Table 5 report 0.9; Appendix F reports 10.3 [9.3, 11.3] — which matches the older `results_v110\baseline_table.json` value of 10.3076 exactly. The paper is reporting two different bonsai checkpoints under one name and has not noticed that one of them barely degrades at all.

**Fix (no new experiments).** (a) Make §3's asset list the nine assets the audit actually covers, naming the 7k twins explicitly and stating that they are optimisation-depth controls rather than independent scenes; move barcelona/bilbao/chicago/amsterdam to a clearly separated appendix paragraph that reports their own numbers (which exist: 50.3/62.9/44.9 at 30%) and does *not* fold them into the "nine". (b) Delete one of the two bonsai checkpoints and say which. (c) Add a one-line provenance sentence to each table naming the JSON behind it and the campaign date. (d) Drop "nine assets" from the abstract until (a) is done.

---

### M2. The abstract's headline range 10.8–27.7 points is contradicted by the paper's own appendix, by a factor of 2.3.

**Claim as written.** Abstract (`main.tex:46–48`): "On nine assets with 400 calibration/deployment splits each and four pruning strengths, geometric edits cost 10.8–27.7 points of per-pixel coverage". Conclusion (`main.tex:1186–1187`): "$10.8$--$27.7$ points of per-pixel coverage at a 30% prune". Highlights line 4. §5.9 (`main.tex:1125`).

**Why a referee will not accept it.** Over the nine assets the paper *says* it measured, the 30%-prune loss is 22.1, 18.9 (bicycle/bicycle_i7k), 0.9 (bonsai), 10.8, 5.7 (flowers/flowers_i7k), 27.7, 20.0 (stump/stump_i7k), 15.2, 12.2 (treehill/treehill_i7k) — **0.9 to 27.7**, not 10.8 to 27.7. Over the nine the paper *describes* in §3 it is 10.3 (bonsai), 17.5 (amsterdam, App. F), 22.1, 10.8, 27.7, 15.2 (released) and **50.3, 62.9, 44.9** (barcelona, bilbao, chicago, App. F) — **10.3 to 62.9**. Either reading falsifies the range; the second falsifies the upper end by 2.3×. The 10.8–27.7 range is the range over exactly the four released checkpoints, and §5.1 does say so ("where the released assets lose 10.8–27.7", `main.tex:519`). The abstract and conclusion drop the qualifier.

The same problem kills "four pruning strengths": only the four released assets have 70/50/30/10%. The other five audit assets have two (50, 30). `dump_summary.json`'s variant list contains no `prune70` and no `prune10` at all; those rows come from `results_v80`.

**Fix (no new experiments).** In the abstract, conclusion, §5.9 and highlight 4, either (i) say "on four fully optimised Mip-NeRF 360 checkpoints, a 30% prune costs 10.8–27.7 points, and on nine assets spanning 0.9 to 27.7", or (ii) quote the full nine-asset range. Do not use an unqualified range anywhere. Delete "four pruning strengths" or scope it to the four released checkpoints.

---

### M3. "Certified envelope" is not certified: KS is an empirical supremum with no finite-sample band, ε is dropped in the abstract, and ε is as large as the effect.

**Claim as written.** Proposition 1 (`main.tex:444–461`): deployment coverage loss ≤ KS(F,F′) + ε, with ε = |F(q)−F_dep(q)| + |F′(q)−F′_dep(q)|. Abstract (`main.tex:52–53`) states the same bound *without* ε. §3 (`main.tex:477–478`): "the certified part KS alone already respects the bound in all 63 cells". §5.8 (`main.tex:1062`): "63/63".

**Why a referee will not accept it.** Four separate problems, in increasing order of severity.

1. *The bound is a two-line triangle inequality, and calling it a Proposition with a "proof sketch" is generous.* Fine as a remark; not as contribution 2.
2. *The abstract's version is false on the paper's own data.* `tab_audit.tex` gives loss/KS = **1.02** for stump/Fisher and 1.02 for stump_i7k/Fisher; four cells exceed 0.93. `audit_bound.json` confirms: `tightness_max = 1.0243`. So "coverage loss ≤ KS" — as printed in the abstract and in the cover letter — is violated in 2 of 63 cells at the level of cell means.
3. *"KS alone respects the bound in all 63 cells" is a misreading of the JSON.* The key that is 1.0 everywhere is `bound_holds_frac` (the bound *with* ε). The key that tests KS alone is `ks_alone_holds_frac`, whose minimum over cells is **0.5375** (stump/Fisher) and which is below 1 in **14 of 63 cells** (bicycle 0.99/0.6275, flowers 0.57, stump 0.9075/0.5375, treehill 0.97, and their 7k twins). At the split level, KS alone fails in up to 46% of draws. The sentence should read "the bound including the slack holds in 63/63 cells; KS alone holds in 49/63".
4. *The slack is not small, and it is the term the recipient cannot compute.* `slack_mean` runs 1.9–8.5 points across cells (median **4.4**). The decision rule of `main.tex:469–470` — "if 1−α−Ĉ(M′) > κ, the asset has been edited outside the declared family" — compares the loss to κ alone, i.e. to a bound that omits a 4.4-point median term. As a policy that is defensible; as a *guarantee* it is not, and the paper's language ("bounds the loss from above", "certified", "still speaks for M′") is guarantee language.
5. *Most importantly: KS is estimated, and the paper never says so.* F and F′ are empirical CDFs of a finite number of correlated calibration residuals. The paper's own effective-sample-size analysis (`main.tex:384–390`) gives n_eff = 77–508 independent scores. A Dvoretzky–Kiefer–Wolfowitz band — and the two references for it are **already in `refs.bib` (`dwk1956`, `massart1990`) but never cited in the text** — gives |KŜ − KS| ≤ sqrt(log(2/δ)/(2 n_eff)) with probability 1−δ. At δ = 0.05 and n_eff = 77 that is **0.139**, i.e. 13.9 points, which is comparable to the KS values themselves (9.4–33.4 points) and larger than the entire measured loss in 12 of the 63 cells. The envelope is therefore not certifiable at any useful level with 16–33 calibration views unless the band is stated, and once it is stated the bound becomes vacuous for the small-view assets. This is the paper's central theoretical claim and it does not survive its own numbers.

**Fix (no new experiments; the JSON already contains what is needed).** (a) Restore ε in the abstract, the cover letter and highlights. (b) Restate the proposition as: loss ≤ KŜ + sqrt(log(2/δ)/(2 n_eff)) + ε, report the resulting κ_δ for δ = 0.05 at each asset's n_eff, and say plainly for which assets the bound is vacuous. (c) Report the per-cell `ks_cal_lo/ks_cal_hi` (already in the JSON, e.g. bicycle/prune50 = [0.083, 0.135]) as the empirical uncertainty on KS — that is a cheaper and more honest version of the same correction. (d) Replace "certified envelope" with "pre-computable bound" everywhere unless (b) is done. (e) Correct "63/63" as in item 3.

---

### M4. The operational claim — the "two-line test" — is never tested, and on the paper's own data it detects almost nothing.

**Claim as written.** `main.tex:466–473`: the issuer publishes κ = max over the declared edit family of KS; "a recipient then has a two-line test: compute Ĉ(M′); if 1−α−Ĉ(M′) > κ, the asset has been edited outside the declared family and the certificate no longer speaks for it." Algorithm table (`main.tex:486–509`) presents this as the recipient's procedure. Abstract: "so the certificate declares how much damage it tolerates."

**Why a referee will not accept it.** Nothing in the paper measures the test's operating characteristics — not its detection rate, not its false-alarm rate. And the paper's own thesis makes the omission fatal: §5.3 argues that *the criterion* is a first-class variable ("a certificate has to carry the one it was issued under"), so a recipient who prunes 30% by Fisher sensitivity instead of stored opacity is exactly the out-of-family case the test exists for.

I ran that experiment from `audit_bound.json` (declare family = {opacity prune 50%, 30%}; κ = max KS over those two cells; recipient applies Fisher 30%). Result: the flag fires on **2 of 9 assets** (bonsai: shortfall 18.3 > κ 10.9; flowers_i7k: 13.5 > 11.9) and fails to fire on the other seven, where the un-flagged losses are 3.8, 5.4, 6.5, 7.2, 10.9, 11.6 and 18.9 points — including 18.9 points on flowers, which passes by 0.2 points. The two assets it catches are the two whose opacity-prune KS happens to be unusually small. No in-family false alarms occur (by construction, since κ is the family maximum), but only because the measured loss/KS ratio is 0.60 at the median. A test that passes an 18.9-point loss and catches a 13.7-point one is not "the practical content of the section".

**Fix (no new experiments).** Add a subsection reporting exactly this: state one declared family, one κ per asset, and a table of (edit outside family, κ, audit shortfall, flagged?) for the 9 Fisher cells (and, if the merge dumps are revived, the merge cells). Report detection rate and the margin. Then either scope the claim honestly ("the test detects edits that exceed the declared *budget*; it does not detect a change of criterion at the same budget, which is why the criterion must be part of the declared family") or extend κ to a criterion-indexed family. That is a stronger section than the current one, and it costs one script over the existing JSON.

---

### M5. §5.8 says the audit is evaluated on "every cell of Table 3". It is evaluated on a disjoint set of cells.

**Claim as written.** `main.tex:1030–1034`: "We evaluate both on every asset×edit cell of Table 3 [tab:dose], re-rendering the edited model on the calibration views…"

**Why a referee will not accept it.** Table 3 (`main.tex:610–658`) has 4 assets × 7 edits = {70%, 50%, 30%, 10% prune, SH 3→1, 8-bit, voxel merge}. Table 5 (`tab_audit.tex`) has 9 assets × 7 edits = {50%, 30%, Fisher 30%, SH 3→1, 8-bit, 6-bit, 4-bit}. The intersection is {50%, 30%, SH, 8-bit} on 4 assets = 16 cells out of 63. The audit covers **none** of the 70%/10% prunes and **none** of the voxel merges — the merge being, by the paper's own §5.3, "the most damaging operation we test" — and covers five assets that never appear in Table 3.

This matters beyond bookkeeping: the abstract's central regression is 30% pruning, but the audit is validated mostly on cells where the edit is small (18 of 63 are quantisation no-ops, 9 are SH truncation ≤3.5 points). Over the 27 pruning cells the audit's MAE is 2.50 points, not 2.23.

**Fix (modest experiment).** Either (a) add the 70%/10% prune and merge cells to the audit — the dumps for `prune70`, `prune10` and `merge40` already exist in `results_v80\battery\*.json` for bicycle and flowers, so two of four assets are recoverable immediately; or (b) rewrite the sentence to "on the 63 cells of Table 5, which cover two pruning budgets, the Fisher criterion, SH truncation and three bit depths, but not the 70%/10% prunes or the merge", and add one sentence acknowledging that the most damaging edit is not audited.

---

### M6. Three incompatible error statistics are reported for the audit, and the one in the table is not the one in the text.

**Claim as written.** `main.tex:1039–1043`: "the mean absolute error is 2.2 points, the worst cell is 5.0 points, and the mean signed error is −0.3 points, i.e. the estimator is unbiased". Table 5's caption (`main.tex:1081–1086`): "error is audit minus coverage in points", with a column whose largest magnitude is 1.2.

**Why a referee will not accept it.** The table's `err` column is `audit_bias_pp`, the difference of the two *means over 400 splits*; its 63 values lie in [−0.63, +1.24]. The text's 2.2 and 5.0 are `audit_mae_pp`, the per-cell mean of |error| *across splits*; the JSON means are 2.226 and 5.005. These are different objects and the paper presents them as one. A referee who adds up the table's column will get 0.3, not 2.2, and will conclude either that the table or the text is wrong.

The bias is also mis-signed: `summary.audit_bias_pp_mean = +0.1296` (median +0.117, range −0.63…+1.24), not −0.3. This is the one place where the error runs *against* the paper: +0.13 points is a much better result than −0.3, and the honest decomposition (bias +0.13, per-split σ ≈ 2.8) says the audit is unbiased and its residual error is pure view-sampling noise — which is a stronger claim than "2.2 points".

Finally the tail is hidden. `audit_abs_p95_pp` has median 5.3 (max 12.8) and `audit_abs_max_pp` has median 8.0 and **max 25.2** (bonsai). "Recovers post-edit coverage to within 2.2 points" is a mean absolute error, not a bound; a single draw can be off by 25 points.

**Fix (no new experiments).** Give Table 5 three columns: `bias` (audit−coverage, means), `MAE` (per-split), `p95 |err|`. Change the text to "mean absolute error 2.2 points across 400 splits, bias +0.13 points, 95th percentile 5.3 points, worst single split 25.2"; add "the audit adds no measurable error beyond the calibration/deployment sampling that any coverage measurement carries (per-split σ ≈ 2.8, split-to-split SD of fresh coverage 1.3–3.4)". Qualify the abstract's "to within 2.2 points" as "2.2 points on average (95th percentile 5.3)". Also note that the worst cell is bonsai — the asset whose fresh coverage is 0.888 and whose calibration set is 33 views — which deserves one sentence, since without bonsai the MAE over the remaining 56 cells is 2.0.

---

### M7. Two campaigns are mixed without disclosure, and Tables 2, 4 and 5 disagree on the same cells by up to 2.4 points.

**Claim as written.** §5.3 (`main.tex:751–757`): Fisher "removes 42% of the damage, from 22.1 to 12.7" on bicycle, "52% (27.7 to 13.3)" on stump, "56% (15.2 to 6.6)" on treehill; "on flowers it nearly doubles the damage, from 10.8 to 19.2". Table 4 reports those values. Contributions bullet 4 (`main.tex:152–154`) repeats "42–56%".

**Why a referee will not accept it.** Table 4's numbers come from `results_v90\derived\tables.json` (`fisher30` drop: −12.71, −19.19, −13.31, −6.64). Tables 2 and 5 come from `results_v120` (`pup30` drop: −11.6, −18.9, −10.9, −6.5). Same nominal cell, two renders, differences of 1.1, 0.3, **2.4** and 0.15 points. Since the paper's own audit error is 2.2 points, the stump difference alone is the size of the paper's headline precision. It also changes the quoted effect: with the v120 values the Fisher ranking "removes" 48%, 61% and 57% of the damage, not 42%, 52% and 56%, and on flowers it multiplies by 1.75, not 1.78.

The same mixing affects Table 3: bicycle SH 3→1 is −3.3 there (v80: −3.274) but −3.5 in Tables 2 and 5 (v120: −3.53). Four SH rows in Table 3 are off by 0.1–0.4 points from the generated tables.

**Fix (free).** Regenerate Table 4 from the v120 `pup30` cells (they are already in `audit_bound.json`), update the three percentages, and add one sentence to §3 saying which campaign produced which table (v80 for the 70%/10%/merge rows, v90 for the task tables, v120 for Tables 2, 5 and 6). A reader who diffs Tables 2, 3, 4 and 5 today finds four contradictions; that is a credibility problem disproportionate to its scientific size.

---

### M8. The task-decoupling result — contribution 6 — rests on numbers that the paper's own later re-measurement moves by up to 13 points, while the text describes the move as 1.7.

**Claim as written.** §5.4 Table 6 and §5.5 Table 7 (`main.tex:855–875`, `957–974`): local re-localisation loses 27.3 / 11.1 / 12.8 / 34.4 points at 30% on bicycle / flowers / stump / treehill, and the task exceeds the coverage loss in 18/36, 12/36, 0/36, 36/36 threshold cells. Appendix E (`supplementary.tex:255–259`): "at the reference cell of Table 6 the task loses 29.0, 7.3, 17.9 and 21.3 points … the same ordering as Table 6 but **up to 1.7 points away from it**".

**Why a referee will not accept it.** `results_v110\task_sweep_4.json` and `baseline_table.json` give 29.0, 7.27, 17.86, 21.30 — consistent with Appendix E — against Table 6's 27.3, 11.1, 12.8, 34.4. The absolute differences are 1.7, **3.8, 5.1 and 13.1** points, and the *ordering* is not the same: Table 6 ranks treehill > bicycle > stump > flowers; the re-run ranks bicycle > treehill > stump > flowers. Treehill's 30%-prune task loss falls from 34.4 (the largest of the four, and the sole basis for the "36/36 cells" claim) to 21.3. Flowers' 11.1 (slightly above the 10.8 coverage loss) becomes 7.3 (well below it), which flips the sign of the comparison on that asset.

The threshold-grid claim is affected too: Appendix E reports the fraction of the **108**-cell grid in which the task exceeds coverage as 0.42, 0.40, 0.17 and 0.97, versus Table 6's 12/36 = 0.33, 0/36 = 0, 36/36 = 1.0 on the 36-cell grid. Two grids, two sets of fractions, and the main text reports only the more dramatic one.

**Fix (free, and it strengthens the paper).** Re-run Tables 6 and 7 from the shipped `task_sweep_4.json` (reference cell 32/±24/2 px/0.6 exists there), report both grids explicitly, and replace "0/36 to 36/36" with the fraction-of-cells formulation. Then fix the Appendix E sentence to state the true maximum discrepancy (13.1 points) and the ordering swap, and explain it (re-built renders from the archive's re-derived entries). A 13-point instability in the task side is, if anything, *more* supportive of the paper's thesis — a task metric that moves 13 points under a renderer rebuild is another instance of "the number is the protocol" — but it cannot be reported as 1.7.

---

### M9. Contribution 2's novelty over AURA is asserted by fiat: no head-to-head, and no argument that would survive one.

**Claim as written.** `main.tex:224–227`: "A head-to-head is not defined without re-implementing its pipeline, because its certificate bounds the mean unreliability of a retained carrier set under its own selection rule while ours bounds the per-pixel error rate of a rendered view; we compare the objects and the quantities they are meant to support, not the implementations."

**Why a referee will not accept it.** AURA is the closest prior art: it attaches a calibrated per-carrier reliability, turns it into a split-conformal bound on the retained set, and — decisively — "extend[s it] into a certified level-of-detail ladder" (`main.tex:218–219`). A certified LOD ladder *is* a family of pruned assets certified together, which is a substantial part of what contribution 2 proposes. The paper's delta is that AURA certifies each rung at issue time whereas the recipient here edits after issue without the issuer's involvement — a real distinction, but it is stated in one sentence and never tested. Declining the comparison on the grounds that the objects differ is exactly the move a referee reads as "the baseline would not favour us". The paper also does not test AURA's selection rule as a fourth pruning criterion, although it tests three criteria and concludes "no criterion dominates" — a conclusion that is only as strong as the criterion set, and the one criterion the nearest competitor proposes is missing.

**Fix.** Two options, in order of cost. (a) Cheap: add AURA's stated score family — isotonic-calibrated per-carrier reliability — as a fourth criterion at the 30% budget on the four released assets. The pipeline is described in enough detail in the prior work (calibrate on held-out views, isotonic regression of reliability against per-carrier error, rank by calibrated reliability) that a faithful re-implementation is a day's work and does not require their code. (b) Cheaper still: compare on the *quantity*, not the implementation — take AURA's reported selection AUC 0.58–0.72 against 0.37–0.53 for opacity and ask what that implies for a coverage drop under a retention rule; state explicitly what a head-to-head would have to hold fixed, and why the comparison is not informative. Either way, remove "not defined".

---

### M10. The paper promises SSIM and never computes it.

**Claim as written.** §3 (`main.tex:319–320`): "the fidelity of each variant is reported with PSNR and SSIM (Table 2)". §5.2 (`main.tex:579–580`): "Table 2 answers with the same renders: PSNR and SSIM for the fresh asset and after each edit".

**Why a referee will not accept it.** Every one of the 72 rows of `tab_fidelity.tex` has `--` in the SSIM column, and `dump_summary.json` contains no `ssim` key at all. The metric was never computed. Two of the paper's own sentences are therefore false, and a vision referee checks SSIM first because PSNR alone at 9.4 dB (treehill) invites the objection that the fidelity comparison is meaningless.

**Fix.** Compute SSIM from the stored renders (it is a one-line addition to the dump script and does not need new renders if the per-view images are still on the node), or delete both sentences and the column, and say PSNR only.

---

### Smaller issues the author should fix without being asked

- `main.tex:176` "494 automated assertions" vs `main.tex:1213` and `supplementary.tex:288` "29 assertions". The cover letter says 494. `review\LITERATURE_SURVEY_2026-11.md:98` records 405 for an earlier suite. Pick one and make it true; with 639 decimal literals in `main.tex`, "all but a handful of the decimal literals are covered by an assertion" (`main.tex:1217`) is not credible at 29.
- `main.tex:174–177`: "the artifacts are the ones Table 1 and every other table are computed from". False: `results_v120` does not contain the 70%/10% prunes, the merge, the opacity×volume criterion, or any task measurement. Tables 3 (partly), 4, 6 and 7 come from v80/v90.
- Table 6's caption (`main.tex:1081`) says "The audit on every asset×edit cell" — of which set? Name the nine.
- `main.tex:1055–1059` and `tab_kview.tex`: the k = 8 row covers 49 cells, not 63 — the 14 missing cells are exactly stump and stump_i7k, which have 16 views and 8 calibration views per split. So "8 of the shipped views" means 8/12 on bicycle, 8/11 on flowers, 8/9 on treehill, and is undefined on stump. Say this; the row currently reads as if it were comparable across assets.
- `main.tex:549` "Coverage is 0.898–0.902 … on all four assets" — true for the four released, but Table 5's bonsai is 0.888 and treehill_i7k is 0.903. Since the 63-cell claim is the one that gets audited, state the nine-asset fresh range somewhere.
- `main.tex:521` "Optimisation depth, not density, is what the measurement requires" contradicts `supplementary.tex:158–162` ("density and optimisation depth co-vary and this measurement alone cannot separate them"). Soften the main-text claim to match the appendix, or the appendix to match the main text; the appendix is the honest version.
- Abstract "harmonic truncation" should be "spherical-harmonic truncation"; as written it is not a term anyone uses.
- Keyword list includes "asset provenance", but no provenance result is measured and the one provenance paper in the bib (`gausstrace2026`) is uncited.

---

## 4. Numerical consistency audit

I checked every number in the abstract, the introduction and §5.8 against `results_v120\audit_bound.json` (A), `results_v120\dump_summary.json` (D), `tab_audit.tex` (T5), `tab_fidelity.tex` (T2) and `tab_kview.tex` (TK). "Mismatch" means the quoted value differs from the file; "no artifact" means no stored file contains the quantity.

### 4.1 Abstract

| # | Claim (line) | Paper | Artifact | Verdict |
|---|---|---|---|---|
| A1 | 30% prune costs 10.8–27.7 pts "on nine assets" (46–48) | 10.8–27.7 | A: 0.9, 5.7, 10.8, 12.2, 15.2, 18.9, 20.0, 22.1, 27.7 | **Mismatch** — the nine-asset range is 0.9–27.7 |
| A2 | "four pruning strengths" on nine assets (47) | 4 | A: two (50, 30) + Fisher; D variant list has no prune70/prune10 | **Mismatch** |
| A3 | quantile grows 53–122% (48) | 53–122 | v90 criterion opacity30: 52.8, 104.7, 121.5, 108.3 | Match (not in v120) |
| A4 | SH truncation + 8-bit "at most 3.3 points and nothing" (48–49) | ≤3.3 | A: max 3.5 (bicycle); `supplementary.tex:228` says 3.7 for the self-trained three | **Mismatch** |
| A5 | "coverage loss ≤ KS(F,F′)" (52–53) | ≤ | A: `tightness_max = 1.0243` (2 cells > 1) | **Mismatch** (ε omitted) |
| A6 | audit "to within 2.2 points for one render pass" (51–52) | 2.2 | A: MAE 2.226 ✓, but k=1 view gives 5.899 (TK), p95 5.3, max 25.2 | Partly; "one render pass" ambiguous |
| A7 | "circular check … off by 11–28 points" (from §3) | 11–28 | A: 0.9 − coverage spans −0.6…+27.8 over the 63 cells | **Mismatch** (see B7) |
| A8 | convention worth 2.4× (57) | 2.4 | Table 7: one-sided/captured = 0.42 (stump), 1/0.42 = 2.37 | Match |
| A9 | task families "disagree by four to eleven times" (58) | 4–11× | v90 `factor`: 7.03, 4.23, 10.92 | Match |

### 4.2 Introduction

| # | Claim (line) | Paper | Artifact | Verdict |
|---|---|---|---|---|
| B1 | 1.0/4.9/22.1/60.0 on bicycle (113) | those | `battery_bicycle.json`: 0.975/4.939/22.085/60.007 | Match (v80, not v120) |
| B2 | Fisher 12.7 vs opacity 22.1 vs opv 40.0 (116) | 12.7 | v90 12.71 ✓; **A: 11.6**; T2/T5: 11.6 | Conflict between tables |
| B3 | "removes 42–56%" (152–154) | 42–56% | v90: 42.4/52.0/56.2%; A: 47.5/60.7/57.2% | Depends on which table |
| B4 | "Fisher ranking removes 52% on stump (27.7→13.3)" (753) | 13.3 | A: 10.9; T2/T5: 10.9 | **Mismatch** with Tables 2/5 |
| B5 | "flowers nearly doubles, 10.8→19.2, q +177%" (754–755) | 19.2 | A: 18.9; v90: 19.19, q 177.1 | Match to v90 only |
| B6 | "opv worst everywhere: 40.0, 61.8; q +263%, +328%" (756–757) | those | v90: 40.03/61.78; 262.8/328.2 | Match (v90) |
| B7 | circular check "returns 0.876–0.927 … true 0.621–0.792: 11–28 points" (428–430) | 11–28 | A: 30% prune coverage 0.6216–0.8440; four released 0.6216–0.7923 | Match only for the four released |
| B8 | "evaluated on every cell of Table 3" (1030–1034, §5.8) | all | Intersection with T5 is 16/63 cells | **Mismatch** |
| B9 | "494 automated assertions" (176) | 494 | `main.tex:1213`: 29; `supplementary.tex:288`: 29 | **Contradiction** |

### 4.3 §5.8 and the tables

| # | Claim (line) | Paper | Artifact | Verdict |
|---|---|---|---|---|
| C1 | 63 cells = "nine scene-checkpoints × seven edits" (1038) | 63 | A: 63 rows, but assets = 4 released + 4 seven-k + bonsai | Count ✓, composition ✗ |
| C2 | MAE 2.2 points (1039) | 2.226 | A `audit_mae_pp_mean` = 2.2264 | Match |
| C3 | worst cell 5.0 (1039) | 5.005 | A `audit_mae_pp_max` = 5.0051 (bonsai/Fisher) | Match |
| C4 | mean signed error −0.3 (1040) | −0.3 | A: **+0.1296** (median +0.117) | **Mismatch, sign and size** |
| C5 | circular check "off by 11–28 on the same cells" (1042) | 11–28 | A: 0.9−coverage = −0.6…+27.8 | **Mismatch** |
| C6 | "off by the same amount on every one of them" (1043) | constant | Contradicts C5 and T5's own `cov` column (62.2–90.6) | **Self-contradiction** |
| C7 | quant8 cells: +0.1 signed, 2.0 absolute (1050–1051) | +0.1/2.0 | A: +0.143 / 2.023 | Match |
| C8 | k views: 5.9/4.0/3.0/2.5, full set 2.2 (1056–1058) | those | A means 5.899/4.049/2.979/2.510; TK identical; 63/63/63/49 cells | Match |
| C9 | KS alone holds 63/63 (478, 1062) | 63/63 | A: `ks_alone_holds_frac` min 0.5375, <1 in 14 cells; `bound_holds_frac` = 1.0 | **Mismatch** |
| C10 | loss/KS median 0.60, range 0.09–1.02, "27 geometric cells" (1063) | 0.600/0.086–1.024 | A over the 27 pruning cells: **0.600 / 0.086–1.024** | Match — but see C11 |
| C11 | same statistic "over the 63 asset×edit cells" (477) | 0.60 / 0.09–1.02 | A over 63: **median 0.120**, range −0.112…1.024 | **Mismatch** |
| C12 | "one cell where the edit improved coverage by 0.4" (1065) | 1 | A: 8 cells with loss ≤ 0; two genuinely positive (+0.16 bonsai/SH, +0.37 treehill_i7k/SH) | **Mismatch** |
| C13 | "+0.91 rank correlation over the 63 cells" (582) | 0.91 | T2 recomputation: 0.82 (63 cells), 0.94 (43 nonzero-ΔPSNR), 0.87 (27 cells ≥0.1 dB) | Not reproducible as stated |
| C14 | 27 cells with measurable dB loss; 1.2–21.3 points/dB, median 3.1 (584–585) | those | At \|ΔPSNR\| ≥ 0.1 dB: n = 27 ✓, ratio 1.18–20.97, median 3.08 | Match (±0.3 on max); cutoff unstated |
| C15 | 2–4 dB band 3.6–18.9; 4–6 dB band 10.8–22.1 (586–587) | those | T2: 3.6–18.9 (n=11), 10.8–22.1 (n=8) | Match |
| C16 | Table 1 median r 0.0258/0.0399/0.0221/0.0310 | those | D pooled 0.0246/0.0389/0.0212/0.0317; mean-of-view 0.0272/0.0402/0.0228/0.0324 | Not reproducible (bicycle 0.0258 = v80 value) |
| C17 | Table 3 SH 3→1 −3.3 (bicycle) vs Table 2 −3.5 | two values | A/T2: 3.53; v80: 3.27 | **Table-vs-table mismatch** |
| C18 | Table 4 Fisher vs Table 2/5 Fisher | 12.7/19.2/13.3/6.6 vs 11.6/18.9/10.9/6.5 | A/T2 | **Table-vs-table mismatch (≤2.4 pts)** |
| C19 | bonsai 1.24M / 37 views (310) | those | D: 1,157,141 / 33 | **Mismatch** |
| C20 | App. F bonsai 10.3 [9.3,11.3] | 10.3 | A/T2/T5: 0.9; v110 `baseline_table`: 10.3076 | **Two different assets** |

### 4.4 Quantities with no artifact in `results_v120` (provenance gaps, not errors)

- q growth 53–122% and the per-cell `q_mean`/`q_edit_mean` (recoverable from `results_v80`, `results_v90`).
- 70%/10% prune rows and the voxel-merge rows of Table 3 (v80, bicycle and flowers only; stump and treehill merge rows have no file I can find).
- The opacity×volume criterion (v90 `criterion`).
- All of Tables 6 and 7 (v90 `criterion_task`, `task2`; v110 `task_sweep_4`).
- The 77–508 effective sample size: no field in either v120 JSON, but it is reproducible from the stated split-to-split SDs (0.09/0.034² = 78; 0.09/0.013² = 533), so the claim is consistent.
- SSIM (absent everywhere).
- Voxel-granularity results: `supplementary.tex:36–43` says they were "measured in our earlier campaign, under the normalised convention" — i.e. not under the paper's primary convention, which is a caveat the main text's §3 (`main.tex:379–380`) and §5.3 (`main.tex:687`) both omit.

---

## 5. Internal contradictions

1. **63 vs 27 cells, same statistic.** `main.tex:477` assigns median 0.60 / range 0.09–1.02 to "the 63 asset×edit cells"; `main.tex:1063` assigns it to "the 27 geometric cells". The JSON says 0.600/0.086–1.024 for the 27 pruning cells and **0.120** for all 63. The first is wrong.
2. **The abstract's inequality vs Proposition 1.** The abstract and cover letter print loss ≤ KS; the proposition has loss ≤ KS + ε and admits ε is unmeasurable by the recipient. The paper's Table 5 has two cells above 1.0.
3. **"63/63" vs the JSON.** `bound_holds_frac` = 1.0 (with ε); `ks_alone_holds_frac` = 0.5375 at worst. §3 and §5.8 both report the first as if it were the second.
4. **§5.8 says "every cell of Table 3"**; the two tables share 16 of 63 cells and none of Table 3's most damaging edit (merge).
5. **Nine assets, three descriptions.** §3: 4 released + bonsai + amsterdam + 3 BungeeNeRF. Cover letter: 5 released + 4 trained. Table 5: 4 released + 4 seven-k twins + bonsai.
6. **Bonsai, two checkpoints.** 1.24M/37 views/10.3 points (App. F, v110) vs 1.157M/33 views/0.9 points (Tables 2 and 5, v120), under one name and no note.
7. **"The certificate is correct when fresh … on all four assets"** (`main.tex:548–549`) vs Table 5's bonsai at 0.888 — the audit's worst cell is precisely the asset where the fresh certificate is 1.2 points below nominal.
8. **Optimisation depth.** `main.tex:521`: "Optimisation depth, not density, is what the measurement requires." `supplementary.tex:158–162`: "density and optimisation depth co-vary and this measurement alone cannot separate them". The appendix is right.
9. **Task numbers.** Appendix E says its re-run is "the same ordering as Table 6 but up to 1.7 points away"; the difference is 13.1 points and the ordering of the top two swaps.
10. **Circular-check rhetoric.** §3 says the circular check "returns 1−α whatever the edit did" and then reports that it returns 0.876–0.927; §5.8 says it "is off by the same amount on every one of them" while reporting a range of 11–28. It cannot be both constant and variable, and if it is constant at ≈0.90 then 0.9 − coverage is a tautology, not a measurement of the check's error.
11. **Reproducibility.** "494 assertions" (contributions) vs "29" (reproducibility section, supplement, status note). "The artifacts are the ones Table 1 and every other table are computed from" vs four tables that are not.
12. **Contribution 3's scope.** "nine assets … at 400 calibration/deployment splits per asset and two region granularities, reporting the effective number of independent scores (77–508)" — the 77–508 is computed on four scenes only (§3), and the two granularities are absent from Table 5 (which is pixel only).
13. **Title vs content.** "Valid but Unusable" asserts validity; §5.1's whole point is that after a 30% prune the certificate is *invalid* (0.62–0.79 coverage against 0.90 nominal). The title describes the secondary result (re-certified but wide) and reads as a claim the paper refutes.

---

## 6. Missing citations

I list only works I can point to a record for: entries already in the author's own `refs.bib` (which states its arXiv IDs were API-checked), works named with IDs in the author's own `review\LITERATURE_SURVEY_2026-11.md`, and two canonical conformal-prediction papers that any CP referee will expect and that I am confident about.

**A. Already in `refs.bib`, never cited — and load-bearing.**
1. `dwk1956` — Dvoretzky, Kiefer & Wolfowitz, *Ann. Math. Stat.* 27(3), 1956. The finite-sample Kolmogorov band. Not citing it in a paper whose central object is a Kolmogorov distance is the single most conspicuous omission in the manuscript (see M3).
2. `massart1990` — Massart, *Ann. Probab.* 18(3), 1990, the tight DKW constant. Same reason.
3. `angelopoulos2023` — Angelopoulos & Bates, *Conformal Prediction: A Gentle Introduction*, FnT ML 16(4), 2023. The standard entry point; its absence from a CVIU paper introducing split conformal to a vision audience is odd.
4. `adaptiveconformal2026` — Zaman et al., *Adaptive Computation with Conformal Certification*, arXiv:2610.19189. Directly on certifying a computed quantity — the same move as the audit.
5. `gausstrace2026` — Han, Luo & Wan, *GaussTrace: Provenance Analysis of 3D Gaussian Splatting Models*, arXiv:2606.10612. The keyword list advertises "asset provenance"; this is the provenance paper in the author's own bib.
6. `cleangs2026` — Shivottam et al., *CleanGS: Pareto-Guided Post-Hoc Cleanup of 3D Gaussian Splatting Scenes*, arXiv:2601.00913. Post-hoc rewriting of a shipped asset is precisely the paper's edit operator; §3's edit taxonomy should cite it.
7. `yubi2026` — Nishizawa et al., *YUBI-Real2Sim: 3DGS Scene Verification for Reliable Policy Evaluation*, arXiv:2610.17521. A downstream-consumer reliability study for splat assets; the natural companion to §5.4–5.5.

**B. 2025–2026 compression / quality work the paper's own survey lists but the manuscript does not cite.**
8. *3DGS.zip* compression survey, arXiv:2407.09510 — the paper cites three compression methods and no survey; a CVIU referee in compression will ask for one.
9. GScomp-QA, arXiv:2605.26880; 3DGS-VBench, arXiv:2508.07038; 3DGS-VBench+, arXiv:2611.04498; GS-QA, arXiv:2502.13196; MUGSQA, arXiv:2511.06830. §5.2's "why not a perceptual metric" paragraph cites one survey and one metric; the benchmark family is the obvious counter-question ("did you try a learned quality metric?").
10. Matryoshka GS, arXiv:2603.19234; Budgeted-GS, arXiv:2610.03162; FilterGS, arXiv:2603.23891. The paper's premise is that recipients re-simplify assets under a budget; it cites two LOD works and should cite the budget-conditioned ones, since a budget-conditioned method is what would actually consume the certificate.
11. LinearMask-GS, arXiv:2609.10095 — cited in `refs.bib` as BMVC 2026 without an arXiv ID; the survey lists the ID. Add it, since a fourth criterion family is exactly what M4's decision rule needs.

**C. Canonical conformal work invoked by name but never cited.**
12. `main.tex:253`: "Weighted conformal prediction repairs coverage when the likelihood ratio is known and adaptive methods track a slowly changing level, but neither applies here" — neither is cited. Add Barber et al. 2023 (already cited elsewhere) for the weighted case, and Gibbs & Candès, *Adaptive Conformal Inference Under Distribution Shift*, arXiv:2106.00170, for the adaptive case.
13. `main.tex:103`: "the score's parameterisation (calibration) or the training objective (conformal training)" — "conformal training" is uncited; Stutz et al., *Learning Optimal Conformal Classifiers*, arXiv:2110.09192.
14. A per-pixel *risk* guarantee is closer to what §5.9's coverage-assurance discussion needs than a per-pixel marginal coverage one: Angelopoulos et al., *Conformal Risk Control*, arXiv:2208.02814.

**D. Deliberately not requested.** I do not ask for a comparison to any method the paper could not run in a revision cycle, and I have not invented identifiers: items 1–11 are traceable to the author's own `refs.bib` or `review\LITERATURE_SURVEY_2026-11.md`, items 12–14 are standard and should be checked before insertion.

---

## 7. What I would ask for in revision (ten lines, cheapest first)

1. Fill the two `[TBD]` markers in Data availability; without a DOI the "Released material" contribution is a promise, not a contribution.
2. Reconcile the assertion count (494 vs 29) and delete "the artifacts are the ones … every other table [is] computed from".
3. Scope every occurrence of "10.8–27.7" to the four released checkpoints, and quote the nine-asset range (0.9–27.7) or the §3-nine range (10.3–62.9) where the nine are claimed.
4. Restore ε in the abstract, cover letter and highlights; correct "KS alone holds 63/63" to "49/63 cells for every split, 61/63 cell means"; fix "mean signed error −0.3" to +0.13.
5. Fix §3's sentence that attributes the 27-cell tightness statistic to 63 cells (it is 0.12 over 63), and the "one cell improved by 0.4" (there are eight non-positive cells, two genuinely positive).
6. Regenerate Table 4 from the v120 `pup30` cells so it agrees with Tables 2 and 5, and update 42–56% to 48–61%; regenerate Table 3's SH rows, or state which campaign each table comes from.
7. Compute SSIM or delete the two sentences that promise it; state the |ΔPSNR| ≥ 0.1 dB cutoff behind "27 cells"; state the k = 8 = 49-cell restriction in the caption.
8. Add the DKW/Massart band to Proposition 1 with the paper's own n_eff, report κ_δ at δ = 0.05, and say for which assets the bound is vacuous.
9. Report the declared-family detection experiment (M4) from the stored JSON: κ per asset, out-of-family Fisher cells, flagged or not, and the margin. This is the section the paper is missing and it costs one script.
10. Re-run Tables 6 and 7 from `task_sweep_4.json`, report both the 36-cell and 108-cell grids, and correct Appendix E's "up to 1.7 points" to the true 13.1 with the ordering swap. Add the AURA score family as a fourth criterion (M9).

---

## 8. Verdict on framing: is "auditable" a contribution, or a reframing of a negative result?

**The case that it is a contribution.** "Auditable" names an object that did not exist in this literature: a *shipping specification*. The paper says a certificate must carry (α, q, region, convention, κ, V_C, {r_i}), and it shows that this list is not decorative — with it, a recipient can recover post-edit coverage with a bias of +0.13 points and no labels; without it, the recipient can only guess. That is a change in what issuers must publish, and specifications have been publishable contributions in this journal's tradition (the 2001 special issue is full of them). The audit also kills a specific, tempting fallacy — re-running calibration on the edited model returns the nominal level by construction and tells you nothing about the old certificate — and naming that fallacy is worth something, because the paper shows it is the *first* thing a practitioner does. On this reading the constructive half converts a "your guarantee broke" paper into "here is what to ship and how to check it", which is exactly the difference between a workshop complaint and a journal article.

**The case that it is a reframing.** Look at what the two objects actually are. The audit is "evaluate the model on the calibration set at the old threshold" — one line that every reader of this paper will have thought of before reaching §3; its contribution is not the estimator but the measurement that the estimator is unbiased, which is a *validation* result, i.e. more measurement. The envelope is a triangle inequality, stated as a Proposition, with a slack term the recipient cannot compute, an empirical supremum presented as a bound, no finite-sample correction, and an operational rule that — on the paper's own JSON — passes an 18.9-point loss while catching a 13.7-point one. Neither object changes a decision the paper exhibits. And the phrase "two missing objects" is not accurate as prior art: AURA already certifies a *ladder* of pruned assets and already reports the criterion ordering the paper reports in §5.3. On this reading "auditable" is the wrapper that lets a negative result be sold as a protocol, and the wrapper is thinner than the measurement it wraps.

**Which the referee would believe.** Both, in that order of weight: 60/40 for the reframing reading, and that is enough to require a rewrite of the framing rather than a rejection. The reason is not that the audit is unoriginal — measurement papers are allowed to validate obvious estimators, and this one does it well — but that the paper *ranks* its contributions in the wrong order and oversells the weaker one. Contribution 2, the envelope, is the one the title and the abstract lead with ("bounds the loss from above"), and it is the one that does not survive: no finite-sample content, no demonstrated decision, a slack as large as the effect. Contribution 1, the audit, is real but modest, and the paper's own data support a *stronger* claim than the one it makes (bias +0.13, i.e. lossless relative to view-sampling noise). Contribution 3, the dose–response, is the actual scientific content and is buried under both.

**What I would advise the author to do with the framing, concretely.**
- Lead with the measurement and the shipping specification, not with "two missing objects". A title of the form "What a 3DGS Coverage Certificate Is Worth After the Asset Is Edited — and What It Must Ship" is defensible on the paper's evidence; the current title is not.
- Demote "Kolmogorov envelope" from a headline to a subsection titled "a pre-computable bound, and how loose it is", with the DKW band reported and the slack reported. It is a perfectly good subsection. It is not a contribution of the same rank as the dose–response.
- Either demonstrate one decision the audit changes (the M4 experiment is the cheapest candidate: flag/no-flag on out-of-family edits, with a stated false-alarm rate) or stop calling the pair "the practical content of the section".
- Say plainly, once, that the negative result is the contribution and the protocol is what makes it actionable. The conclusion already half-says this ("The audit is what turns a negative result into a protocol"); move that sentence to the abstract and delete the triumphal register around the envelope.

**Bottom line.** Major revision. The measurement is worth publishing, the artifacts are real enough to check (which is rare and to the author's credit), and three of the four things that would sink the paper — the range, the ε, the 63/27 confusion — are text edits. The fourth, the asset-set mismatch, needs one honest paragraph and a decision about which nine assets the paper is about. If that paragraph cannot be written, the paper should be rejected, because the tables would then be describing experiments the text does not.
