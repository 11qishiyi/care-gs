# J1/J2 — rate–reliability planning: the frontier, the collision, and why the audit is not optional

**Rounds J1 and J2, 2026-11-18. CPU only, no node rented.** Both rounds are *secondary analyses* of grids that
were measured in earlier rounds for other purposes:

| grid | what it is | used for |
|---|---|---|
| `experiments/artifacts/a4/m5_rd_v2.json` | 8 scene-checkpoints × **20 coded variants**, measured rate, measured bytes/primitive, paired coverage drop (400 splits), **PSNR + SSIM + LPIPS** | J1 (frontier, collision, planners, dB↔pp) |
| `results_v120/audit_bound_nobonsai.json` | 8 scene-checkpoints × **7 edits = 56 cells**, truth coverage, audit estimate, envelope | J2 (decision rules) |

Criteria below were written **before** either script ran, on data measured for another purpose, so they are
secondary-analysis criteria, not pre-registration in the M-series sense. Verdicts are given verbatim.

---

## 0 What this round adds to the paper

The JVCIR version needs a *method*, not only a measurement. J1/J2 supply it in four statements, each backed by a
table: (i) within a coverage tolerance the achievable rate is set by **which action** you spend the budget on, not by
how aggressive you are; (ii) at the same rate, the standard action (pruning) costs **13–23 coverage points** where
quantisation costs 0.5–2.5; (iii) every coverage-blind planner violates the tolerance, and a fixed safe configuration
gives up 62–72 % of the rate; (iv) the only decision rule that never false-accepts is the **audit on the shipped
calibration views** — a cross-asset prior false-accepts 2–4 of 56 cells.

---

## 1 Asset set and the exclusion rule (stated, not hidden)

Rule, applied mechanically: **an asset is excluded if any variant improves coverage** (a positive drop), because that
is a ground-truth/exposure artefact rather than a compression effect.

* kept (6): `bicycle`, `bicycle_i7k`, `flowers`, `flowers_i7k`, `stump`, `stump_i7k`
* excluded (2): `treehill`, `treehill_i7k` — 2 and 5 variants respectively *raise* coverage; clean PSNR of
  `treehill` is 9.41 dB against the archive GT, which is the exposure mismatch documented in N16.

This is the same rule as `experiments/protocol_assets.py`; nothing here re-admits an asset the protocol excluded.

---

## 2 J1-E1 — the rate–reliability frontier exists, and pruning is not on it

Largest rate whose measured coverage loss stays within ε:

| ε (pp) | best rate, any action | best rate, quantisation only | best rate, pruning only |
|---|---|---|---|
| 0.5 | **8.72 – 12.97×** (5 of 6 assets; `stump` has no admissible point) | same | **none on any asset** |
| 1.0 | **8.97 – 15.78×** (6/6) | same | **none on any asset** |
| 2.0 | 9.60 – 15.93× | same | 1.22 – 1.29× (`p90` only; `flowers` has none) |
| 5.0 | 12.94 – 15.93× | same | 1.25 – 2.32× (`p50`/`p70`/`p90`) |

Reading, and it is the whole method claim in one line: **inside a one-point coverage tolerance the quantisation
family reaches 9–16×, while pruning cannot reach 1.3× on any of the six assets.** The two families are not
different aggressiveness levels of the same knob; only one of them is admissible at all.

At ε = 1 pp the frontier points also carry the full metric triple, e.g. `bicycle` 9.68× at −0.83 pp with PSNR 21.90 /
SSIM 0.7431 / LPIPS 0.2060; `stump` 8.97× at −0.72 pp with 23.62 / 0.7537 / 0.1889.

**Verdict J1-C1** (predicted: quantisation dominates pruning at ε ≤ 2 pp on ≥ 4 of 6 assets): **PASS, 6/6 at ε ≤ 1 pp.**

---

## 3 J1-E2 — matched-rate collision: what each action buys at the rate the planner picks

ε = 1 pp, rate = the frontier rate from §2. "Fidelity-first" = the variant at or below that rate with the highest
PSNR; "prune-first" = the highest-rate pruning variant at or below that rate.

