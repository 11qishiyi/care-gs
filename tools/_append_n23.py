import io

TEXT = """
---

## N23 The last SH representation we tried, and the budget identity behind the 12x shelf

**Date.** 2026-11-14, round 10.  **Status.** Negative, and it did not consume a node.

The SH axis had already given four shapes and none of them reached 12x at a near-lossless
guarantee (N18 single codebook, N19 two-stage residual, N20 per-primitive mode selection, N21
product quantisation).  The fifth candidate was prediction: sort the primitives along a Morton
curve, code the first one of every block absolutely and the rest as residuals against their
predecessor, so that a fixed bit budget buys a finer step because the residuals are smaller.

Measured on synthetic blocks with a realistic band spread (amplitude falling by 10x from the DC
term to the highest band), at 2 bits per coefficient:

    prediction error 7.79e-02   scalar error 6.03e-02   ratio 1.293

Prediction lost.  Two mechanisms, both structural rather than accidental:

1. **The scale is shared by 64 primitives.**  One block, one scale, means the step is set by the
   largest residual in the block, while the published scalar code re-derives a scale for every
   single primitive.  The scale granularity that prediction gives up is worth more than the
   dynamic range it saves.
2. **The error accumulates.**  Reconstruction is a running sum, so each quantised residual adds
   its own error to everything after it.  Over a block of 64 that drift is about two steps, which
   is the same size as the saving.

Closed-loop prediction (predicting from the reconstructed predecessor) removes the drift but
needs a sequential scan over 5M primitives; at block level it only removes the drift *within* a
block, which is exactly the amount the shared scale already lost.  Since the pilot loses at the
first gate, no node round was spent on it.  The module stays in the tree (`experiments/dpcm.py`)
with its self-test recording the measurement rather than asserting a victory.

**The budget identity that this made visible.**  `rate = 236 / bytes per primitive`, so 12x means
19.7 B/primitive.  The cheapest variant at or below 0.4 pp currently measures 25.4 B, of which
about 19 B is SH at 3 bits.  Geometry -- 11 scalars -- can be packed from 11.8 B to 6.1 B
(quaternion smallest-three 1.4 B, scales 5 bit 1.9 B, opacity 4 bit 0.5 B, cluster positions c=6
2.25 B), and zstd takes its usual quarter, so the frontier moves from 9.5x to about 11x and stops.
Two points pin it: SH at 3 bits costs 0.11-0.42 pp and at 2 bits costs 1.46-6.16 pp, with nothing
in between available on any representation we have tried; and geometry cannot go below 6 B without
losing the lossless part of the shelf.

Twelve times with a near-lossless guarantee is therefore not a coding problem.  It is a budget
identity, and chasing it further would have been chasing a number rather than a mechanism.  See
`experiments/FRONTIER_BOUND.md` for the arithmetic.

**What survives.**  Geometry packing is still worth doing -- it is the last lever and worth about
+1.3x on the near-lossless frontier -- and it is cheap.  The 12-20x region remains reachable, but
only at 1.5-7 pp of coverage loss, which is where the method's advantage over the published
formats lives anyway (2.9-20.9 pp at equal bytes from 5.5x up).

**Lesson.**  Before spending a round on "a better codec for property X", price the round with the
budget identity: what fraction of the byte budget does X occupy, and how much of that can be
removed before the loss becomes visible?  If the answer is "less than the gap", the round will
not move the frontier no matter how good the codec is.  N17 reached the same conclusion for the
number of SH bands, N20 for scheduling, and N23 for prediction -- three different codecs, one
shared reason.
"""

P = r"D:\3dsg_1\APPENDIX_negative_results.md"
s = io.open(P, encoding="utf-8").read()
assert "N23" not in s, "N23 already present"
if not s.endswith("\n"):
    s += "\n"
s += TEXT
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("appended N23;", len(s), "chars total")
