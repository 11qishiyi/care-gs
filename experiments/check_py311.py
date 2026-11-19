"""Check every experiment script parses as Python 3.11, not just whatever the local shell has.

The node image ships Python 3.11.13 while this workstation runs 3.12+, and 3.12 added PEP 701
(nested f-strings may reuse their own quote character).  A file that only parses on 3.12 fails
on the node *after* the push, which is a wasted round trip, so this gate runs before pushing.

    python experiments/check_py311.py [paths...]
"""
from __future__ import annotations

import ast
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check(path: str) -> str | None:
    src = open(path, encoding="utf-8").read()
    try:
        ast.parse(src, filename=path, feature_version=(3, 11))
    except SyntaxError as exc:
        return f"{path}:{exc.lineno}: {exc.msg}"
    return None


def main(argv) -> int:
    paths = argv[1:]
    if not paths:
        paths = sorted(glob.glob(os.path.join(ROOT, "experiments", "**", "*.py"), recursive=True))
        paths += sorted(glob.glob(os.path.join(ROOT, "research", "code", "calib", "*.py")))
    bad = [e for e in (check(p) for p in paths) if e]
    for e in bad:
        print("FAIL", e)
    print(f"{len(paths) - len(bad)}/{len(paths)} files parse as 3.11")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
