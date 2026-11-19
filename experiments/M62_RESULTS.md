# M62 — same-model baselines: Fisher (our saliency) wins, but only +0.4 dB over the viewer default

**Round 52, node 2142164 (A100-PCIE-40GB, ¥2.80/h), 2026-11-17 19:45–…** Every cross-paper number this project owns
compares our post-hoc compression of a published checkpoint against HAC/PCGS numbers from models *they retrained*. This
round is the missing comparison: one checkpoint, one container spec, five pruning scores, equal bytes.

## Protocol

`tools/same_model_baselines.sh <scene> 0.5 fisher` — the published 30k checkpoint, pruned to 50 % by each score, then
encoded at `gp6-6-6_c8_sh3` (48-bit colour), archived and rendered at factor 1 on the same held-out views. Scores:
`opacity` (the viewer default, and LightGaussian's starting point), `volume` (`opacity·cbrt(sx·sy·sz)`, this project's
proxy before M47), `area` (`opacity·mean cross-section`), and `fisher` (accumulated squared gradients of
means/scales/opacity — the PUP-3DGS score, which is what M47's "saliency" is).

## bonsai (1,244,819 primitives)

| arm | primitives | file | PSNR | Δ vs control | B/prim |
|---|---|---|---|---|---|
| control | 1,244,819 | 15,297,685 B (15.30 MB) | **27.08** | — | 12.29 |
| fisher, 50 % | 622,410 | 8,072,984 B (8.07 MB) | **26.58** | **−0.50** | 12.97 |
| opacity, 50 % | 622,410 | 7,950,570 B (7.95 MB) | 26.15 | −0.93 | 12.77 |
| area, 50 % | 622,410 | 7,837,673 B (7.84 MB) | 24.92 | −2.16 | 12.59 |
| volume, 50 % | 622,410 | 7,837,731 B (7.84 MB) | 24.55 | −2.53 | 12.59 |

The control reproduces M51's 15,297,685 B / 27.08 dB to the byte and to the hundredth of a dB, so the container and the
probe are sound.

## What the table actually says

1. **The score ordering replicates M47/M48**: fisher > opacity > area > volume, and the spread is large (2.0 dB between
   the best and the worst at the same budget).
2. **Against `volume`** — the baseline every earlier round used — fisher gains **+2.03 dB** at +3 % bytes. That is the
   number the project has been quoting, and it stands.
3. **Against `opacity`** — a real, published baseline (and the one a practitioner would actually use) — the gain is only
   **+0.43 dB** (26.58 against 26.15 at +1.5 % bytes). Most of the "saliency wins" headline was beating a uniquely bad
   proxy, not beating the state of the practice.
4. **Pruning to half the bytes costs half a decibel** with the Fisher score. That is a competitive operating point in its
   own right, and it is the honest framing for the paper: *a Fisher-diagonal score plus this container keeps 26.58 dB at
   8 MB, where the viewer's own score keeps 26.15 dB and the volume proxy 24.55 dB.*

## Consequences for the paper

* The method claim must be **"we replicate and quantify the Fisher score in a compression pipeline"**, not "we invent a
  new pruning score" — the score is PUP-3DGS's, and `opacity` is nearly as good.
* The same-model table is the one reviewers can check; it needs bicycle (running) and ideally stump before submission.

## Reproduction

```bash
bash tools/same_model_baselines.sh bonsai 0.5 fisher
```

Files: `tools/same_model_baselines.sh`, `experiments/artifacts/a4/smb_bonsai/` (rows, stage log),
`experiments/artifacts/a4/smb_bonsai_bundle.tgz`.

## bicycle (6,131,954 primitives)

| arm | primitives | file | PSNR | Δ vs control | B/prim |
|---|---|---|---|---|---|
| control | 6,131,954 | 76,598,203 B (76.60 MB) | **24.06** | — | 12.49 |
| fisher, 50 % | 3,065,977 | 40,166,441 B (40.17 MB) | **23.53** | **−0.53** | 13.10 |
| opacity, 50 % | 3,065,977 | 39,501,375 B (39.50 MB) | 22.78 | −1.28 | 12.88 |
| area, 50 % | 3,065,977 | 38,999,009 B (39.00 MB) | 22.14 | −1.92 | 12.72 |
| volume, 50 % | 3,065,977 | 38,756,326 B (38.76 MB) | 19.67 | −4.39 | 12.64 |

## The two scenes together

| score | bonsai Δ | bicycle Δ | gain over the next-best score |
|---|---|---|---|
| fisher | −0.50 | −0.53 | — |
| opacity | −0.93 | −1.28 | **+0.43 / +0.75** |
| area | −2.16 | −1.92 | +1.66 / +1.39 |
| volume | −2.53 | −4.39 | +2.03 / +3.86 |

The ordering is identical on both scenes, the Fisher loss is a stable **−0.5 dB for half the bytes**, and the two numbers
that matter are: **+2.0…+3.9 dB over `volume`** (what the project used to quote) and **+0.43…+0.75 dB over `opacity`**
(what a practitioner would actually use). bicycle makes the point sharply: the volume proxy costs 4.4 dB there, so a
paper that only ever compared against it was flattering itself by 4 dB.

## LPIPS column (round 55)

bicycle, keep 50 %, 48-bit colour, `--fidelity --lpips-net vgg`:

| arm | file | PSNR | SSIM | LPIPS |
|---|---|---|---|---|
| control | 76.60 MB | 24.06 | 0.7393 | **0.2813** |
| fisher | 40.17 MB | 23.52 | 0.7269 | **0.2916** |
| opacity | 39.50 MB | 22.78 | 0.7049 | 0.3034 |
| area | 39.00 MB | 22.14 | 0.6662 | 0.3264 |
| volume | 38.76 MB | 19.67 | 0.5782 | 0.3777 |

Half the bytes costs +0.010 LPIPS with the Fisher score and +0.096 with the volume proxy; the ordering matches PSNR and
SSIM, so the score comparison does not depend on the metric.
