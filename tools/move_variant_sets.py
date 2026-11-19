"""Move the VARIANT_SETS registry below every grid constant it references.

`qfp_rd.py` defines AFQ_VARIANTS and M3_VARIANTS after the M15/M16 grids, so a registry dict built
at the M16 block cannot see them.  This moves the block to just after M3_VARIANTS.

    python tools/move_variant_sets.py
"""
from __future__ import annotations

import sys

PATH = "experiments/qfp_rd.py"
MARK = "#: The registered grids, keyed by the value of ``--variant-set``."


def main() -> int:
    src = open(PATH, encoding="utf-8").read()
    if MARK not in src:
        print("registry block not found -- nothing to do")
        return 0
    start = src.index(MARK)
    end = src.index("}\n", start) + 2
    block = src[start:end]
    src = src[:start] + src[end:].lstrip("\n")
    m3 = src.index('M3_VARIANTS = ",".join([')
    close = src.index("])\n", m3) + 3
    src = src[:close] + "\n\n" + block + src[close:]
    open(PATH, "w", encoding="utf-8", newline="\n").write(src)
    print(f"moved {len(block)} characters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