| asset | rate | planner | planner drop | fidelity-first | its drop | prune-first | its drop |
|---|---|---|---|---|---|---|---|
| bicycle | 9.68 | `m16_o6_sh3` | −0.83 | `d2_m16_o8_sh8` | −2.12 | `p20` | **−20.43** |
| bicycle_i7k | 13.27 | `d1_m16_o8_sh4` | −0.95 | `d2_m16_o8_sh8` | −0.49 | `p10` | **−15.09** |
| flowers | 9.64 | `d2_m16_o8_sh4` | −0.89 | `d2_m16_o8_sh8` | −0.86 | `p20` | **−23.20** |
| flowers_i7k | 15.78 | `d0_m16_o8_sh8` | −0.74 | `d0_m16_o8_sh8` | −0.74 | `p10` | **−19.35** |
| stump | 8.97 | `m18_o6_sh3` | −0.72 | `d2_m16_o8_sh8` | −2.47 | `p20` | **−20.79** |
| stump_i7k | 9.90 | `m16_o6_sh3` | −0.85 | `d2_m16_o8_sh8` | −0.99 | `p20` | **−12.74** |

Two readings, both needed in the paper:

1. **Against pruning the margin is not close**: at the same rate, the pruning route costs **12.7–23.2 points** where
   the planner costs 0.7–0.95. Any pipeline that reaches a mid rate by deleting primitives has already destroyed the
   guarantee, whatever its PSNR says.
2. **Against fidelity-first the margin is small and sometimes negative**: `bicycle` (2.12 vs 0.83), `stump`
   (2.47 vs 0.72) show that a PSNR-maximising choice *does* lose more coverage; `bicycle_i7k` (0.49 vs 0.95) and
   `flowers` (0.86 vs 0.89) show it does not always. **Claim only what holds 6/6: pruning is dominated. Claim the
   fidelity gap as "0.5–2.5 points, sign varies", not as "fidelity is always wrong".**

**Verdict J1-C2** (predicted: pruning loses ≥ 5 pp at matched rate on ≥ 4/6 assets): **PASS 6/6** (12.7–23.2 pp).
**J1-C2b** (predicted: fidelity-first loses ≥ 1 pp on ≥ 4/6): **FAIL — 2/6.** Reported as a bounded, sign-varying gap.

---

## 4 J1-E2b — four planners, one tolerance, leave-one-asset-out

Every planner sees only: the target asset's **measured rates** (encoding is cheap) and a **cross-asset prior** for
coverage loss (median over the other five assets of the same variant). Nothing sees the target's labels.

| planner | mean rate / oracle | tolerance violations | mean excess when violating |
|---|---|---|---|
| oracle (uses truth) | 1.000 | 0/6 | — |
| **CARP** = prior + tolerance | 0.911 (ε=1) / 1.006 (ε=2) / 1.057 (ε=5) | **3/6 / 3/6 / 2/6** | 0.89 / 1.43 / 1.23 pp |
| max-rate (coverage-blind) | 2.10 / 1.92 / 1.51 | **6/6** | **35.8 / 34.8 / 31.8 pp** |
| fixed 8-bit SH (published-format default) | 0.384 / 0.351 / 0.276 | 1/6 / 0/6 / 0/6 | 0.18 pp |
| prune-only under the same prior | — / 0.106 / 0.108 | — / 1/6 / 1/6 | 0.68 / 2.81 pp |

The four corners are all bad in different ways, and that is the point:

* **coverage-blind maximisation** buys 1.5–2.1× the rate and pays 32–36 points of coverage — this is what "compress
  as much as the PSNR allows" does;
* **the published-format default** (8-bit SH, geometry untouched) is safe and gives up **62–72 %** of the achievable
  rate;
* **pruning under the same prior** cannot even be formulated at ε = 1 (no admissible point) and reaches only ~0.11×
  the oracle rate when it can be;
* **the prior-only planner** is close in rate (0.91–1.06×) but **violates the tolerance on half the assets** — so a
  cross-asset prior is not a certificate.

**Verdict J1-C3** (predicted: a prior-only planner stays within 10 % of oracle rate on ≥ 4/6 assets): **PASS (0.91–1.06×)**.
**J1-C4** (predicted: it never violates ε): **FAIL — 2–3 of 6.** This failure is the motivation for J2 and, in the
paper, for making the audit part of the method rather than a validation afterthought.

