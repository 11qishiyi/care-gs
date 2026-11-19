"""M22: one colour basis for six million Gaussians.

The per-primitive SH block is 20.61 B of a 23.57 B primitive and M20 showed it is at its empirical
floor *as 45 independent numbers at 3 bits each*.  This module asks the cheaper question before
rebuilding the representation: how many numbers does this model's colour actually have, and how do the
bits want to be spread over them?

Fit: centre the ``(n, 45)`` rest-coefficient matrix, randomised SVD, keep ``r`` components.  The basis
(``r x 45`` floats) is shared by the whole asset; every primitive keeps ``r`` coefficients, quantised
with a per-component depth chosen by reverse water-filling on the component variances under a fixed
bit budget.  The geometry path is untouched, so a rendered difference is a colour-model difference.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import m4_bytes as M  # noqa: E402


# ---------------------------------------------------------------------------
# the fit
# ---------------------------------------------------------------------------


def rest_matrix(sh) -> np.ndarray:
    """``(n, 45)`` rest coefficients, the block the shelf spends 20.61 B on."""
    arr = sh["rest"] if isinstance(sh, dict) else sh
    arr = np.asarray(arr)
    return np.asarray(arr, dtype=np.float32).reshape(arr.shape[0], -1)


def fit(rest: np.ndarray, rank: int, seed: int = 0) -> dict:
    """Shared basis + per-component scales for ``rank`` components."""
    import torch

    #: ``svd_lowrank`` starts from a random matrix, so without this the same model encodes to a
    #: different file on every run — which would make the paper's bytes irreproducible and would
    #: make two containers of the same model differ for no reason anyone could see.
    torch.manual_seed(int(seed))
    x = torch.from_numpy(np.ascontiguousarray(rest, dtype=np.float32))
    mean = x.mean(dim=0, keepdim=True)
    xc = x - mean
    u, s, v = torch.svd_lowrank(xc, q=min(rank + 10, min(xc.shape) - 1), niter=4)
    basis = v[:, :rank].T.contiguous()                     # (rank, 45)
    coef = (xc @ basis.T).numpy()                          # (n, rank)
    #: scale per component from a high quantile, not the max: one outlier primitive otherwise sets
    #: the step for six million others (measured: 115 % relative error, worse than coding zero).
    comp = np.quantile(np.abs(coef), 0.999, axis=0) * 1.15
    comp = np.maximum(np.asarray(comp, dtype=np.float32), 1e-9)
    energy = float((s[:rank] ** 2).sum() / (s ** 2).sum())
    return {"basis": basis.numpy().astype(np.float32), "mean": mean.numpy().astype(np.float32),
            "comp": comp, "coef": coef, "energy": energy,
            "singular": s[:max(rank, 8)].numpy()}


def allocate(comp: np.ndarray, bits_total: int, lo: int = 1, hi: int = 12) -> np.ndarray:
    """Greedy reverse water-filling: hand out ``bits_total`` bits across components by variance.

    Distortion of component j at ``b`` bits is ``comp_j^2 * 4**-b / 12``; the greedy step gives one more
    bit to whichever component gains most, which is the integer optimum for squared error.
    """
    r = len(comp)
    bits_total = int(max(bits_total, lo * r))
    b = np.full(r, lo, dtype=np.int64)
    s2 = np.asarray(comp, dtype=np.float64) ** 2
    for _ in range(bits_total - lo * r):
        if bool((b >= hi).all()):
            break                     # every component is at the cap: the budget cannot be spent
        gain = s2 * (4.0 ** -b) * 3.0
        gain[b >= hi] = -1.0
        b[int(np.argmax(gain))] += 1
    return b


def quantise_alloc(coef: np.ndarray, comp: np.ndarray, bits_total: int) -> dict:
    """Uniform mid-tread per component at the allocated depth: ``bits_total`` bits per primitive."""
    b = allocate(comp, bits_total)
    wide = int(b.max()) > 8
    out = np.empty_like(coef, dtype=np.float32)
    codes = []
    for j, bj in enumerate(b):
        step = 2.0 / float(1 << int(bj))
        v = np.asarray(coef[:, j], dtype=np.float32) / comp[j]
        c = np.clip(np.floor((v + 1.0) / step), 0, (1 << int(bj)) - 1)
        c = c.astype(np.uint16 if wide else np.uint8)
        out[:, j] = ((c.astype(np.float32) + 0.5) * step - 1.0) * comp[j]
        codes.append(c)
    return {"codes": codes, "bits": b.astype(np.uint8), "bits_total": int(b.sum()),
            "err": float(np.abs(out - coef).mean()), "rec": out}


def quantise_prim(coef: np.ndarray, comp: np.ndarray, bits: int = 3) -> dict:
    """The first (bad) quantiser, kept for the record: one scale per primitive for all components."""
    qmax = (1 << (bits - 1)) - 1
    cn = coef / comp[None, :]
    u = np.abs(cn).max(axis=1) / qmax
    ref = float(max(u.max(), 1e-12))
    lvl = np.clip(np.rint(u / ref * 255.0), 0, 255).astype(np.uint8)
    uq = lvl.astype(np.float32) / 255.0 * ref
    codes = np.clip(np.rint(cn / np.maximum(uq, 1e-12)[:, None]), -qmax - 1, qmax).astype(np.int64)
    codes += qmax + 1
    rec = (codes - (qmax + 1)).astype(np.float32) * uq[:, None] * comp[None, :]
    return {"codes": codes.astype(np.uint8), "lvl": lvl, "ref": np.float32(ref),
            "err": float(np.abs(rec - coef).mean()), "qmax": qmax, "rec": rec}


# ---------------------------------------------------------------------------
# code packing
# ---------------------------------------------------------------------------


def pack_codes(codes, bits, layout: str = "bits") -> bytes:
    """Concatenate per-component codes; each component has its own depth, so each gets its own span.

    ``layout="interleaved"`` writes one primitive's codes together (component-major is the default and
    what every container before M34 used).  The difference only matters under damage: a 4 MB frame of
    a component-major block holds one component for ~68 % of the primitives, while the same frame of an
    interleaved block holds *all* components of ~(4 MB / bytes-per-primitive) of them.
    """
    import m19_codec as C

    if layout == "interleaved":
        n = len(codes[0])
        out = np.empty((n, len(bits)), dtype=np.uint8)
        for c, bj in enumerate(bits):
            out[:, c] = np.asarray(codes[c], dtype=np.uint8)
        return out.tobytes()
    out = []
    for c, bj in zip(codes, bits):
        dt = np.uint8 if int(bj) <= 8 else np.uint16
        if layout == "bytes":
            out.append(np.asarray(c, dtype=dt).tobytes())
        else:
            out.append(M.pack_bits(np.asarray(c).astype(np.int64), int(bj)))
    return b"".join(out)


def unpack_codes(buf, bits, n: int, layout: str = "bits") -> list:
    import m19_codec as C

    if layout == "interleaved":
        rec = np.frombuffer(buf, dtype=np.uint8, count=n * len(bits)).reshape(n, len(bits))
        return [rec[:, c].copy() for c in range(len(bits))]
    out, off = [], 0
    for bj in bits:
        bj = int(bj)
        if layout == "bytes":
            dt = np.uint8 if bj <= 8 else np.uint16
            out.append(np.frombuffer(buf, dtype=dt, count=n, offset=off).copy())
            off += n * (1 if bj <= 8 else 2)
        else:
            nbytes = int(np.ceil(n * bj / 8.0))
            #: narrow on purpose: the decoder holds these for a whole asset (M25)
            dt = np.uint8 if bj <= 8 else (np.uint16 if bj <= 16 else np.uint32)
            out.append(C.unpack_bits(buf[off:off + nbytes], bj, n, dtype=dt))
            off += nbytes
    return out


# ---------------------------------------------------------------------------
# encode / decode one model
# ---------------------------------------------------------------------------


def encode_basis(splats, rank: int, bits_total: int = 64, level: int = 12, path: str = None,
                 layout: str = "bits", spec_name: str = "c10_o8_sh3",
                 return_recon: bool = False, geo_delta: bool = False,
                 geo_mode: str = "delta") -> dict:
    """Container with the shelf geometry, the shelf DC, and a shared basis for the rest block."""
    import m19_codec as C
    import qfp_rd as Q

    spec = Q.parse_spec(spec_name)
    geo, sh = M._attribute_arrays(splats)
    deg = int(splats.sh_degree)
    n = int(geo["means"].shape[0])
    order = M.morton_order(geo["means"])
    streams, model_bpp = M._encode(spec, geo, sh, deg, None, order, sh_layout="bytes")
    rest = rest_matrix(sh)[np.asarray(order)]
    f = fit(rest, rank)
    q = quantise_alloc(f["coef"], f["comp"], bits_total)

    streams.pop("sh_rest", None)
    streams["sh_basis"] = np.asarray(f["basis"], dtype=np.float32).tobytes()
    streams["sh_basis_mean"] = np.asarray(f["mean"], dtype=np.float32).tobytes()
    streams["sh_basis_comp"] = np.asarray(f["comp"], dtype=np.float32).tobytes()
    streams["sh_coef_bits"] = np.asarray(q["bits"], dtype=np.uint8).tobytes()
    streams["sh_coef"] = pack_codes(q["codes"], q["bits"], layout)
    #: the rest block's own width (45 at degree 3).  Taken from the matrix rather than from the
    #: spec's degree helper — the helper's answer once disagreed with what the basis was fitted on,
    #: and the mismatch only surfaced when the decoder tried to reshape the basis.
    cols = int(rest.shape[1]) + 3
    meta = {"spec": spec_name, "n": n, "sh_degree": deg, "sh_layout": "bytes",
            "deg_out": int(deg), "model_bytes_per_prim": float(model_bpp),
            "sh_basis_rank": int(rank), "sh_coef_bits_total": int(q["bits_total"]),
            "sh_coef_layout": layout, "sh_rest_cols": cols - 3, "sh_energy": f["energy"],
            "sh_bits_per_component": [int(x) for x in q["bits"]]}
    if getattr(spec, "sh_vq_bits", None):
        meta["sh_vq_bits"] = int(spec.sh_vq_bits)
    streams["geo_hdr"] = C.geo_header(geo, spec)
    if geo_delta:
        #: M23: recode the geometry streams as Morton deltas.  The decoded levels are identical.
        import m23_pred
        meta, streams = m23_pred.apply(meta, streams, mode=geo_mode)
    info = C.write_container(path, streams, meta, level) if path else None
    out = {"streams": streams, "meta": meta, "info": info, "energy": f["energy"],
           "coef_err": q["err"], "model_bytes_per_prim": float(model_bpp),
           "bits_per_component": [int(x) for x in q["bits"]]}
    if return_recon:
        #: the encoder's own idea of the rest block, in the container's primitive order
        out["recon"] = (f["mean"] + q["rec"] @ f["basis"]).astype(np.float32)
        out["order"] = np.asarray(order)
    return out


def coef_windows(meta: dict, bits, n: int, layout: str = "bits") -> list:
    """``[(component, i0, i1)]`` -- which primitive window of which component each lost frame covers.

    The codes are concatenated component-major, so a lost byte range maps to exactly one component
    and a primitive window inside it.  Both follow from ``n``, the component depth and the layout,
    which is why a decoder can do this from the header alone.
    """
    ent = next((s for s in meta.get("streams", []) if s.get("name") == "sh_coef"), None)
    if not ent or not ent.get("lost_ranges"):
        return []
    if layout == "interleaved":
        #: one record per primitive, so a byte range covers a contiguous primitive window for *all*
        #: components at once
        rec = len(bits)
        out = []
        for lo_b, hi_b in ent["lost_ranges"]:
            if hi_b <= lo_b:
                continue
            i0, i1 = max(0, lo_b // rec), min(n, int(np.ceil(hi_b / rec)))
            if i1 > i0:
                out += [(k, i0, i1) for k in range(rec)]
        return out
    spans, off = [], 0
    for bj in bits:
        bj = int(bj)
        span = (n if bj <= 8 else n * 2) if layout == "bytes" else int(np.ceil(n * bj / 8.0))
        spans.append((off, off + span, bj))
        off += span
    out = []
    for lo_b, hi_b in ent["lost_ranges"]:
        if hi_b <= lo_b:
            continue
        for k, (s0, s1, bj) in enumerate(spans):
            a, b = max(lo_b, s0), min(hi_b, s1)
            if b <= a:
                continue
            if layout == "bytes":
                step = 1 if bj <= 8 else 2
                i0, i1 = (a - s0) // step, int(np.ceil((b - s0) / step))
            else:
                i0 = (a - s0) * 8 // bj
                i1 = int(np.ceil((b - s0) * 8 / bj))
            i0, i1 = max(0, int(i0)), min(n, int(i1))
            if i1 > i0:
                out.append((k, i0, i1))
    return out


def neutralise_coef(codes: list, bits, meta: dict, n: int, layout: str = "bits") -> list:
    """Fill the codes of frames that failed their checksum with the code that means *zero*.

    The basis alphabet has no reserved "no colour" symbol: a coefficient is decoded as
    ``(code + 0.5) * step - 1``, so the code that means zero is the **midpoint** ``2**(b-1)``, one per
    component.  Zero-filled bytes (which is what a damaged frame leaves behind) decode to the most
    negative value the alphabet has, so a lost frame does not just lose its colour, it paints the
    primitives it held as dark as the model can go: bicycle 16.51 dB instead of 24.06 for a single
    4 MB frame (M33).  The shelf streams have their own reserved neutral code (``qmax + 1``); this is
    the basis block's equivalent.
    """
    windows = coef_windows(meta, bits, n, layout)
    if not windows:
        return codes
    out = [np.array(c, copy=True) for c in codes]
    for k, i0, i1 in windows:
        out[k][i0:i1] = 1 << (int(bits[k]) - 1)
    return out


def solve_basis(meta: dict, streams: dict, n: int, cols: int, out: np.ndarray = None,
                chunk: int = 1 << 20) -> np.ndarray:
    """``(n, 45)`` rest block from basis streams (decoder side; also used by ``m19_codec``).

    Reconstructed in float32 and in chunks: the full block is 2.2 GB in float64 for a 6 M-primitive
    asset, and the renderer consumes float32 anyway.  ``out`` lets the caller hand in a pre-allocated
    buffer so the peak is one copy of the answer, not two.
    """
    r = int(meta["sh_basis_rank"])
    basis = np.frombuffer(streams["sh_basis"], dtype=np.float32).reshape(r, cols)
    mean = np.frombuffer(streams["sh_basis_mean"], dtype=np.float32)
    comp = np.frombuffer(streams["sh_basis_comp"], dtype=np.float32)
    bits = list(np.frombuffer(streams["sh_coef_bits"], dtype=np.uint8))
    codes = unpack_codes(streams["sh_coef"], bits, n, str(meta.get("sh_coef_layout", "bits")))
    codes = neutralise_coef(codes, bits, meta, n, str(meta.get("sh_coef_layout", "bits")))

    if out is None:
        out = np.empty((n, cols), dtype=np.float32)
    steps = [np.float32(2.0 / float(1 << int(bj))) for bj in bits]
    chunk = max(1, int(chunk))
    for i in range(0, n, chunk):
        j = min(n, i + chunk)
        coef = np.empty((j - i, len(bits)), dtype=np.float32)
        for k, bj in enumerate(bits):
            #: the packed code is an unsigned integer of ``bj`` bits; the half-step offset is what
            #: the encoder's ``(code + 0.5) * step - 1`` produced before quantisation
            coef[:, k] = (codes[k][i:j].astype(np.float32) + np.float32(0.5)) * steps[k] - np.float32(1.0)
            coef[:, k] *= comp[k]
        np.matmul(coef, basis, out=out[i:j])
        out[i:j] += mean
    return out


# ---------------------------------------------------------------------------
# probe: how low-rank is this colour, and where do the bits want to go
# ---------------------------------------------------------------------------


def probe(path: str, ranks=(8, 16, 32), budgets=(32, 48, 64, 96, 128, 165)) -> dict:
    import m20_model
    import qfp_rd as Q

    t0 = time.time()
    mod = m20_model.load_model(path)
    rest = rest_matrix({"rest": mod.shN})
    n = rest.shape[0]
    print(f"{os.path.basename(path)}: {n:,} primitives, rest {rest.shape[1]} cols, "
          f"loaded {time.time()-t0:.1f} s", flush=True)

    #: reference the basis has to beat: the shipped 3-bit ladder on the same block
    qq = quantise_prim(rest, np.ones(rest.shape[1], dtype=np.float32),
                       bits=int(Q.parse_spec("c10_o8_sh3").sh_bits))
    base = float(np.sqrt(((qq["rec"] - rest) ** 2).mean() / max(1e-12, (rest ** 2).mean())))
    print(f"  shelf 3-bit ladder: rel RMSE {base*100:6.3f}%  (20.61 B/prim, the thing to beat)",
          flush=True)

    mean = rest.mean(axis=0, keepdims=True)
    out = {"path": path, "n": n, "shelf_rel_rmse": base, "rows": []}
    for r in ranks:
        f = fit(rest, r)
        for B in budgets:
            q = quantise_alloc(f["coef"], f["comp"], B)
            rec = mean + q["rec"] @ f["basis"]
            err = float(np.sqrt(((rec - rest) ** 2).mean() / max(1e-12, (rest ** 2).mean())))
            hdr = (r * rest.shape[1] * 4 + rest.shape[1] * 4 + r) / n
            row = {"rank": r, "bits": int(q["bits_total"]), "rel_rmse": err,
                   "bytes_per_prim": q["bits_total"] / 8.0 + hdr, "energy": f["energy"],
                   "bits_per_component": [int(x) for x in q["bits"]]}
            out["rows"].append(row)
            print(f"  r={r:2d}  {q['bits_total']:3d} bits ({q['bits_total']/8.0:5.2f} B)  "
                  f"rel RMSE {err*100:6.3f}%  {'BEATS' if err < base else '     '} shelf  "
                  f"alloc {list(q['bits'][:6])}...", flush=True)
    del mod
    return out


def encode_all(ply: str, plans, out: str, level: int = 12, layouts=("bits",),
               spec_name: str = "c10_o8_sh3", geo_delta: bool = False, tag_prefix: str = "") -> list:
    """Encode the same model for each ``(rank, bits)`` plan, decode it back, export the PLY."""
    import m19_codec as C
    import m20_model

    mod = m20_model.load_model(ply)
    rows = []
    for rank, bits in plans:
        for layout in layouts:
            tag = f"{tag_prefix}r{rank:02d}_b{bits:03d}_{layout}"
            p = os.path.join(out, f"{tag}.gs1")
            t0 = time.time()
            rec = encode_basis(mod, rank=rank, bits_total=bits, level=level, path=p, layout=layout,
                               spec_name=spec_name, geo_delta=geo_delta)
            enc_s = time.time() - t0
            t1 = time.time()
            meta, streams = C.read_container(p)
            dec = C.decode(meta, streams)
            dec_s = time.time() - t1
            ply_out = os.path.join(out, f"{tag}.ply")
            C.to_ply(meta, streams, ply_out)
            size = os.path.getsize(p)
            n = int(meta["n"])
            row = {"rank": rank, "bits": bits, "layout": layout, "bytes": size, "n": n,
                   "bytes_per_prim": size / n, "encode_s": round(enc_s, 1),
                   "decode_s": round(dec_s, 2), "energy": rec["energy"], "file": p, "ply": ply_out,
                   "bits_per_component": rec["bits_per_component"]}
            rows.append(row)
            print(f"  r={rank:2d} B={bits:3d} {layout:5s} {size/1e6:7.2f} MB  "
                  f"{row['bytes_per_prim']:5.2f} B/prim  enc {enc_s:5.1f} s  dec {dec_s:5.2f} s",
                  flush=True)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe", help="reference PLY to measure the colour spectrum on")
    ap.add_argument("--encode", help="reference PLY to encode for the given plans")
    ap.add_argument("--ranks", default="8,16,32")
    ap.add_argument("--budgets", default="32,48,64,96,128,165")
    ap.add_argument("--plans", default="16:48,16:64,32:64,32:96")
    ap.add_argument("--out", default="/workspace/res/m22/models")
    ap.add_argument("--layouts", default="bits")
    ap.add_argument("--spec", default="c10_o8_sh3")
    ap.add_argument("--geo-delta", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    if a.probe:
        ranks = tuple(int(x) for x in a.ranks.split(",") if x.strip())
        budgets = tuple(int(x) for x in a.budgets.split(",") if x.strip())
        out = probe(a.probe, ranks, budgets)
        if a.json:
            json.dump(out, open(a.json, "w"), indent=1)
            print("WROTE", a.json)
        return 0
    if a.encode:
        os.makedirs(a.out, exist_ok=True)
        plans = [tuple(int(v) for v in p.split(":")) for p in a.plans.split(",") if p.strip()]
        rows = encode_all(a.encode, plans, a.out, spec_name=a.spec, geo_delta=a.geo_delta,
                          tag_prefix=a.tag,
                          layouts=tuple(x for x in a.layouts.split(",") if x.strip()))
        if a.json:
            json.dump(rows, open(a.json, "w"), indent=1)
            print("WROTE", a.json)
        return 0
    ap.error("--probe or --encode is required")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
