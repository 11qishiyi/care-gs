# J7 results — a coverage-aware pruning score loses to opacity, badly (2026-11-20)

**Round J7. MatPool instance 2143958 (V100-16GB, ¥1.85/h), rented 00:46, released after the pull.** Criteria were
pre-registered in [`J7_PLAN.md`](J7_PLAN.md) before the render; the verdict is the script's, not a reading of it.

## The question

The paper's headline is that the **action family**, not the compression strength, decides whether a shipped coverage
statement survives: inside a one-point tolerance quantisation reaches 8.97–15.78×, while pruning has no admissible
point at all. But the pruning arms rank primitives by **opacity** (`prune50`) or by a Fisher/PUP diagonal (`pup30`) —
both coverage-blind. A reviewer will ask: *would a score designed for coverage do better?*

## The answer

No. It does much worse.

| scene | keep | loss, opacity (pp) | loss, coverage-aware (pp) | ratio |
|---|---|---|---|---|
| bicycle | 0.9 | −0.00 | 2.84 | — |
| bicycle | 0.7 | 0.17 | 10.46 | **61.5×** |
| bicycle | 0.5 | 3.95 | 21.58 | **5.5×** |
| stump | 0.9 | −0.00 | 0.64 | — |
| stump | 0.7 | 0.29 | 3.77 | **13.0×** |
| stump | 0.5 | 7.28 | 10.82 | **1.5×** |

Criterion: the coverage-aware arm had to keep the loss at ≤70% of opacity's on ≥4 of 6 cells. **0 of 6**; the median
ratio is **13×** *in the wrong direction*. Verdict: **the score is not the reason; the asymmetry is a property of the
action family.**

## Why it went wrong (the useful part)

The score was `alpha_j · footprint_j · (1 − |e(p_j) − q|/q)+`: keep the primitives whose pixels sit *near* the
threshold, because those are where the error can cross `q`. That intuition is backwards, and the data says so:

1. **Proximity is not sensitivity.** A pixel far below `q` is far below it because the model renders it *well*; deleting
   the primitive that carries it can push its error across `q`. The score treats "far from the threshold" as
   "free to delete", which is exactly wrong for well-modelled pixels.
2. **The score ignores the change.** What matters is `|render_after − render_before|`, not the current residual. Opacity
   is a crude but *direct* proxy for that change (a low-alpha primitive contributes little to any pixel); my score
   weighted it by two quantities that do not track the change at all.
3. The self-test could not catch this: it verified the *properties* of the score (monotone in α, quadratic in scale,
   threshold-aware, ranking differs from opacity by 47%) but not that those properties point the right way. A property
   test is not a validity test.

## What it buys the paper

One sentence in §5.2, and a stronger claim:

> We also tried a pruning score built to protect the shipped quantile — rank primitives by opacity, footprint and
> proximity of their pixels to `q`. It is **worse** than plain opacity at every matched keep rate (median 13× the
> coverage loss; 0 of 6 cells improve), which is what one should expect: what a deletion costs is the *change* it
> induces, not the residual it finds.

That converts "your pruning baseline is a straw man" into "we built the non-straw-man version and it is worse".

## Cost

| item | value |
|---|---|
| instance | 2143958, V100-16GB, ¥1.85/h |
| wall clock | 00:46 → 01:26 (40 min) ≈ **¥1.2** |
| data | bicycle + stump PLY (1.52 + 1.23 GB), images 189/194 + 125/125, both archives built |
| artifacts | `_pull_j7/j7.json`, `experiments/artifacts/a4/j7_report.json`, `tab_prune_cov.tex` |

## Reproduce

```bash
# node, with the CAS path (the mirror's redirect 502s from MatPool but the signed URL serves 206)
bash experiments/j7_all.sh            # gate -> deps -> data -> archives -> j7_run.py
pwsh -File tools/pull_j6.ps1 -NodeId <id> -Remote /root/res/j7/j7.json -Local _pull_j7/j7.json
python experiments/j7_report.py       # the verdict + tab_prune_cov.tex
```
