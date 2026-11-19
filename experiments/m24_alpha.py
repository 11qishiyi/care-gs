"""M24: pick the alphabet per stream, by measurement, after zstd.

M20 decided that one code per byte beats packed bits by 8.2 % — on the 45-column SH block — and every
SH stream has inherited that decision since, including a three-column block where the packed form is
2.7x smaller before compression.  This module stops inheriting: it encodes the same codes in every
candidate alphabet, compresses each candidate exactly as the container would, and keeps the smaller.

Nothing here changes a code, so the decoded model is bit-identical to the shelf point and any change in
rendered PSNR is a bug.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m4_bytes as M  # noqa: E402

LAYOUTS = ("bits", "bytes")


def zlen(buf: bytes, level: int = 12) -> int:
    return len(M._zstd(buf, level))


def choose(streams_by_layout: dict, names, level: int = 12, log=print) -> dict:
    """Per stream, the layout whose compressed size is smallest, with the full table kept."""
    table, choice = [], {}
    for name in names:
        cand = {lay: ss[name] for lay, ss in streams_by_layout.items() if name in ss}
        if not cand:
            continue
        row = {"stream": name,
               "candidates": {lay: {"raw": len(buf), "zstd": zlen(buf, level)}
                              for lay, buf in cand.items()}}
        best = min(row["candidates"], key=lambda k: row["candidates"][k]["zstd"])
        row["chosen"] = best
        row["saved_vs_bits"] = (row["candidates"].get("bits", {}).get("zstd", 0)
                                - row["candidates"][best]["zstd"])
        choice[name] = best
        table.append(row)
        log(f"  {name:16s} " + "  ".join(
            f"{lay}={row['candidates'][lay]['raw']/1e6:6.2f}->"
            f"{row['candidates'][lay]['zstd']/1e6:6.2f} MB" for lay in row["candidates"])
            + f"   keep {best}")
    return {"choice": choice, "table": table}


def build(splats, rank: int = 16, bits_total: int = 48, level: int = 12,
          spec_name: str = "gp8-8-8_c10_sh3", mode: str = "auto", coef_layout: str = "bits",
          jobs: int = 1, log=print) -> dict:
    """Container streams with the M22 basis colour block; ``mode`` selects the alphabet rule.

    ``coef_layout`` is the *coefficient* block's order: ``bits`` (component-major, packed), ``bytes``
    (component-major, one byte per code) or ``interleaved`` (all of one primitive's codes together,
    M34).  Only the last one changes what a lost frame costs.

    ``jobs`` runs the colour alphabets concurrently (M46).  The three passes read the same arrays and
    write their own streams, so they are independent by construction; the cost is that all three stream
    sets are live at once.
    """
    import m19_codec as C
    import m22_basis as B
    import qfp_rd as Q

    spec = Q.parse_spec(spec_name)
    geo, sh = M._attribute_arrays(splats)
    deg = int(splats.sh_degree)
    order = M.morton_order(geo["means"])
    n = int(geo["means"].shape[0])

    #: M45: the geometry streams do not depend on ``sh_layout``, so the alphabet search only needs
    #: the colour streams of the three layouts -- the geometry is built once instead of three times.
    geo_streams, geo_pp = M._encode(spec, geo, sh, deg, None, order, sh_layout=LAYOUTS[0], parts=("geo",))

    def colour(lay):
        return M._encode(spec, geo, sh, deg, None, order, sh_layout=lay, parts=("sh",))[0]

    if int(jobs) > 1:
        #: M46: three independent passes over the same arrays.  Each holds its own colour streams, so
        #: this trades ~0.7 GB of peak for wall clock -- never more than three workers, since there are
        #: exactly three alphabets.
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(int(jobs), len(LAYOUTS))) as pool:
            cand = dict(zip(LAYOUTS, pool.map(colour, LAYOUTS)))
    else:
        cand = {lay: colour(lay) for lay in LAYOUTS}
    res = choose(cand, [k for k in cand["bits"] if "sh" in k], level, log=log)
    if mode == "auto":
        use = res["choice"].get("sh_dc", "bits")
    elif mode in LAYOUTS:
        use = mode
    else:
        raise SystemExit(f"unknown mode {mode}")
    #: M43: keep only the winner's streams.  The two rejected layouts are never read again,
    #: and holding them costs half a gigabyte while the basis fit runs.
    keep = dict(geo_streams)
    keep.update(cand[use])
    del cand

    rest = B.rest_matrix(sh)[np.asarray(order)]
    f = B.fit(rest, rank)
    q = B.quantise_alloc(f["coef"], f["comp"], bits_total)
    streams = {k: v for k, v in keep.items() if "sh_rest" not in k}
    #: the ladder writes one scale level for DC and one for the rest block; the basis path replaces
    #: the rest block entirely, so the second level is a byte the decoder never reads.  Ship one.
    lvl = C.unpack_bits(streams["sh_scale"], 8, n * 2).reshape(n, 2)
    streams["sh_scale"] = M.pack_bits(lvl[:, 0].copy(), 8)
    streams["sh_hdr"] = np.frombuffer(streams["sh_hdr"], dtype=np.float32)[0:1].tobytes()
    meta_scale_levels = 1
    streams["sh_basis"] = np.asarray(f["basis"], dtype=np.float32).tobytes()
    streams["sh_basis_mean"] = np.asarray(f["mean"], dtype=np.float32).tobytes()
    streams["sh_basis_comp"] = np.asarray(f["comp"], dtype=np.float32).tobytes()
    streams["sh_coef_bits"] = np.asarray(q["bits"], dtype=np.uint8).tobytes()
    streams["sh_coef"] = B.pack_codes(q["codes"], q["bits"], coef_layout)
    streams["geo_hdr"] = C.geo_header(geo, spec)
    meta = {"spec": spec_name, "n": n, "sh_degree": deg, "sh_layout": use, "deg_out": deg,
            "sh_basis_rank": int(rank), "sh_coef_bits_total": int(q["bits_total"]),
            "sh_coef_layout": coef_layout, "sh_rest_cols": int(rest.shape[1]),
            "sh_energy": f["energy"], "sh_bits_per_component": [int(x) for x in q["bits"]],
            "alphabet_mode": mode, "alphabet_choice": res["choice"],
            "sh_scale_levels": int(meta_scale_levels)}
    return {"streams": streams, "meta": meta, "table": res["table"], "choice": res["choice"],
            "energy": f["energy"]}


def sizes(path: str) -> dict:
    """Per-stream ``raw``/``comp`` from the container's own size table."""
    import m19_codec as C
    meta, _ = C.read_container_sizes(path)
    return {e["name"]: {"raw": int(e["raw"]), "comp": int(e["comp"])} for e in meta["streams"]}


