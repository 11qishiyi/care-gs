"""Pull one entry out of a huge remote zip with HTTP range requests.

    python tools/zip_entry.py --url https://host/models.zip --list
    python tools/zip_entry.py --url ... --entry bicycle/point_cloud/iteration_30000/point_cloud.ply \
        --out /workspace/data/m20/bicycle.ply --workers 8

Why not ``zipfile``: the archive here is 14.7 GB and the entry we want is 1.5 GB.  ``zipfile`` against a
ranged file object reads in 8 kB blocks, which is one HTTP request per block.  So this parses the central
directory by hand (zip64 aware), then fetches only the bytes of the entry, in parallel chunks.

A single connection to this host runs at ~230 kB/s and eight run at a few times that, which is the
difference between a two-hour download and a twenty-minute one.
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
import threading
import time
import zlib

CHUNK = 256 << 10


def http_range(url: str, start: int, end: int, tries: int = 10) -> bytes:
    """Bytes [start, end] inclusive.

    Small ranges with a long fuse: at 40 kB/s (which this host does under contention) a 1 MB range needs
    half a minute, and with a dozen workers sharing the pipe it needs minutes, so a short retry budget
    turns a slow download into a failing one.
    """
    import urllib.request

    last = None
    for i in range(tries):
        req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}",
                                                  "User-Agent": "zip_entry/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                status = r.status
                buf = r.read()
            if status == 206 and len(buf) == end - start + 1:
                return buf
            last = f"status {status} short read {len(buf)} != {end - start + 1}"
        except Exception as exc:                     # noqa: BLE001 - retried and reported
            last = f"{type(exc).__name__}: {exc}"
        time.sleep(min(20, 2 + 2 * i))
    raise IOError(f"range {start}-{end} failed after {tries} tries: {last}")


def http_size(url: str) -> int:
    import urllib.request

    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "zip_entry/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return int(r.headers["Content-Length"])


def _eocd(url: str, size: int) -> dict:
    """Locate the end-of-central-directory record (and its zip64 companion)."""
    tail_len = min(size, 1 << 20)
    tail = http_range(url, size - tail_len, size - 1)
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise ValueError("no EOCD in the last 1 MB")
    (sig, disk, cd_disk, n_here, n_total, cd_size, cd_off, comment_len) = struct.unpack(
        "<IHHHHIIH", tail[i:i + 22])
    info = {"n": n_total, "cd_size": cd_size, "cd_off": cd_off}
    if cd_off == 0xFFFFFFFF or cd_size == 0xFFFFFFFF or n_total == 0xFFFF:
        j = tail.rfind(b"PK\x06\x06")               # zip64 EOCD
        if j < 0:
            raise ValueError("zip64 sizes present but no zip64 EOCD")
        (_s, _sz, _made, _need, _disk, _cdd, _n, _nt, cd_size64, cd_off64) = struct.unpack(
            "<IQHHIIQQQQ", tail[j:j + 56])
        info.update(cd_size=cd_size64, cd_off=cd_off64, n=_nt)
        info["zip64"] = tail.rfind(b"PK\x06\x07") >= 0
    return info


def _central_directory(url: str, cd_off: int, cd_size: int) -> list:
    raw = http_range(url, cd_off, cd_off + cd_size - 1)
    out, p = [], 0
    while raw[p:p + 4] == b"PK\x01\x02":
        (sig, made, need, flags, method, mtime, mdate, crc, csize, usize, nlen, elen, clen,
         disk, iattr, eattr, off) = struct.unpack("<IHHHHHHIIIHHHHHII", raw[p:p + 46])
        name = raw[p + 46:p + 46 + nlen].decode("utf-8", "replace")
        extra = raw[p + 46 + nlen:p + 46 + nlen + elen]
        q = 0
        while q + 4 <= len(extra):
            hid, hsz = struct.unpack("<HH", extra[q:q + 4])
            body = extra[q + 4:q + 4 + hsz]
            if hid == 1:                            # zip64 extended information
                k = 0
                for field in ("usize", "csize", "off"):
                    needs = (field == "usize" and usize == 0xFFFFFFFF) or \
                            (field == "csize" and csize == 0xFFFFFFFF) or \
                            (field == "off" and off == 0xFFFFFFFF)
                    if needs:
                        val = struct.unpack("<Q", body[k:k + 8])[0]
                        k += 8
                        if field == "usize":
                            usize = val
                        elif field == "csize":
                            csize = val
                        else:
                            off = val
            q += 4 + hsz
        out.append({"name": name, "method": method, "crc": crc, "csize": csize,
                    "usize": usize, "off": off, "flags": flags})
        p += 46 + nlen + elen + clen
    return out


def _data_offset(url: str, entry: dict) -> int:
    head = http_range(url, entry["off"], entry["off"] + 29)
    if head[:4] != b"PK\x03\x04":
        raise ValueError(f"bad local header at {entry['off']}")
    nlen, elen = struct.unpack("<HH", head[26:30])
    return entry["off"] + 30 + nlen + elen


def fetch_entry(url: str, entry: dict, out: str, workers: int = 8, log=print) -> str:
    """Fetch the entry's compressed bytes as ``workers`` streams that land on disk as they arrive.

    Writing each worker's bytes to its own file is what makes a stalled worker visible (its file stops
    growing) and the fetch resumable, instead of 1.5 GB living in memory until the last byte arrives.
    """
    start = _data_offset(url, entry)
    size = entry["csize"]
    log(f"{entry['name']}: {size/1e6:.1f} MB at {start} (method {entry['method']})")

    per = (size + workers - 1) // workers
    t0 = time.time()

    def work(i: int) -> None:
        a = i * per
        b = min(size, a + per) - 1
        part = f"{out}.part{i:02d}"
        done = os.path.getsize(part) if os.path.exists(part) else 0
        with open(part, "ab") as fh:
            while done < b - a + 1:
                lo = start + a + done
                hi = min(start + b, lo + CHUNK - 1)
                buf = http_range(url, lo, hi)
                fh.write(buf)
                fh.flush()
                done += len(buf)

    th = [threading.Thread(target=work, args=(i,)) for i in range(workers)]
    for t in th:
        t.start()
    while any(t.is_alive() for t in th):
        time.sleep(20)
        got = sum(os.path.getsize(f"{out}.part{i:02d}")
                  for i in range(workers) if os.path.exists(f"{out}.part{i:02d}"))
        log(f"  {got/1e6:7.1f} / {size/1e6:.1f} MB  ({time.time()-t0:.0f}s)")
    for t in th:
        t.join()

    blob = b""
    for i in range(workers):
        part = f"{out}.part{i:02d}"
        with open(part, "rb") as fh:
            blob += fh.read()
        os.remove(part)
    dt = time.time() - t0
    log(f"  fetched {len(blob)/1e6:.1f} MB in {dt:.0f}s ({len(blob)/1e6/max(dt, 1e-9):.2f} MB/s)")
    if entry["method"] != 0:
        log("  decompressing")
        blob = zlib.decompress(blob, -15)
    if entry["usize"] and len(blob) != entry["usize"]:
        raise ValueError(f"size {len(blob)} != {entry['usize']}")
    if zlib.crc32(blob) & 0xFFFFFFFF != entry["crc"]:
        raise ValueError("crc mismatch")
    with open(out, "wb") as fh:
        fh.write(blob)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", required=True)
    ap.add_argument("--entry", default="", help="exact name, or a suffix to match uniquely")
    ap.add_argument("--out", default="")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--size", type=int, default=0, help="skip the HEAD if already known")
    a = ap.parse_args()

    size = a.size or http_size(a.url)
    info = _eocd(a.url, size)
    print(f"archive {size/1e9:.2f} GB, {info['n']} entries, cd at {info['cd_off']}", flush=True)
    if a.list and not a.entry:
        for e in _central_directory(a.url, info["cd_off"], info["cd_size"]):
            print(f"{e['usize']/1e6:9.2f} MB  {e['name']}")
        return 0
    entries = _central_directory(a.url, info["cd_off"], info["cd_size"])
    if not a.entry:
        print("no --entry given", file=sys.stderr)
        return 2
    hit = [e for e in entries if e["name"] == a.entry] or \
          [e for e in entries if e["name"].endswith(a.entry)]
    if len(hit) != 1:
        print(f"{len(hit)} entries match {a.entry!r}", file=sys.stderr)
        for e in hit[:10]:
            print("  " + e["name"], file=sys.stderr)
        return 2
    out = a.out or hit[0]["name"].rsplit("/", 1)[-1]
    fetch_entry(a.url, hit[0], out, a.workers)
    print(f"wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
