"""Print the stream table of a .gs1 file: what the bytes are actually spent on.

Used by M20/M21 to attribute a file size to attributes, and by M21 to see what separability costs:
the same three bits per coefficient as one packed stream, or as three planes with their own frames.
"""

from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m19_codec as C  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    for path in a.files:
        meta, total = C.read_container_sizes(path)
        head = C._header_len(path)
        print(f"\n{os.path.basename(path)}  {os.path.getsize(path)/1e6:.2f} MB "
              f"(header {head} B, payload {total/1e6:.2f} MB, {meta.get('spec')}, "
              f"n={meta.get('n'):,}, layout={meta.get('sh_layout')}"
              f"{', progressive' if meta.get('sh_progressive') else ''})")
        for r in C.layer_table(path):
            print(f"  {r['name']:18s} {r['comp']/1e6:8.2f} MB  "
                  f"raw {r['raw']/1e6:8.2f} MB  {100.0*r['comp']/max(1,total):5.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
