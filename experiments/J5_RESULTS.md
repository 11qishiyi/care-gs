# J5 results — the qualitative grid (2026-11-18)

**Round J5. MatPool instance 2142711 (A40, 1 区, ¥2.85/h, image `Pytorch 2.8.0` 634333), rented 14:44, released
17:00 on explicit confirmation (`matcli node release --id 2142711 --confirm-release`).** Criteria were pre-registered in [`J5_PLAN.md`](J5_PLAN.md) before the renders existed; two hold, one
does not, and one scene had to be dropped because its checkpoint is corrupt. Both failures are recorded here and are
visible in the manuscript.

## What was produced

| item | value |
|---|---|
| scene | `bicycle` only (see "the stump checkpoint is corrupt" below) |
| view | held-out view **15**, chosen by the pre-registered rule (**median clean PSNR** over the 13 deployment views, rank 4/13) |
| magnification | GT window at **(840, 360)**, $200\times200$, chosen by **argmax ground-truth gradient energy** on a 20-px grid |
| arms | `clean` 1.00× · `gp6-6-6_c8_sh6` 5.07× · `gp6-6-6_c8_sh3` 8.25× · `p50` (Fisher 50 %) 2.00× |
| PSNR at that view | **27.03 / 26.84 / 26.59 / 26.11 dB** |
| SSIM at that view | 0.8129 / 0.8026 / 0.7914 / 0.7758 |
| figure | `figures_j/fig6_qualitative.pdf` (+ 300 dpi PNG), `tools/jvcir_fig_qual.py` |
| artifact | `experiments/artifacts/a4/j5_fig_qual.json` (crop box, σ, per-arm rate/PSNR/SSIM) |
| raw pull | `_pull_j5/` (patches, thumbnail, `j5_pack.json`, logs) |

## Criteria

| | criterion | outcome |
|---|---|---|
| **J5-C1** | each arm's view PSNR within 1.5 dB of the matching Table 9 scene mean | **FAIL** — clean is 27.03 dB here against 24.65 dB in Table 9 (Δ 2.38 dB) |
| **J5-C2** | in the magnification, the 8.25× arm beats the 2.00× prune arm | **PASS** — 26.59 vs 26.11 dB |
| **J5-C3** | the magnification is not sky/flat (GT σ ≥ 0.02) | **PASS** — σ = 0.164 |

**C1 diagnosis** (this is the criterion doing its job, not a bug): Table 9's `bicycle` rows were rendered from the
checkpoint cached at `/mnt/m35cache` in the J4 round; this round's checkpoint came from the public mirror
(`dylanebert/3dgs`, `iteration_30000`), which renders sharper against the `images_4` ground truth — every arm is
2–2.5 dB above the table, in the same order. Two consequences: (i) the labels in Fig. 6 are **one view of a different
checkpoint** and the manuscript says so in §5.8; (ii) only within-figure comparisons are claimed. Folding the figure
into Table 9's accounting would need the original checkpoint, which no longer exists.

## The stump checkpoint is corrupt

The mirror's `stump/point_cloud/iteration_30000/point_cloud.ply` (1,230,527,188 B, byte count verified after a
48-chunk assembly) loads with **9 non-finite scales**, `|means|` up to $7.4\times10^{31}$ and `|sh0|` up to
$3.0\times10^{32}$ (probe output below). The clean render still looks right, but every quantisation arm collapses to
10.79 dB / SSIM 0.0014, because the min–max grids are fitted on those values. J4's numbers for `stump` came from a
different copy (`/mnt/m35cache`), so they are unaffected.

```
bicycle n 6131954  ...  nonfinite 0, max|means| 96.9
stump   n 4961797  means  max 7.397609067642071e+31
                   scales nonfinite 9, max inf
                   sh0    max 3.035682754035806e+32
                   shN    max 1.1988696458192518e+33
```

Rule applied (mechanical, so the exclusion is not a choice): **an arm whose PSNR at the chosen view is more than 5 dB
below the clean render is degenerate; its scene is dropped from the figure and reported here.** `bicycle`'s arms are
0.2–0.9 dB below clean; `stump`'s quantised arms are 17.8 dB below.

## One addition that was not pre-registered

The arms turned out to be visually close at ×1 (that is the paper's point), so the figure carries a second row:
each render differenced against the **clean** render, amplified ×8. This isolates what the *action* did instead of
showing how far the model is from ground truth. It is an addition, not a substitution, and it is declared here
because it was decided after seeing the first row.

## Cost (and why it was 2.5× the estimate)

| stage | wall clock | note |
|---|---|---|
| rent → image ready | 14:44–14:47 | image not cached |
| pip + gsplat 1.5.3 | 14:47–14:48 | `packaging` already satisfied this time |
| images (194 + 125) | 14:50–15:21 | mirror throttles a single connection to ~30 KB/s; 32-way pooling gave ~1.4 MB/s |
| PLYs (1.52 GB + 1.23 GB) | 15:10–16:12 | 24–48 HTTP-range chunks; one resume bug and one stale-part bug had to be fixed mid-flight |
| archives + render + pack | 16:12–16:25 | 2 scenes × 4 arms at 1236×822 |
| pull + verify | 16:25–16:45 | 6 patches + thumbnail over `matcli node exec` |
| **total** | **~136 min** (14:44–17:00) | **≈ ¥6.5** (estimate was ¥1.7–2.2) |

The overrun is entirely download: the mirror served single streams at 30 KB/s and only scaled with connection
counting. Two fixes are now in the repo so the next round does not rediscover them: `j5_fetch_all.sh` (chunked,
size-verified) and `j5_ply_resume.sh` (per-chunk resume, exact-length check — an oversized stale part must be
deleted, not kept).

## What the figure says (and what it does not)

It says: at 8.25× the container's error is spread thinly over texture, while a prune that saves a quarter as much
concentrates its error on edges — the two families are not two intensities of one knob, which is §5.2's claim in a
currency a reader can check by eye.

It does not say: that this view is representative of the scene mean (C1), or that `stump` behaves the same way (its
checkpoint is corrupt), or that a subjective viewer would prefer either arm (no subjective study).

## Reproduce

```bash
# node (A40, image Pytorch 2.8.0)
bash experiments/j5_fix_images2.sh                 # images from the COLMAP name list
bash experiments/j5_ply_resume.sh bicycle 1520726124
bash experiments/j5_build.sh                       # archives -> j5_render.py -> j5_pack.py
# local
pwsh -File tools/pull_j5.ps1 -NodeId <id>
python tools/jvcir_fig_qual.py                     # fig6 + artifacts/a4/j5_fig_qual.json
python tools/verify_jvcir.py                       # gate, including the Fig. 6 label check
```
