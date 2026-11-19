# M17 — the number we can report at HAC's operating point

Round 13, 2026-11-15.  One scene (bicycle), one node (A100-PCIE-40GB, 2.4 h, ¥6.7).  Verdict:
**`representation_bound_confirmed`** — our pipeline cannot reach HAC's quality at HAC's size, and the
reason is now measured in two independent terms rather than asserted.

## Why this round existed

M16 lost 4.97 dB to HAC on bicycle at HAC's 27.54 MB, but it had measured exactly one pruning
setting: keep 20 %, 1500 finetune steps.  That confounded two things — how good our codec is per
byte, and how good a pruned model is at that primitive count.  M17 held the codec fixed (the M16
grid, unchanged) and moved pruning to settings a project would actually ship, with a finetune long
enough to be a comparison rather than a gesture.

Pre-registered in `METHOD_PLAN.md` at 06:50, before any data: K1 keep .50 / lr 1.0, K2 keep .35 /
lr 1.0, K3 keep .50 / lr 0.3, all 8000 steps, criterion C5 = best row at ≤ 27.54 MB reaches
24.50 dB (HAC 25.05 minus the 0.55 dB protocol bias C1 measured on this same scene).

## Two configurations were lost, and why

K1 and K2 (lr_scale 1.0) both diverged to NaN, caught by the finite guard at step ~3400 with
`psnr=1.33`; neither wrote a PLY.  K3 survived to step 5600 and then oscillated
(`psnr 22.45 → 4.71` within 200 steps).  The cause was a trainer defect, not a hyper-parameter
choice: **only `means` decayed its learning rate**.  Scales (5e-3), opacity (5e-2) and SH (2.5e-3)
held their initial rates for all 8000 steps, which a 1500-step run hides and an 8000-step run does
not.  3DGS decays *every* group to 1 % of its initial rate (`get_expon_lr_func`); this loop applied
that schedule to means alone.

Fixed before the reported runs (`research/code/scripts/train_gs.py`):

* `lr_init` is snapshotted per group and every group is decayed as `lr_init * lr_final_frac ** frac`
  (`--lr_final_frac`, default 0.01, i.e. 3DGS's 1 % floor);
* `--grad_clip` (default 1.0 in this round's runner) clips the global gradient norm before the step;
* a non-finite *loss* now drops that step instead of writing NaN into every parameter.

The reported runs are all on that recipe, so the two keep fractions are comparable.  The lost
configurations are recorded here rather than deleted: lr_scale 1.0 is not viable at 3 M primitives
for 8000 steps, and that is a fact about the trainer, not about compression.

## Measured

| configuration | primitives | clean PSNR | vs base | ft gain | cheapest row | best ≤ 27.54 MB |
|---|---|---|---|---|---|---|
| base (mirror 30 k) | 6,131,954 | 24.52 | — | — | `vq12_c8_o8` 72.2 MB (20.0×) | *none* |
| keep .50, no ft | 3,065,977 | 19.78 | −4.75 | — | 36.5 MB (12.5×) | *none* |
| keep .50, ft 8 k | 3,065,977 | 22.67 | −1.85 | **+2.89** | 36.5 MB (12.5×) | *none* |
| keep .35, no ft | 2,146,184 | 16.88 | −7.65 | — | 25.6 MB (17.6×) | 16.93 dB |
| keep .35, ft 8 k | 2,146,184 | 21.81 | −2.71 | **+4.93** | 25.7 MB (17.6×) | **21.51 dB** |

Per-primitive cost of the cheapest coder (`vq12_c8_o8`) is **11.90 B after zstd-12 + Morton order**
(12.69 B before coding), which is what sets the whole geometry of this table: 27.54 MB / 11.90 B =
**2.31 M primitives**.

## The two-term gap

**1. Bytes.**  27.54 MB buys 2.31 M primitives at our cheapest 11.90 B/prim.  Keeping 3.07 M (the
50 % model) needs ≥ 36.5 MB — over budget by 33 % before any quality question is asked.  Storing
the *full* 6.13 M model inside 27.54 MB would need 4.49 B/prim; nothing in the family reaches it
(the cheapest measured row anywhere in M15–M17 is 7.97 B/prim of *geometry alone*, before colour).

**2. Fidelity.**  At the primitive count the budget allows, our best model is 21.81 dB clean — 2.71
dB below the base model — and 21.51 dB once coded.  So even if colour were free and coding were
lossless, a 2.2 M-primitive vanilla-3DGS model would still sit ~3.2 dB under HAC's 25.05.

Finetuning does real work and is measurable at fixed bytes: +2.89 dB at 50 % keep, +4.93 dB at 35 %
keep.  It recovers about half of what pruning removed (4.93 of 7.65).  But it recovers *along* the
rate-distortion curve, not above it: at 25.7 MB, the 35 % finetuned model reads 21.51 dB where HAC
reads 25.05 dB at 27.5 MB.

**The uncomfortable corollary.**  Our codec has no operating point at all at 48×: the cheapest way
to store the full model costs 72.2 MB (20×), and 48× would need 4.49 B/prim.  HAC reaches 48× only
because it never stores a per-Gaussian SH — colour comes from an MLP over a sparse anchor set.
This is not a bit-budget we can squeeze; it is a representation we do not have.

## What this changes

* The paper's competitive claim narrows to the near-lossless regime, where our measured shelf is
  5.2× at −0.09 pp and 9.4× at −0.26 pp on a checkpoint we did not train (M16), and where **no
  published method reports a number at all**.  That is a defensible, first-of-its-kind claim.
* Prune + finetune is now a working, measured tool (`prune_ply.py`, 8000-step recipe, +4.9 dB at
  35 % keep), but it is not a route to 45×.  Building that route means adopting a shared colour
  model — a different architecture, not a better codec.
* A 30 k-step finetune (rather than 8 k) would test whether the remaining 2.7 dB is budget or
  patience.  That is the single cheapest open question, and it is what M18 should answer before
  any architectural work.

## Reproduction

```
bash experiments/run_m17.sh deps data base      # ~20 min on a fresh node
bash experiments/run_m17.sh k3   # keep .50, lr .3, 8000 steps, grad_clip 1.0
bash experiments/run_m17.sh k2b  # keep .35, lr .3
bash experiments/m17_finish.sh  # bytes (one job at a time), merge
bash experiments/m17_pass2.sh   # dumps WITH `clean`, then rd json + report
python experiments/m17_report.py --rd m17_rd.json --bytes m17_bytes.json --out m17_report.md
```

Artifacts: `experiments/artifacts/a4/m17_{rd,bytes,report}.{json,md}`.
Timings on the A100: prune+archive+probe 2 min, 8000 finetune steps 20 min at 3.07 M primitives
(two runs in parallel), bytes 6–10 min per model, analysis 9 min.
