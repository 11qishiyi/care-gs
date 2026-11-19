# Rebuttal FAQ — the six objections this paper will get, answered with numbers

Internal document (not submitted). Each answer is one paragraph the author can paste, with the file and table that
backs it. Written 2026-11-18, after the competitor audit in `review/CARE_GS_GAP_2026-11-18.md`.

---

## Q1. "At 19–28 MB you are 3 dB behind HAC/PCGS. Why is this a contribution?"

Because the quantity is different, and the manuscript says so twice — Table 11 computes the gap rather than hiding
it, and §6 repeats it. Our claim is that a shipped coverage guarantee survives *attribute* rate reduction and does
not survive *geometric* reduction, and that the surviving loss is computable by the recipient. HAC and PCGS optimise
rate–distortion and report no guarantee at all, so there is no configuration of theirs that could answer this
question. The honest form of the comparison is the one in the paper: at their file size we lose 2.97 dB (HAC) and
3.62 dB (PCGS) on `bicycle`, and we lose because each primitive pays for its own SH coefficients while anchor-based
coders pay 3–6 B against a learned anchor (§5.9). A reader who wants the fidelity frontier should use their codecs;
a reader who must ship a guarantee cannot.

*Backing*: `tab_gap.tex`, `§5.9`, `§6`, `experiments/artifacts/a4/sota_table.md`.

## Q2. "The certificate is not new — QuantileGS (Nov 2026), VSCP (Sep 2026), AURA (Jul 2026)."

Correct, and §2.4 says so in a table. QuantileGS calibrates a per-pixel bound for a frozen model and *transports* it
through pruning (requiring the original model and its quantile fields); VSCP states the guarantee at the view level;
AURA exports a split-conformal pruning certificate through glTF/USD and extends it to a certified LoD ladder. None of
them measures what an ordinary rate–distortion codec does to the statement, and none measures an edit made by the
recipient after delivery. That is the empty slot we occupy: the certificate is our *object*, not our contribution.

*Backing*: `tab_claims` (Table 2), `§2.4`, `review/CARE_GS_GAP_2026-11-18.md` §3.

## Q3. "PLEDGE already inverts declared tolerances into a codec, with bounds shipped in the header."

PLEDGE bounds four attributes deterministically; a pixel's error is a nonlinear composite of those four after
rasterisation, alpha compositing and occlusion, so a per-attribute bound does not deliver a per-pixel statement and a
per-pixel coverage statement does not deliver a per-attribute bound. We do not construct a bound at all: we calibrate
coverage on held-out views and audit it afterwards. The two are complementary, and §2.4 states the difference in one
sentence each, because the objects are different, not the numbers.

*Backing*: `§2.4` paragraph on PLEDGE, `tab_claims`.

## Q4. "Only two scenes can be compared with published methods."

Yes, and the exclusion is mechanical: `bicycle` and `stump` are the two where our clean render reproduces the
published 3DGS number (−0.59 and −0.51 dB, carried as a stated 0.55 dB bias); the other six checkpoints are internal,
and `bonsai` is excluded from the audit grid because its archive pairs cameras and ground truth at 15.8 dB against
the released model's 32.1 dB. We would rather have two comparable scenes and a stated rule than eight incomparable
ones. The claims that do not depend on cross-paper comparison — the frontier (Table 3), the collision (Table 4), the
planner comparison (Table 5) and the decision table (Table 6) — are measured on six scene-checkpoints.

*Backing*: `§4.1`, `tab_frontier`, `tab_collision`, `tab_planners`, `tab_decision`.

## Q5. "Is a one-point coverage drop meaningful? Is any of this perceptible?"

We do not claim perceptual relevance, and the paper says so. ε is a *contract parameter* the issuer chooses, and the
result that matters is that the choice is decidable and that one decibel is worth 0.91–3.86 coverage points depending
on the asset (a 4.2× spread, §5.6) — so a fidelity budget is not a coverage budget. If a reviewer wants the
perceptual version of this question, the answer is a subjective study, which we list as future work (§6) and which
the compressed-3DGS perceptual literature has its own protocols for (GScomp-QA, 3DGS-VBench+).

*Backing*: `§5.6`, `tab_perceptual`, `§6`.

## Q6. "Per-pixel coverage is the wrong granularity — view-level is what users experience."

VSCP's own numbers are the reason this is a real objection (89.9 % marginal pixel coverage against 61.4 % view-event
coverage at a 90 % target), and §6 cites them. We stay per-pixel because the certificate names a per-pixel threshold,
because the planner's tolerance is defined on the same quantity the certificate states, and because a view-level
statement would need its own audit — which we have not measured. A view-level audit is the natural next experiment
and is listed in §6 rather than promised in §1.

*Backing*: `§2.2`, `§6`, `vscp` entry in `refs.bib`.

---

## If the reviewer asks something not on this list

The reflex that has worked all along: answer with a table, not a sentence. Every claim in this manuscript is
reproducible from `deposit_jvcir.zip` by `tools/jvcir_tables.py`, and `tools/verify_jvcir.py` fails if the number
in the prose and the number in the table disagree. If an objection cannot be answered with a number in the deposit,
the honest response is "that is a limitation we have not measured", and §6 is where it goes.
