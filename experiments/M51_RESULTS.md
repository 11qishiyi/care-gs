# M51 — the "free" opacity byte is not free at the top of the curve

**Round 34, node 2141711 (A100-PCIE-40GB, ¥2.80/h), 2026-11-17 11:47–12:52 ≈ ¥3.0.** M50 found that dropping opacity
from 6 to 4 bits saved 2.37 % of a *pruned* mid-rate container for +0.01 dB and proposed it for the headline
near-lossless row. This round measured that row on all three published models. The byte is not free: it costs
**0.11 dB on every scene**, and it is nonetheless the cheapest byte available at that end of the curve.

## Result (three untouched published models, shipping spec `gp6-6-{6,4}_c8_sh3`, 48-bit colour)

| scene | control | opacity 4-bit | Δ bytes | Δ PSNR | Δ SSIM | ratio (control → 4-bit) |
|---|---|---|---|---|---|---|
| bicycle (6,131,954 prim) | 76,598,203 B / **24.06** / 0.73932 | 74,802,867 B / **23.95** / 0.73303 | **−2.35 %** | **−0.11** | −0.0063 | 18.90× → 19.35× |
| stump (4,961,797) | 62,649,653 B / **25.52** / 0.74324 | 61,191,922 B / **25.41** / 0.73685 | **−2.33 %** | **−0.11** | −0.0064 | 18.71× → 19.14× |
| bonsai (1,244,819) | 15,297,685 B / **27.08** / 0.88680 | 14,927,795 B / **26.97** / 0.88237 | **−2.42 %** | **−0.11** | −0.0044 | 19.20× → 19.68× |

Payload conventions as in the series: 1447.1 / 1170.98 / 293.78 MB. The control rows reproduce the shelf to the byte
(76,598,203 B is M44's md5-identical container; 25.52 and 27.08 are the published clean-container numbers).

## Verdict — `not_free_but_cheapest`

* **J1 FAILS.** The criterion asked for ≤ 0.05 dB loss; all three scenes lose **0.11 dB**. The byte is not free.
* **J2 FAILS as written.** The ratio does improve (+0.45× / +0.44× / +0.48×), but not *at equal PSNR* — it is bought
  with 0.11 dB. The row stays on 6-bit opacity unless the paper decides to trade.
* **J3 PASSES.** Decode wall clock within 1.2 % (bicycle 15.95 → 15.76 s, stump 12.85 → 12.72, bonsai 3.25 → 3.22) and
  peak RSS within 0.02 % (4.27 / 3.49 / 0.95 GB): the stream is narrower, not differently shaped.
* **J4 PASSES** for the byte model (881 cases, 0 mismatches; `m19_codec --selftest` ALL PASS on the round's node).
  The "header still declares 6-bit opacity" clause was **not** checked and is recorded as unverified.

## Why M50 saw "free" and this round sees 0.11 dB

On the 25 %-pruned model the opacity field is nearly constant — pruning had already removed the faint splats whose
opacity spans the range — so the 6-bit quantiser was spending bits on values that almost did not vary, and widening it
to 4 bits changed nothing. The unpruned models keep the whole opacity distribution, and the top two bits of it matter:
the loss is the same 0.11 dB on all three scenes, which is what a saturation effect looks like, not noise.

## Is 0.11 dB a good price for 2.35 %?

At this end of the curve, yes — it is the cheapest byte the container has:

| lever (bicycle, this end) | Δ bytes | Δ dB | dB per 1 % |
|---|---|---|---|
| **opacity 6 → 4 bits** | **−2.35 %** | **−0.11** | **0.047** |
| colour 48 → 40 bits (M22, 98.53 → 95.22 MB) | −3.36 % | −0.45 | 0.134 |
| colour 48 → 32 bits (M22, 98.53 → 92.10 MB) | −6.53 % | −1.14 | 0.175 |

So the honest statement is not "free" but "the best available exchange at the near-lossless end, 3× cheaper per byte
than cutting the colour block". Whether to spend it is an editorial decision about the headline row, not a technical
one: 18.90× at −0.46 dB or 19.35× at −0.57 dB.

## Corrections propagated

`M50_RESULTS.md` said the change was "worth ≈ +0.47× on the near-lossless shelf" and implied it came for nothing; a
note there now points at this round. The `M51 spec` in `METHOD_PLAN.md` named the wrong colour budget
(`c9_sh3:16:165`); it was corrected at 11:55, before any measurement, and the correction is recorded in the spec
itself.

## Reproduction

```bash
bash tools/m51_go.sh        # deps, three COLMAP scenes, six containers, first-pass renders
bash tools/m51_fix.sh       # the node's gsplat is older than the renderer API; pin 1.5.3
bash tools/m51_pass2.sh     # re-render + decode timing; writes rows_final.txt
```

The first pass is kept in the artifacts because it is what caught two environment defects: the image ships **no
gsplat** (the renderer needs `gsplat.rasterization`, added in 1.5) and **no `/usr/bin/time`** (decode timing uses
`tools/m51_decode.py` and `resource.getrusage(RUSAGE_CHILDREN)` instead). Neither is a property of the codec, and both
would have silently produced "NA" rows.

Files: `tools/m51_{go,fix,pass2}.sh`, `tools/m51_decode.py`, `experiments/artifacts/a4/m51/` (stage logs, six render
logs, six decode logs, `rows.txt` and `rows_final.txt`), `experiments/artifacts/a4/m51_bundle.tgz`.

## Cost

Node 2141711: 1.08 h ≈ **¥3.0**, of which ~28 min is the three-scene COLMAP fetch (a fresh node pays it every round),
~20 min the six encodes, ~5 min renders, ~1 min decodes. Released immediately after the last row.
