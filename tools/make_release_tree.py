"""Stage a clean release tree for GitHub (and therefore Zenodo).

Only what the paper needs is copied: the manuscript and its generated tables, the six figures, the generators, the
artifact JSON every number comes from, the round notes, the review documents, and the two small pulled bundles the
figures are built from. Everything else in the working directory (caches, node logs, intermediate archives, the
9.7 MB PDF that was read for the survey) stays out.

    python tools/make_release_tree.py [--out _repo]
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(".")
PATTERNS = [
    ("submission/jvcir", ["*.tex", "*.bib", "*.txt", "*.pdf", "*.md"]),
    ("figures_j", ["*.pdf", "*.png"]),
    ("tools", ["*.py"]),
    ("experiments", ["*.py", "*.sh", "*.md", "*.json"]),
    ("experiments/artifacts/a4", ["*.json"]),
    ("review", ["*.md"]),
    ("research/code/calib", ["*.py"]),
    ("_pull_j5", ["*.png", "*.jpg", "*.json"]),
    ("_pull_j6", ["*.json"]),
]
SKIP_NAMES = {"__pycache__"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_repo")
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    n = 0
    total = 0
    for rel, globs in PATTERNS:
        src_dir = ROOT / rel
        if not src_dir.exists():
            print(f"  !! missing {rel}")
            continue
        dst_dir = out / rel
        dst_dir.mkdir(parents=True, exist_ok=True)
        for pat in globs:
            for f in sorted(src_dir.glob(pat)):
                if f.is_dir() or f.name in SKIP_NAMES:
                    continue
                dst = dst_dir / f.name
                shutil.copy2(f, dst)
                n += 1
                total += f.stat().st_size

    # data/ mirrors the two pulls under the name the README uses
    for src, dst in (("_pull_j5", "data/pull_j5"), ("_pull_j6", "data/pull_j6")):
        if (ROOT / src).exists():
            shutil.copytree(ROOT / src, out / dst, dirs_exist_ok=True)
            for f in (out / dst).glob("*.py"):
                f.unlink()

    for name in ("README.md", "LICENSE", "CITATION.cff"):
        src = Path("_repo_in") / name
        if src.exists():
            shutil.copy2(src, out / name)

    gi = Path("_repo_in") / ".gitignore"
    if gi.exists():
        shutil.copy2(gi, out / ".gitignore")

    print(f"staged {n} files, {total/1e6:.1f} MB -> {out}/")
    big = sorted(((p.stat().st_size, p.relative_to(out)) for p in out.rglob('*') if p.is_file()), reverse=True)[:6]
    for sz, p in big:
        print(f"  {sz/1e6:6.2f} MB  {p}")


if __name__ == "__main__":
    main()
