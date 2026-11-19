# Cover letter — JVCIR submission

**Manuscript:** CARE-GS: coverage-aware rate reduction for 3D Gaussian Splatting assets
**Author:** Tianji Su, Ningbo University
**Type:** Regular paper
**Date:** 2026-11-18

---

Dear Editor,

Please consider the enclosed manuscript for publication in the *Journal of Visual Communication and Image
Representation* as a regular paper.

**What the paper does.** A 3D Gaussian Splatting asset is now a file that changes hands: it is trained once, shipped,
and then re-compressed by whoever receives it. The sender and the receiver share only fidelity numbers — PSNR, SSIM,
LPIPS — and those numbers do not say whether the per-pixel quality guarantee that travelled with the asset still
holds. The manuscript measures what a recipient's edit does to that guarantee, and turns the measurement into a
method: a container that makes attribute quantisation worth spending (17.35× at −0.04 dB), a coverage-aware planner
that chooses the operating point against a stated tolerance, and an audit that the recipient can run on the
calibration views the asset already carries (56/56 decisions, no false acceptance, no new labels).

**Where it sits in the journal.** The work is visual data reduction and compression for a 3D representation, and it is
measured in the vocabulary this journal's compression papers use: a bitstream composition table, BD-rate for the pruning arms (−45.06 %), and a decode-time and memory budget. The journal's 3DGS line has so far
addressed how such an asset is *trained and optimised*; this manuscript addresses what happens to it after it leaves
the training machine, and the manuscript states that relationship explicitly, with three of the journal's recent 3DGS
papers cited in §2.1.

The comparison literature for this particular step lives outside the venue (anchor-based and progressively quantised
3DGS coders), so rather than leave that comparison to the reader, the gap table computes it from the published numbers and
reports where this container loses: across four published coders at their own operating points the gap is
0.96–3.62 dB on *bicycle* (2.97 dB behind HAC at 25.67 MB, 3.62 dB behind PCGS at 18.40 MB) and 6.25 dB behind HAC on
*stump*. The claim is accordingly narrow —
not that the rate–distortion frontier is beaten, but that rate reduction can be certified, and what certification
costs. The Limitations section states the remaining boundaries in the same terms (no subjective study, a per-pixel
rather than view-level guarantee, and no closure of the fidelity gap).

**What is new, in three sentences.**
1. The damage an edit does to a shipped coverage certificate is decided by the *action family*, not by its strength:
   inside a one-point tolerance, quantisation reaches 8.97–15.78× on six scene-checkpoints while pruning has no
   admissible configuration at all.
2. A shared rank-16 colour basis, smallest-three quaternions and per-stream alphabets take a 1447 MB asset to
   83.41 MB at 24.08 dB, with every step attributed in an ablation table.
3. The planner is admissible only because the audit exists: a leave-one-asset-out prior reaches 0.91–1.06× the oracle
   rate but violates the tolerance on two to three of six assets, whereas the audit on the shipped calibration views
   decides all 56 measured cells with zero false accepts.

**Data and code.** Under the journal's Option C, the code, the per-view residual dumps, the derived tables and the
reproduction scripts are archived at Zenodo (DOI to be inserted before submission) and maintained on GitHub. Every
number in the tables is regenerated from those artefacts by a script in the archive, and a verification gate in the
repository re-checks the manuscript against them.

**Suggested reviewer profiles.** Because the topic sits between two communities, I would suggest: one reviewer from
the journal's 3DGS cluster (dynamic or feed-forward Gaussian splatting), one from the journal's point-cloud codec
cluster (G-PCC / V-PCC rate–distortion or complexity work), and one from neural-field compression outside the venue
(anchor-based or vector-quantised 3DGS coding). I have no conflicts to declare with respect to these areas.

**Declarations.** The manuscript is original, has not been published elsewhere, and is not under consideration by
another journal. The author declares no competing interests. A generative-AI declaration is included in the
manuscript, as required.

Thank you for your consideration.

Yours sincerely,
Tianji Su
Ningbo University, Ningbo, China
71736850@qq.com
