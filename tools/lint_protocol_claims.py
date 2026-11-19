"""Flag cross-paper claims that use a protocol-excluded scene.

M16 excluded `bonsai` from comparisons against published methods (our render of that checkpoint is 4.1 dB
below the published one).  The exclusion lived in one paragraph, so it drifted: summary tables and even
one round's prose re-introduced "bonsai vs PCGS".  This linter makes the rule mechanical.

A violation is a line that
  * names an excluded scene,
  * names a published method,
  * and carries a PSNR-like number,
  * and does not itself say that the comparison is excluded/internal.

    python3 tools/lint_protocol_claims.py                 # scans the docs that carry numbers
    python3 tools/lint_protocol_claims.py path.md ...     # or an explicit set
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

import protocol_assets as PA  # noqa: E402

DEFAULT_DOCS = [
    ROOT / "experiments/FRONTIER_BOUND.md",
    ROOT / "experiments/METHOD_PLAN.md",
    ROOT / "experiments/artifacts/a4/sota_table.md",
    ROOT / "experiments/M16_RESULTS.md",
    ROOT / "experiments/M31_RESULTS.md",
    ROOT / "experiments/M32_RESULTS.md",
    ROOT / "experiments/M47_RESULTS.md",
    ROOT / "experiments/M48_RESULTS.md",
    ROOT / "experiments/M49_RESULTS.md",
    ROOT / "experiments/M50_RESULTS.md",
    ROOT / "experiments/M51_RESULTS.md",
    ROOT / "experiments/MIDRATE_BOUND.md",
]
PSNR_RE = re.compile(r"\b\d{2}\.\d{1,2}\b")
EXCUSE_RE = re.compile(r"exclud|internal|not comparab|不可比|内部", re.IGNORECASE)


def scan(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        low = line
        scene = next((s for s in PA.excluded_scenes() if s in low.lower()), None)
        if scene is None:
            continue
        method = next((m for m in PA.METHOD_NAMES if m in low), None)
        if method is None:
            continue
        if not PSNR_RE.search(low):
            continue
        if EXCUSE_RE.search(low):
            continue
        try:
            rel = str(path.relative_to(ROOT))
        except ValueError:
            rel = str(path)
        out.append({"file": rel, "line": i, "scene": scene,
                    "method": method, "text": line.strip()[:220]})
    return out


def main(argv: list[str]) -> int:
    docs = [Path(a) for a in argv[1:]] or DEFAULT_DOCS
    problems = []
    for d in docs:
        problems.extend(scan(d if d.is_absolute() else ROOT / d))
    for p in problems:
        print(f"{p['file']}:{p['line']}  [{p['scene']} vs {p['method']}]  {p['text']}")
    print(f"\n{len(problems)} unqualified cross-paper claim(s) on protocol-excluded scene(s)")
    for s in PA.sanity():
        print("registry PROBLEM:", s)
    return 1 if problems or PA.sanity() else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
