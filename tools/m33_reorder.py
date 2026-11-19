"""Rewrite a container with the colour header first, then ask what a half-downloaded file looks like.

The shipping layout is geometry-first: ``geo_hdr``, the cluster table, positions, quaternions,
scales, opacities, and only then ``sh_dc``/``sh_scale``/the colour block.  A client that stops at
half the payload therefore has every position and no colour at all -- M33 measured 9.25 dB on
bicycle at 50 %, which is a cliff and not a ladder.

Nothing in the format requires that order: every stream is independently framed and compressed, and
the decoder reads them by name.  This tool writes the *same* streams in a different physical order
(DC and the colour level first, geometry after) so the prefix at 50 % is a degree-0 model instead of
a colourless one.  It is a diagnostic, not a shipping change: it says how much of the ladder's
absence is a layout decision rather than a compression limit.

    python tools/m33_reorder.py --gs1 <file> --out <file> [--order dc-first|geometry-first]
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(HERE, "experiments"), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import m19_codec as C  # noqa: E402

#: What a viewer needs to render *anything*: the container's own header streams, then the DC term
#: and its level (the degree-0 model), then everything else in the shipping order.
DC_FIRST = ("geo_hdr", "sh_hdr", "sh_scale", "sh_dc", "geo_means", "cluster_hdr", "cluster_off",
            "geo_scales", "geo_quats", "geo_quat_which", "geo_quat_abc", "geo_opacities")


def reorder(src: str, dst: str, order=DC_FIRST) -> dict:
    """Write ``src``'s frames to ``dst`` with the streams physically in ``order``."""
    meta, _ = C.read_container_sizes(src)
    by_name = {s["name"]: s for s in meta["streams"]}
    head = [n for n in order if n in by_name]
    tail = [s["name"] for s in meta["streams"] if s["name"] not in head]
    new_names = head + tail
    old = {s["name"]: s for s in meta["streams"]}

    with open(src, "rb") as f:
        if f.read(4) != C.MAGIC:
            raise ValueError(f"{src}: not a GS1 file")
        version, head_len = struct.unpack("<II", f.read(8))
        meta_in = json.loads(f.read(head_len).decode("utf-8"))
        body = f.read()

    #: slice the payload per stream, in the order it was written
    off, blob = 0, {}
    for s in meta_in["streams"]:
        n = sum(s["frames"])
        blob[s["name"]] = body[off:off + n]
        off += n
    meta_out = dict(meta_in)
    meta_out["streams"] = [dict(old[n]) for n in new_names]
    payload = b"".join(blob[n] for n in new_names)
    head_bytes = json.dumps(meta_out, separators=(",", ":")).encode("utf-8")
    with open(dst, "wb") as f:
        f.write(C.MAGIC)
        f.write(struct.pack("<II", version, len(head_bytes)))
        f.write(head_bytes)
        f.write(payload)
    #: the rewrite is only correct if the file still decodes to the same bytes
    a, sa = C.read_container(src)
    b, sb = C.read_container(dst)
    same = all(sa[k] == sb[k] for k in sa) and set(sa) == set(sb)
    return {"src": src, "dst": dst, "order": new_names, "bytes": os.path.getsize(dst),
            "streams_identical": bool(same)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gs1", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    info = reorder(a.gs1, a.out)
    print(f"{info['dst']}  {info['bytes']/1e6:.2f} MB  streams_identical={info['streams_identical']}")
    print("order:", " ".join(info["order"][:12]), "...")
    if a.json:
        json.dump(info, open(a.json, "w", encoding="utf-8"), indent=1)
    return 0 if info["streams_identical"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