def report(path: str, plans, level: int = 12, out: str = "/workspace/res/m24", log=print,
           emit_ply: bool = True, emit_legacy: bool = True, coef_layout: str = "bits",
           suffix: str = "", min_frame: int = 0) -> list:
    import m19_codec as C
    import m20_model

    if min_frame:
        #: M34: the frame size is the knob that sets the cost of one lost frame
        C.MIN_FRAME = int(min_frame)
    mod = m20_model.load_model(path)
    rows = []
    for item in plans:
        spec_name, rank, bits = item if len(item) == 3 else ("gp8-8-8_c10_sh3", item[0], item[1])
        tag = f"{spec_name.replace('-', '_')}_r{rank:02d}_b{bits:03d}{suffix}"
        log(f"=== {tag} ===")
        rec = build(mod, rank=rank, bits_total=bits, level=level, spec_name=spec_name,
                    mode="auto", coef_layout=coef_layout, log=log)
        rec["meta"]["min_frame"] = int(C.MIN_FRAME)
        p = os.path.join(out, f"{tag}_auto.gs1")
        C.write_container(p, rec["streams"], rec["meta"], level)
        n = int(rec["meta"]["n"])

        #: the legacy container: every SH stream one code per byte, which is what ships today.
        #: ``emit_legacy=False`` measures the cost of the file that actually ships (one build, one write).
        if emit_legacy:
            leg = build(mod, rank=rank, bits_total=bits, level=level, spec_name=spec_name,
                        mode="bytes", log=lambda *a: None)
            pl = os.path.join(out, f"{tag}_legacy.gs1")
            C.write_container(pl, leg["streams"], leg["meta"], level)
        else:
            leg, pl = {"streams": rec["streams"], "meta": rec["meta"], "choice": {}}, p

        row = {"plan": tag, "rank": rank, "bits": bits, "n": n,
               "bytes_auto": os.path.getsize(p),
               "bytes_legacy": os.path.getsize(pl) if emit_legacy else os.path.getsize(p),
               "bytes_per_prim": os.path.getsize(p) / n, "choice": rec["choice"],
               "table": rec["table"], "file": p,
               "file_legacy": pl if emit_legacy else None}
        row["saved"] = row["bytes_legacy"] - row["bytes_auto"]
        sa, sl = sizes(p), sizes(pl)
        row["streams_auto"], row["streams_legacy"] = sa, sl
        log("  stream            legacy raw/comp      auto raw/comp")
        for name in sorted(set(sa) | set(sl), key=lambda k: -(sl.get(k, {}).get("comp", 0))):
            a_, l_ = sa.get(name, {"raw": 0, "comp": 0}), sl.get(name, {"raw": 0, "comp": 0})
            log(f"  {name:16s} {l_['raw']/1e6:7.2f}/{l_['comp']/1e6:7.2f}   "
                f"{a_['raw']/1e6:7.2f}/{a_['comp']/1e6:7.2f}")
        if emit_ply:
            for kind, path in (("auto", p), ("legacy", pl)):
                meta, streams = C.read_container(path)
                out_ply = os.path.join(out, f"{tag}_{kind}.ply")
                C.to_ply(meta, streams, out_ply)
                row[f"ply_{kind}"] = out_ply
        rows.append(row)
        log(f"  auto {row['bytes_auto']/1e6:7.2f} MB   legacy {row['bytes_legacy']/1e6:7.2f} MB   "
            f"saved {row['saved']/1e6:5.2f} MB   {row['bytes_per_prim']:5.2f} B/prim")
    json.dump(rows, open(os.path.join(out, "m24_streams.json"), "w"), indent=1)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ply", required=True)
    ap.add_argument("--plans", default="gp8-8-8_c10_sh3:16:48")
    ap.add_argument("--level", type=int, default=12)
    ap.add_argument("--out", default="/workspace/res/m24")
    ap.add_argument("--no-ply", action="store_true")
    ap.add_argument("--no-legacy", action="store_true",
                    help="skip the bytes-alphabet container; times the one file that ships")
    ap.add_argument("--coef-layout", default="bits", choices=("bits", "bytes", "interleaved"),
                    help="order of the M22 coefficient block (M34: interleaved = one record per "
                         "primitive, so a lost frame costs fewer primitives)")
    ap.add_argument("--suffix", default="", help="appended to the container's file-name tag")
    ap.add_argument("--min-frame", type=int, default=0,
                    help="M34: smallest zstd frame in bytes (0 = the module default, 4 MB)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    plans = []
    for item in a.plans.split(","):
        if not item.strip():
            continue
        parts = item.split(":")
        if len(parts) == 3:
            plans.append((parts[0], int(parts[1]), int(parts[2])))
        else:
            plans.append(("gp8-8-8_c10_sh3", int(parts[0]), int(parts[1])))
    report(a.ply, plans, a.level, a.out, emit_ply=not a.no_ply, emit_legacy=not a.no_legacy,
           coef_layout=a.coef_layout, suffix=a.suffix, min_frame=a.min_frame)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
