"""Is the single-pass conclusion an artefact of its own noise assumption?

`tools/jvcir_resolution.py` models a single audit pass as `truth + N(0, sigma_cell)` with `sigma_cell` measured per
cell over 400 splits. This script rewrites that assumption by a factor k in {0.75, 1, 1.25, 1.5} and reports how the
conclusion moves. If the expected false-accept count and the accuracy stay in a narrow band, the claim in the paper
does not depend on the Gaussian assumption being exactly right --- only on the audit's error being of that order.

    python tools/j6_sigma_sensitivity.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

A4 = Path("experiments/artifacts/a4")
SRC = Path("results_v120/audit_bound_nobonsai.json")
KS = [0.75, 1.0, 1.25, 1.5]
EPSS = [1.0, 2.0]


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def main() -> None:
    d = json.loads((A4 / "j2_audit_decision.json").read_text(encoding="utf-8"))
    cells = d["per_cell"]
    sig = {(r["scene"], r["variant"]): float(r["audit_mae_pp"])
           for r in json.loads(SRC.read_text(encoding="utf-8"))["rows"]}
    rows = []
    for k in KS:
        for eps in EPSS:
            fa = sum(phi((eps - c["truth"]) / (k * sig.get((c["scene"], c["variant"]), 2.0)))
                     for c in cells if c["truth"] > eps)
            fr = sum(1.0 - phi((eps - c["truth"]) / (k * sig.get((c["scene"], c["variant"]), 2.0)))
                     for c in cells if c["truth"] <= eps)
            rows.append(dict(sigma_scale=k, eps=eps, expected_false_accept=round(fa, 2),
                             expected_false_reject=round(fr, 2),
                             expected_accuracy=round(1.0 - (fa + fr) / len(cells), 3)))
    out = {"source": "j2_audit_decision.json + audit_bound_nobonsai.json",
           "note": "single pass = truth + N(0, k * sigma_cell); k rewrites the noise assumption", "rows": rows}
    (A4 / "j6_sigma_sensitivity.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    print(f"{'sigma x':>8s} {'eps':>5s} {'E[false acc]':>13s} {'E[false rej]':>13s} {'accuracy':>9s}")
    for r in rows:
        print(f"{r['sigma_scale']:8.2f} {r['eps']:5.1f} {r['expected_false_accept']:13.2f} "
              f"{r['expected_false_reject']:13.2f} {r['expected_accuracy']:9.3f}")
    at1 = [r for r in rows if r["eps"] == 1.0]
    print(f"\nat eps=1 the expected false accepts span "
          f"{min(r['expected_false_accept'] for r in at1):.2f}-{max(r['expected_false_accept'] for r in at1):.2f} "
          f"and the accuracy {min(r['expected_accuracy'] for r in at1):.3f}-{max(r['expected_accuracy'] for r in at1):.3f}")
    print(f"wrote {A4/'j6_sigma_sensitivity.json'}")


if __name__ == "__main__":
    main()
