import io

def append(path, frag):
    a = io.open(path, encoding="utf-8").read()
    n = io.open(frag, encoding="utf-8").read()
    io.open(path, "w", encoding="utf-8").write(a.rstrip() + "\n" + n)
    print(f"{path}: +{len(n)} chars")

append("APPENDIX_negative_results.md", "tools/n36.md")
append("experiments/FRONTIER_BOUND.md", "tools/fb8.md")

# METHOD_PLAN: the round result, plus the amendment registered before the sweep existed
a = io.open("experiments/METHOD_PLAN.md", encoding="utf-8").read()
spec = io.open("tools/m29_spec.md", encoding="utf-8").read()
amend = io.open("tools/m29_amend.md", encoding="utf-8").read()
round_doc = """

---

## M29 round result (round 25, 2026-11-16 07:00, data on disk)

Two verdicts, one per question.  **`contexts_do_not_pay`** — the attribute codes are at their entropy
(zstd is within 0.2 bits of the order-1 bound on every stream; all five decoder-computable contexts land
within 0.1 % of plain zstd, and the split container is larger).  **`shelf_extends`** — with the widths
treated as the only lever, the near-lossless point moves to **76.56 MB / 12.49 B per primitive /
24.06 dB / 18.90×** (from 83.41 MB / 24.08 dB / 17.35×), decode 7.51 s and 1.96 GB, decoder unchanged.

* F1 PASS (76.56 MB ≤ 78 MB at 24.06 dB ≥ 24.00 dB), F2 reported (four points), F3 PASS.
* The sweep is shallow then steep: 6 bits cost 0.01 dB, the last 13 cost 0.05 dB; the position quantiser
  (10 → 8 bits) is 1.5 B/primitive on its own.
* Coarsening saves *less* than the nominal bits wherever zstd was already below the width (P0 → P1:
  1.8 MB saved against 4.9 MB predicted).

Details: `experiments/M29_RESULTS.md`; negative result **N36**; probe `experiments/m29_entropy.py`;
split machinery `experiments/m29_split.py` (+4 tests, bit-identical round trip).
"""
io.open("experiments/METHOD_PLAN.md", "w", encoding="utf-8").write(
    a.rstrip() + "\n\n---\n\n" + spec.rstrip() + "\n" + amend + round_doc)
print("METHOD_PLAN: spec + amendment + round result appended")
