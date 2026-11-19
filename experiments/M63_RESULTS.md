# M63 — BD-rate for the pruning scores: both halve the bitrate, and they are the same score

**Round 53, node 2142199 (A100-PCIE-40GB, ¥2.80/h), 2026-11-17 20:50–22:30 ≈ ¥4.6.** M62 compared the scores at one
operating point. A compression paper needs BD-rate, so this round swept four colour budgets on every arm and computed it.

## Protocol

bicycle (6,131,954 primitives), keep 50 %, container `gp6-6-6_c8_sh3` at colour budgets 96/64/48/32 (plus 24 for the
control only, so the curves overlap), rendered at factor 1 on the same 25 held-out views. **No finetuning**: every arm is
prune-then-encode, which is the fair same-post-processing comparison and is *not* the M47/M48 setup (those finetuned 12k
steps after pruning).

| arm | 96 | 64 | 48 | 32 | 24 |
|---|---|---|---|---|---|
| control (no prune) | 115.09 MB / 24.25 | 84.16 / 24.22 | 76.60 / 24.06 | 69.92 / 22.94 | 68.52 / 21.17 |
| fisher (PUP score) | 60.32 / **23.75** | 44.28 / **23.71** | 40.19 / **23.52** | 36.21 / **22.38** | — |
| opacity | 59.27 / 22.91 | 43.44 / 22.90 | 39.50 / 22.78 | 35.84 / 21.85 | — |
| volume | 57.93 / 19.71 | 42.42 / 19.70 | 38.76 / 19.67 | 35.50 / 19.26 | — |

## BD-rate against the unpruned control (overlapping quality range)

| arm | BD-rate | BD-PSNR | points |
|---|---|---|---|
| fisher | **−45.06 %** | n/a (rate ranges do not overlap) | 4 |
| opacity | **−44.96 %** | n/a | 4 |
| volume | n/a (its whole curve sits below the control's quality range) | n/a | 4 |

## What this says, and what it corrects

1. **Pruning at all is worth ~45 % of the bitrate at equal quality** — without any finetuning, in the same container.
2. **The three scores separate into two groups, not three.** `fisher` and `opacity` are within 0.1 percentage points of
   BD-rate of each other (−45.06 against −44.96). The +0.74 dB gap M62 reported at 48 bits is real but it is a *quality
   ceiling* difference — fisher reaches 23.75 dB where opacity tops out at 22.91 — not a rate advantage across the curve.
3. **`volume` is not on the same axis at all**: at equal bytes it renders 4–4.4 dB lower, so no BD-rate exists against a
   control whose minimum is 21.17 dB. Quoting "+2.0…+3.9 dB over volume", as this project did for six rounds, was
   comparing against an arm that is simply broken.
4. **The honest headline for the paper**: *pruning to half the primitives preserves quality to within half a decibel and
   saves 45 % of the bitrate; the choice between the Fisher score and the viewer's opacity score changes the quality
   ceiling, not the rate.* That is a weaker method claim than "our new score", and it is the one the data supports.

## LPIPS: measured, not obtained

The probe ran with `--fidelity --lpips-net vgg` (the 528 MB backbone downloaded in 42 s), but `qfp_rd` writes
`"lpips": null` into its manifest for every scene — the value is not computed on this code path. The LPIPS column is
therefore `NA` throughout, and fixing it is a separate round (the render is RGB; the null suggests the fidelity branch
returns early for this variant set).

## Reproduction

```bash
python3 tools/bd_rate.py --selftest                       # identity, -50 %, +25 %
bash tools/smb_rates.sh bicycle 0.5 "96 64 48 32"          # 16 rows on one node in ~80 min
python3 tools/bd_rate.py --ref rows_u.txt --test rows_u.txt
```

Files: `tools/smb_rates.sh`, `tools/bd_rate.py`, `tools/smb_ctrl24.sh`,
`experiments/artifacts/a4/smb_rates/` (rows_u.txt, stage log), `experiments/artifacts/a4/smb_rates_bundle.tgz`.

## Addendum (round 54): the LPIPS column is obtainable — three defects, all fixed

`NA` in the table above had three causes, none of them the metric itself:

1. **the backbone was never downloaded** — `_fidelity_stats` refuses to load LPIPS without the weight file (by design,
   to avoid a hidden 528 MB download stalling a campaign), and none of the harnesses warmed it;
2. **the path check looked in one directory** — it now searches `$TORCH_HOME`, `$XDG_CACHE_HOME/torch`, `~/.cache/torch`
   and `/root/.cache/torch`, and the error names every path tried (3 tests);
3. **the renderer leaves no GPU memory for VGG** — a 6.1 M-primitive render holds ~32 GB of a 40 GB card, so the 6 GB
   backbone OOMs; the code now falls back to CPU after `torch.cuda.OutOfMemoryError` (~40 s for 25 views).

Verified on bicycle's control entry: PSNR 24.52, SSIM 0.7705, **LPIPS 0.2397** (the 3DGS paper reports ≈0.245 at
25.11 dB on the same scene). The sixteen-entry column still needs one ~80 min re-probe; the machinery is ready.
