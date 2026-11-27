"""Measure what the node can actually pull: one stream, and N streams in parallel.

The launcher's throughput gate measured a single 8 MB range request, which is the wrong object: the PLY download uses
48 parallel range requests, and the mirror throttles per connection rather than per host. This prints both numbers so
the gate can compare the one it implements.

    python3 experiments/bench_node.py [--url ...] [--streams 8] [--mb 8]
"""
from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor

import requests


def resolve(url: str) -> str:
    r = requests.head(url, allow_redirects=False, timeout=30)
    return r.headers.get("Location") or url


def one(session: requests.Session, url: str, start: int, size: int) -> tuple[int, float]:
    t0 = time.time()
    r = session.get(url, headers={"Range": f"bytes={start}-{start + size - 1}"}, timeout=90, stream=True)
    n = 0
    for chunk in r.iter_content(1 << 16):
        n += len(chunk)
    return n, time.time() - t0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="https://hf-mirror.com/datasets/dylanebert/3dgs/resolve/main/"
                                     "bicycle/point_cloud/iteration_30000/point_cloud.ply")
    ap.add_argument("--streams", type=int, default=8)
    ap.add_argument("--mb", type=int, default=8)
    a = ap.parse_args()

    signed = resolve(a.url)
    print(f"signed url: {'yes' if signed != a.url else 'no (using the mirror url)'}")
    size = a.mb << 20

    t0 = time.time()
    with requests.Session() as s:
        n, _ = one(s, signed, 0, size)
    dt = max(time.time() - t0, 0.1)
    print(f"single stream : {n / dt / 1024:7.0f} KB/s ({n} B in {dt:.1f}s)")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=a.streams) as ex:
        futs = [ex.submit(one, requests.Session(), signed, i * size, size) for i in range(a.streams)]
        total = sum(f.result()[0] for f in futs)
    dt = max(time.time() - t0, 0.1)
    print(f"{a.streams:2d} streams    : {total / dt / 1024:7.0f} KB/s ({total} B in {dt:.1f}s)")


if __name__ == "__main__":
    main()