"""Per-stream table for one shipping container (reads the container's own size table)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments"))

import m19_codec as C  # noqa: E402


def main(argv):
    path = argv[1]
    meta, _ = C.read_container_sizes(path)
    n = int(meta["n"]) if "n" in meta else 1
    rows = [(e["name"], int(e["raw"]), int(e["comp"])) for e in meta["streams"]]
    tot = sum(c for _, _, c in rows) or 1
    print(f"{os.path.basename(path)}  file {os.path.getsize(path)/1e6:.2f} MB  n={n:,}")
    print(f"{'stream':22s} {'raw MB':>9s} {'comp MB':>9s} {'share':>7s} {'b/prim':>7s}")
    for name, raw, comp in rows:
        print(f"{name:22s} {raw/1e6:9.2f} {comp/1e6:9.2f} {100.0*comp/tot:6.1f}% {comp/n:7.3f}")
    print(f"{'TOTAL':22s} {sum(r for _, r, _ in rows)/1e6:9.2f} {tot/1e6:9.2f} {100.0:6.1f}% "
          f"{tot/n:7.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
