import io

TEXT = """
---

## M14 pilot and the 12x budget identity (round 10, 2026-11-14 19:50)

**M14 = block-prediction (DPCM) coding of the SH block.**  Hypothesis: residuals against a Morton
predecessor have a smaller dynamic range, so a fixed bit budget buys a finer step and 12x becomes
reachable at 3 bits.  **Pilot gate, run locally before any node time:** at 2 bits on synthetic
blocks with a 10x band spread, prediction measures 7.79e-2 against 6.03e-2 for the published
scalar code -- ratio 1.293, prediction loses.  Mechanisms: the block shares one scale while the
scalar code re-adapts per primitive, and the running-sum reconstruction accumulates the residual
error.  Closed-loop prediction would fix the drift but needs a sequential scan over 5M primitives.
**No node round was spent; recorded as N23.**

**Budget identity (the reason to stop aiming at 12x).**  `rate = 236 / B_per_prim`, so 12x needs
19.7 B.  The cheapest near-lossless variant measures 25.4 B (about 19 B of it SH at 3 bits).
Geometry packing -- quaternion smallest-three 1.4 B, log-scales 5 bit 1.9 B, opacity 4 bit 0.5 B,
cluster positions c=6 2.25 B, header 0.09 B = 6.1 B against 11.8 B today -- plus the usual zstd
quarter puts the near-lossless frontier at **about 11x, not 12x**.  Pinned by two measured facts:
SH at 3 bits costs 0.11-0.42 pp and at 2 bits 1.46-6.16 pp, with no representation in between
(N18-N21, N23 all land on one side or the other); and geometry cannot go below ~6 B without
giving up the lossless shelf.  Full arithmetic in `experiments/FRONTIER_BOUND.md`.

**M15 (next, still worth a round): geometry packing.**  The last lever, worth about +1.3x on the
near-lossless frontier (9.5x -> 11x) at unchanged coverage.  Gated by the same rule as M14: the
quaternion part must be verified locally first (smallest-three reconstruction error at 3 bit per
component, against the 8-bit uniform grid that M2 measured as free), and only then does it earn a
node round.  Judgement, pre-registered before data: at a common budget, the packed variant must
hold loss within 0.5 pp of the unpacked variant at the same quality and sit at least 1.0x higher
in ratio, on at least 6 of 8 assets.
"""

P = r"D:\3dsg_1\experiments\METHOD_PLAN.md"
s = io.open(P, encoding="utf-8").read()
assert "M14 pilot and the 12x budget identity" not in s
if not s.endswith("\n"):
    s += "\n"
s += TEXT
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("appended; METHOD_PLAN.md now", s.count("\n") + 1, "lines")