---

## 5 J2 — the decision rule that never false-accepts

56 cells, truth = full held-out coverage loss, audit = re-render on the shipped calibration views and count residuals
under the shipped quantile. "False accept" = shipped with a tolerance the asset does not meet.

| ε (pp) | prior rule: accuracy | prior: false accepts | **audit rule: accuracy** | **audit: false accepts** |
|---|---|---|---|---|
| 0.5 | 0.946 | 0/56 | **1.000** | **0/56** |
| 1.0 | 0.857 | **4/56** | **1.000** | **0/56** |
| 2.0 | 0.964 | 2/56 | **1.000** | **0/56** |
| 5.0 | 0.929 | 3/56 | **1.000** | **0/56** |

With a safety margin δ subtracted from the tolerance, the audit keeps zero false accepts at δ = 0 for every ε; the
margin table is in `j2_audit_decision.md`.

**Honest caveat, and it belongs in the paper**: the decision task on this grid is *nearly* separable — geometric
edits lose **2.06–27.70** points while appearance/precision edits lose **−0.37 to +3.55** (negative = coverage
gained), so the two families overlap only in the 2–3.6 point band, and 32 of the 56 cells are non-geometric. The
1.000 accuracy therefore mainly restates §2; the number that carries the audit's real precision is the **regression
error**, MAE 2.0 points (no-op floor 1.8), and the decision table's contribution is the *contrast with the prior*,
which false-accepts cells drawn from that overlap band.

**Verdict J2-C1** (predicted: the audit false-accepts on ≤ 1 of 56 cells at every ε): **PASS 0/56.**
**J2-C2** (predicted: the prior false-accepts on ≥ 2 cells at some ε): **PASS (4/56 at ε = 1 pp).**

---

## 6 J1-E3 — a decibel budget is not a coverage budget

Coverage points per decibel, per asset, over the quantisation family:

| asset | pairs | pp per dB (median) | min | max |
|---|---|---|---|---|
| bicycle | 12 | 3.86 | 1.68 | 35.27 |
| bicycle_i7k | 9 | 2.01 | 1.13 | 11.26 |
| flowers | 8 | 3.02 | 1.61 | 9.90 |
| flowers_i7k | 5 | 0.91 | 0.81 | 1.27 |
| stump | 9 | 3.77 | 2.59 | 37.90 |
| stump_i7k | 12 | 3.50 | 1.46 | 16.16 |

**0.91–3.86 pp per dB across assets: a 4.2× spread.** Any pipeline that enforces a fidelity budget ("stay within
0.5 dB") therefore enforces a coverage budget that varies by 4× between assets — which is why the planner has to
optimise the certified quantity directly instead of proxying it with dB.

---

## 7 What this round changes in the manuscript

| change | where | cost |
|---|---|---|
| New main table: rate–reliability frontier by action family (§2) | Results, first table after the method | free (J1) |
| New main table: matched-rate collision (§3) | Results | free (J1) |
| New main table: four planners × tolerance (§4) + decision rules (§5) | Method/Results | free (J1/J2) |
| `CARP` becomes the named algorithm; the audit becomes its acceptance test, not a post-hoc check | Method § | writing |
| The "prune vs quantise" claim is now stated as **an admissible-set statement**, not a preference | Abstract + contributions | writing |
| §6's 4.2× spread replaces the vague "fidelity and coverage disagree" | Results | free |
| The near-separability caveat is stated in §5 rather than left for a reviewer | Results | writing |

**Nothing in this round required a GPU, a new render, or a new download.** The next thing that would require compute
is a fourth cross-paper scene (HAC/PCGS checkpoints for `flowers`/`treehill`), which is listed in the JVCIR plan as
optional and is *not* needed for the claims above.

---

## 8 Reproduce

```bash
python experiments/j1_reliability.py     # -> artifacts/a4/j1_reliability.{json,md}
python experiments/j2_audit_decision.py  # -> artifacts/a4/j2_audit_decision.{json,md}
```

Both read only files already in the repository; both print their own verdict lines. Wall clock: < 2 s each.
