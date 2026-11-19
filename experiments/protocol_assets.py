"""Which published checkpoints are usable for cross-paper claims, and which are internal-only.

M16 established the rule the hard way: `bicycle` and `stump` reproduce the published 3DGS numbers to
within 0.6 dB, so our compressed rows can be compared with HAC/PCGS on those scenes; `bonsai` renders at
28.06 dB against a published 32.12 and was therefore excluded rather than compared.  Four rounds later
the exclusion was still only a sentence in M16, so a summary table re-introduced the invalid comparison.

This module is the registry the linter reads.  Adding a scene requires stating the measured clean PSNR,
the published one, and the delta — an asset cannot be marked comparable without evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = ROOT / "experiments" / "published_3dgs.json"

#: scene -> (cross_paper, reason).  `clean_ours` / `clean_published_3dgs` are the M16 measurements.
ASSETS = {
    "bicycle": {
        "cross_paper": True,
        "clean_ours": 24.52,
        "clean_published_3dgs": 25.11,
        "why": "reproduces the published 3DGS number within the 0.55 dB protocol bias (M16)",
    },
    "stump": {
        "cross_paper": True,
        "clean_ours": 26.15,
        "clean_published_3dgs": 26.66,
        "why": "reproduces the published 3DGS number within the 0.55 dB protocol bias (M16)",
    },
    "bonsai": {
        "cross_paper": False,
        "clean_ours": 28.06,
        "clean_published_3dgs": 32.12,
        "why": "4.1 dB below the published 3DGS render of the same checkpoint; the checkpoint/GT pairing "
               "cannot be vouched for, so bonsai rows are internal comparisons only (M16)",
    },
}

METHOD_NAMES = ("HAC", "PCGS", "3DGS", "ContextGS", "Scaffold-GS")


def excluded_scenes() -> list[str]:
    return [s for s, v in ASSETS.items() if not v["cross_paper"]]


def load_published() -> dict:
    return json.loads(PUBLISHED.read_text(encoding="utf-8"))


def sanity() -> list[str]:
    """The registry must agree with the published table it refers to."""
    problems = []
    pub = load_published()["methods"]["3dgs"]
    for scene, v in ASSETS.items():
        if scene not in pub:
            problems.append(f"{scene}: not in published_3dgs.json")
            continue
        delta = v["clean_published_3dgs"] - v["clean_ours"]
        if v["cross_paper"] and abs(delta) > 0.7:
            problems.append(f"{scene}: marked comparable but |Δ| = {abs(delta):.2f} dB")
        if not v["cross_paper"] and abs(delta) <= 0.7:
            problems.append(f"{scene}: marked excluded but |Δ| = {abs(delta):.2f} dB")
    return problems


if __name__ == "__main__":
    for p in sanity():
        print("PROBLEM:", p)
    print("excluded from cross-paper claims:", ", ".join(excluded_scenes()) or "(none)")
