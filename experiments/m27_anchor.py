"""M27 -- anchors: attributes shared by a voxel, not carried by every primitive.

The mid-rate row is representation-bound (M26, N33): a fixed set of Gaussians that each carry their own
mean, rotation, scale, opacity and 45 coefficients costs ~16 B at the rate where HAC and PCGS sit 4 dB
above us.  Their files are cheap because a *voxel* pays for the attributes once and its members pay only
an offset plus a little colour.  This module is the cheapest version of that idea that keeps our own
container and decoder honest:

* primitives are grouped into voxels (edge chosen so a voxel holds ``target_ppa`` of them);
* the voxel pays for one position, one rotation, one scale triple, one opacity and one rest-colour
  vector (rank-16 basis, the M22 coder);
* each primitive pays a 3-bit offset inside its voxel and its own DC -- the base colour really is
  per-primitive, and 3 bits of it is what the shelf already spends.

Nothing is trained and no network is introduced: this answers "how many decibels does sharing cost"
before "how many would a decoder buy back".  If sharing is cheap, the budget identity that made the
20-30 MB row unwinnable (N25-N27) moves by a factor of four.
"""

from __future__ import annotations

import argparse
import json
import os

import numpy as np

import m4_bytes as M
import m19_codec as C
import geom_pack as GP
import m22_basis as B

OFFSET_BITS = 3  #: 8 levels per axis inside a voxel


# ----------------------------------------------------------------------------- grouping

def _key(ij: np.ndarray, side: int = 2048) -> np.ndarray:
    """One int64 per voxel so grouping is a 1-D sort instead of an ``axis=0`` unique.

    ``np.unique(..., axis=0)`` sorts rows and costs minutes on six million primitives; a linear key
    does the same job in seconds.  2048 levels per axis covers any voxel grid a 24-bit position
    quantiser can represent.
    """
    return (ij[:, 0] * side + ij[:, 1]) * side + ij[:, 2]


def voxel_size_for(means: np.ndarray, target_ppa: float = 8.0, iters: int = 10) -> float:
    """Voxel edge that puts ``target_ppa`` primitives in the average occupied voxel.

    A density estimate brackets the answer, then the bracket is *checked* by expanding it until it
    really contains the target -- the first version of this function trusted the estimate and
    returned a voxel ten times too coarse, which quietly turned a ``ppa = 8`` sweep into a
    ``ppa = 85`` one (every container 2.5x smaller and unusable, with no error anywhere).
    """
    mn = means.min(axis=0)
    span = np.maximum(means.max(axis=0) - mn, 1e-6)
    vol = float(np.prod(span))
    guess = (vol * max(target_ppa, 1.0) / max(1, len(means))) ** (1.0 / 3.0)

    def ppa_at(edge: float) -> float:
        ij = np.floor((means - mn) / edge).astype(np.int64)
        return len(means) / max(1, int(np.unique(_key(ij)).shape[0]))

    lo = hi = None
    edge = guess
    for _ in range(24):
        p = ppa_at(edge)
        if p > target_ppa:
            hi = edge
            edge *= 0.6
            if lo is not None:
                break
        else:
            lo = edge
            edge *= 1.6
            if hi is not None:
                break
    if lo is None:
        lo = edge * 0.6
    if hi is None:
        hi = edge * 1.6
    if hi < lo:
        lo, hi = hi, lo
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if ppa_at(mid) > target_ppa:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def group(means: np.ndarray, voxel: float):
    """Primitives sorted by voxel, plus the occupied voxel indices and per-voxel counts.

    Anchors sit at the *centre* of their voxel rather than at the mean of their members: the centre
    is a grid point the decoder can rebuild from the index alone (no stored float), and it bounds the
    member offset to ``+-voxel/2`` instead of ``+-voxel``, which halves the position error at the
    same 3-bit offset.
    """
    mn = means.min(axis=0)
    ij = np.floor((means - mn) / voxel).astype(np.int64)
    key = _key(ij)
    uniq_key, inv = np.unique(key, return_inverse=True)
    inv = inv.reshape(-1)
    order = np.argsort(inv, kind="stable")
    inv = inv[order]
    counts = np.bincount(inv, minlength=int(uniq_key.shape[0])).astype(np.int64)
    starts = np.concatenate([[0], np.cumsum(counts)[:-1]])
    #: recover the three indices of each occupied voxel from its key (same order as ``uniq_key``)
    side = 2048
    i = uniq_key // (side * side)
    rest = uniq_key % (side * side)
    j = rest // side
    l = rest % side
    vox = np.stack([i, j, l], axis=1).astype(np.int64)
    return order, starts, counts, vox, mn.astype(np.float32)


def _quant(v: np.ndarray, bits: int):
    v = np.asarray(v, dtype=np.float32)
    mn = v.min(axis=0)
    step = (v.max(axis=0) - mn) / max(1, (1 << bits) - 1)
    step = np.where(step > 0, step, np.float32(1.0)).astype(np.float32)
    codes = np.clip(np.round((v - mn) / step), 0, (1 << bits) - 1).astype(np.int64)
    return codes, mn.astype(np.float32), step


def _deg_from_cols(cols: int) -> int:
    k = cols // 3
    return int(round((k + 1) ** 0.5 - 1))


# ----------------------------------------------------------------------------- encoding

def _get(obj, key: str, default=None):
    """Attribute or key, whichever the caller's container uses (dict or ``SimpleNamespace``)."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def encode(splats: dict, spec_name: str = "c10_o8_sh3", target_ppa: float = 8.0, rank: int = 16,
           bits_total: int = 48, level: int = 12, path: str = None, pos_bits: int = 10,
           attr_bits: int = 8, dc_bits: int = 6, offset_bits: int = OFFSET_BITS,
           share_scale: bool = True, share_quat: bool = True, share_opacity: bool = True,
           share_rest: bool = True) -> tuple:
    """Write an anchor container for ``splats``; returns ``(meta, streams, path)``."""
    means = np.asarray(_get(splats, "means"), dtype=np.float32)
    n = means.shape[0]
    sh = _get(splats, "sh", None)
    sh0 = _get(sh, "sh0") if sh is not None else _get(splats, "sh0")
    shn = _get(sh, "shN") if sh is not None else _get(splats, "shN")
    voxel = voxel_size_for(means, target_ppa)
    order, starts, counts, vox, org = group(means, voxel)
    #: the count stream is uint16; a voxel that holds more primitives than that has to grow
    while counts.max() > 65000:
        voxel *= 1.5
        order, starts, counts, vox, org = group(means, voxel)
    na = int(vox.shape[0])
    a_means = org[None, :] + (vox.astype(np.float32) + 0.5) * np.float32(voxel)
    pos_bits = int(max(1, np.ceil(np.log2(max(2, int(vox.max()) + 1)))))

    rest_all = np.asarray(shn, dtype=np.float32).reshape(n, -1)
    dc_all = np.asarray(sh0, dtype=np.float32).reshape(n, 3)

    ofa = np.repeat(np.arange(int(vox.shape[0])), counts)

    def _mean(v):
        v = np.asarray(v, dtype=np.float64)[order]
        return (np.add.reduceat(v, starts, axis=0) / (counts[:, None] if v.ndim > 1 else counts))

    def _max(v):
        v = np.asarray(v, dtype=np.float64)[order]
        return np.maximum.reduceat(v, starts, axis=0)

    scales = np.log(np.maximum(np.asarray(_get(splats, "scales"), dtype=np.float64), 1e-12))
    #: opacity is averaged in *linear* space and turned back into a logit afterwards.  Averaging
    #: logits is an average of odds, which one opaque member drags to near-certainty: measured on
    #: bicycle it moved the median opacity of a voxel from 0.12 to 0.21 and cost most of a decibel.
    opac_lin = np.clip(np.asarray(_get(splats, "opacities"), dtype=np.float64).reshape(-1), 1e-6, 1 - 1e-6)
    quats = np.asarray(_get(splats, "quats"), dtype=np.float64)

    a_scale = _mean(scales)
    a_opac_lin = _mean(opac_lin)
    a_opac = np.log(a_opac_lin / (1 - a_opac_lin))

    #: quaternions have a double cover: ``q`` and ``-q`` are the same rotation, so a plain mean of a
    #: voxel whose members disagree about the sign lands near zero, and renormalising that is noise.
    #: Measured before the fix: mean |dot| 0.92, worst 0.00005 -- i.e. some anchors' rotations were
    #: simply random.  Align every member to the sign of the unnormalised mean first.
    q_o = quats[order]
    raw = np.add.reduceat(q_o, starts, axis=0)
    norm = np.linalg.norm(raw, axis=1, keepdims=True)
    ref = raw / np.maximum(norm, 1e-12)
    ref[norm[:, 0] < 1e-9] = np.array([1.0, 0.0, 0.0, 0.0])
    dot = (q_o * ref[ofa]).sum(axis=1)
    q_o = q_o * np.where(dot < 0.0, -1.0, 1.0)[:, None]
    a_quat = np.add.reduceat(q_o, starts, axis=0) / counts[:, None]
    a_quat /= np.maximum(np.linalg.norm(a_quat, axis=1, keepdims=True), 1e-12)

    st: dict = {}

    # positions: an anchor is a voxel index, a member is a 3-bit offset inside it
    st["a_vox"] = M.pack_bits(vox.reshape(-1), pos_bits)
    st["a_org"] = org.astype(np.float32).tobytes()

    off = means[order] - a_means[ofa]
    quantum = voxel / float(1 << int(offset_bits))
    ocode = np.clip(np.round((off + 0.5 * voxel) / quantum), 0,
                    (1 << int(offset_bits)) - 1).astype(np.int64)
    st["a_off"] = M.pack_bits(ocode.reshape(-1), int(offset_bits))
    st["a_count"] = counts.astype(np.uint16).tobytes()

    #: A shared attribute stores one value per voxel; an unshared one stores one per primitive.
    #: The switches exist because the first measurement said the sharing cost 6-8 dB, and the
    #: question "which attribute cannot be shared" has to be answered before the representation is
    #: judged: an anchor grid whose *opacity* is constant inside a voxel is not the same object as
    #: one whose opacity is predicted from the offset.
    if share_scale:
        scodes, smn, sstep = _quant(a_scale, attr_bits)
        st["a_scale"] = M.pack_bits(scodes.reshape(-1), attr_bits)
        st["a_scale_hdr"] = np.concatenate([smn, sstep]).astype(np.float32).tobytes()
    else:
        psc = scales[order]
        sc, smn, sstep = _quant(psc, attr_bits)
        st["p_scale"] = M.pack_bits(sc.reshape(-1), attr_bits)
        st["p_scale_hdr"] = np.concatenate([smn, sstep]).astype(np.float32).tobytes()

    if share_opacity:
        ocodes, omn, ostep = _quant(a_opac.reshape(-1, 1), attr_bits)
        st["a_opac"] = M.pack_bits(ocodes.reshape(-1), attr_bits)
        st["a_opac_hdr"] = np.concatenate([omn, ostep]).astype(np.float32).tobytes()
    else:
        pl = np.log(opac_lin[order] / (1 - opac_lin[order])).reshape(-1, 1)
        oc, omn, ostep = _quant(pl, attr_bits)
        st["p_opac"] = M.pack_bits(oc.reshape(-1), attr_bits)
        st["p_opac_hdr"] = np.concatenate([omn, ostep]).astype(np.float32).tobytes()

    if share_quat:
        qwhich, qabc = GP.st3_encode(a_quat, attr_bits)
        st["a_quat_which"] = M.pack_bits(np.asarray(qwhich, dtype=np.int64).reshape(-1), 2)
        st["a_quat_abc"] = M.pack_bits(np.asarray(qabc, dtype=np.int64).reshape(-1), attr_bits)
    else:
        pq = quats[order]
        qwhich, qabc = GP.st3_encode(pq, attr_bits)
        st["p_quat_which"] = M.pack_bits(np.asarray(qwhich, dtype=np.int64).reshape(-1), 2)
        st["p_quat_abc"] = M.pack_bits(np.asarray(qabc, dtype=np.int64).reshape(-1), attr_bits)

    # colour: per-primitive DC against a per-anchor level, rest shared through the M22 basis
    dc = dc_all[order]
    a_lvl = _max(np.abs(dc).max(axis=1)).astype(np.float32)
    lcodes, lmn, lstep = _quant(a_lvl.reshape(-1, 1), attr_bits)
    st["a_dc_lvl"] = M.pack_bits(lcodes.reshape(-1), attr_bits)
    st["a_dc_lvl_hdr"] = np.concatenate([lmn, lstep]).astype(np.float32).tobytes()

    qmax = (1 << (dc_bits - 1)) - 1
    lvl_prim = a_lvl[ofa][:, None]
    dcode = np.clip(np.round(dc / np.maximum(lvl_prim, 1e-8) * qmax), -qmax - 1, qmax).astype(np.int64)
    st["a_dc"] = M.pack_bits((dcode + (qmax + 1)).reshape(-1), dc_bits)

    a_rest = _mean(rest_all) if share_rest else np.asarray(rest_all, dtype=np.float32)[order]
    n_rest = int(a_rest.shape[0])
    f = B.fit(a_rest, rank)
    q = B.quantise_alloc(f["coef"], f["comp"], bits_total)
    st["a_basis"] = np.asarray(f["basis"], dtype=np.float32).tobytes()
    st["a_basis_mean"] = np.asarray(f["mean"], dtype=np.float32).reshape(-1).tobytes()
    st["a_coef_comp"] = np.asarray(f["comp"], dtype=np.float32).tobytes()
    st["a_coef_bits"] = np.asarray(q["bits"], dtype=np.uint8).tobytes()
    st["a_coef"] = B.pack_codes(q["codes"], q["bits"], "bits")

    cols = int(rest_all.shape[1])
    meta = {
        "n": int(n), "n_anchor": na, "spec": spec_name, "deg_out": _deg_from_cols(cols),
        "sh_rest_cols": cols, "voxel": float(voxel), "target_ppa": float(target_ppa),
        "rank": int(f["basis"].shape[0]), "offset_bits": int(offset_bits), "pos_bits": int(pos_bits),
        "attr_bits": int(attr_bits), "dc_bits": int(dc_bits), "anchor_mode": True,
        "sh_layout": "bits", "color": "anchor_basis", "ppa_measured": float(n / max(1, na)),
        "basis_energy": float(f["energy"]), "coef_bits": int(q["bits_total"]),
        "sh_scale_levels": 1, "n_rest": int(a_rest.shape[0]),
        "share": {"scale": bool(share_scale), "quat": bool(share_quat),
                  "opacity": bool(share_opacity), "rest": bool(share_rest)},
    }
    if path:
        C.write_container(path, st, meta, level=level)
    return meta, st, path


# ----------------------------------------------------------------------------- decoding

def decode(meta: dict, streams: dict) -> dict:
    """Rebuild the renderer tensors from an anchor container alone."""
    n = int(meta["n"])
    na = int(meta["n_anchor"])
    pb = int(meta.get("pos_bits", 10))
    ab = int(meta.get("attr_bits", 8))
    ob = int(meta.get("offset_bits", OFFSET_BITS))
    voxel = float(meta["voxel"])
    cols = int(meta["sh_rest_cols"])

    org = np.frombuffer(streams["a_org"], dtype=np.float32).reshape(-1)[:3]
    vox = C.unpack_bits(streams["a_vox"], pb, na * 3, dtype=np.uint16).reshape(na, 3)
    a_means = (org[None, :] + (vox.astype(np.float32) + np.float32(0.5))
               * np.float32(voxel)).astype(np.float32)

    counts = np.frombuffer(streams["a_count"], dtype=np.uint16).astype(np.int64)
    if int(counts.sum()) != n or counts.shape[0] != na:
        counts = np.full(na, max(1, n // max(1, na)), dtype=np.int64)
    ofa = np.repeat(np.arange(na), counts)[:n]

    ocode = C.unpack_bits(streams["a_off"], ob, n * 3, dtype=np.uint8).reshape(n, 3)
    step = np.float32(voxel / float(1 << ob))
    means = (a_means[ofa] + (ocode.astype(np.float32) - np.float32((1 << ob) - 1) / 2.0) * step)

    def _attr(name, dim):
        h = np.frombuffer(streams[f"a_{name}_hdr"], dtype=np.float32).reshape(-1, dim)
        c = C.unpack_bits(streams[f"a_{name}"], ab, na * dim, dtype=np.uint8).reshape(na, dim)
        return h[0] + c.astype(np.float32) * h[1]

    def _prim(name, dim):
        h = np.frombuffer(streams[f"p_{name}_hdr"], dtype=np.float32).reshape(-1, dim)
        c = C.unpack_bits(streams[f"p_{name}"], ab, n * dim, dtype=np.uint8).reshape(n, dim)
        return h[0] + c.astype(np.float32) * h[1]

    if "a_scale" in streams:
        scales = np.exp(_attr("scale", 3)[ofa]).astype(np.float32)
    else:
        scales = np.exp(_prim("scale", 3)).astype(np.float32)
    if "a_opac" in streams:
        a_opac = _attr("opac", 1).reshape(-1)
        opac = (1.0 / (1.0 + np.exp(-a_opac[ofa]))).astype(np.float32)
    else:
        opac = (1.0 / (1.0 + np.exp(-_prim("opac", 1).reshape(-1)))).astype(np.float32)
    if "a_quat_which" in streams:
        which = C.unpack_bits(streams["a_quat_which"], 2, na, dtype=np.uint8)
        abc = C.unpack_bits(streams["a_quat_abc"], ab, na * 3, dtype=np.uint8).reshape(na, 3)
        quats = np.asarray(GP.st3_decode(which, abc, ab), dtype=np.float32)[ofa]
    else:
        which = C.unpack_bits(streams["p_quat_which"], 2, n, dtype=np.uint8)
        abc = C.unpack_bits(streams["p_quat_abc"], ab, n * 3, dtype=np.uint8).reshape(n, 3)
        quats = np.asarray(GP.st3_decode(which, abc, ab), dtype=np.float32)

    lh = np.frombuffer(streams["a_dc_lvl_hdr"], dtype=np.float32).reshape(1, 2)
    lc = C.unpack_bits(streams["a_dc_lvl"], ab, na, dtype=np.uint8).astype(np.float32)
    a_lvl = (lh[0, 0] + lc * lh[0, 1])[:, None]
    dcb = int(meta.get("dc_bits", 3))
    qmax = (1 << (dcb - 1)) - 1
    dcode = C.unpack_bits(streams["a_dc"], dcb, n * 3, dtype=np.uint8).reshape(n, 3).astype(np.float32)
    sh_dc = (dcode - np.float32(qmax + 1)) / np.float32(qmax) * a_lvl[ofa]

    basis = np.frombuffer(streams["a_basis"], dtype=np.float32).reshape(-1, cols)
    vmean = np.frombuffer(streams["a_basis_mean"], dtype=np.float32)
    comp = np.frombuffer(streams["a_coef_comp"], dtype=np.float32)
    bits = np.frombuffer(streams["a_coef_bits"], dtype=np.uint8).astype(np.int64)
    n_rest = int(meta.get("n_rest", na))
    codes = B.unpack_codes(streams["a_coef"], bits, n_rest, str(meta.get("sh_layout", "bits")))
    coef = np.empty((n_rest, len(bits)), dtype=np.float32)
    for k, bj in enumerate(bits):
        stp = np.float32(2.0 / float(1 << int(bj)))
        coef[:, k] = (codes[k].astype(np.float32) + np.float32(0.5)) * stp - np.float32(1.0)
        coef[:, k] *= comp[k]
    rest_a = (coef @ basis + vmean).astype(np.float32)
    sh_rest = (rest_a[ofa] if rest_a.shape[0] == na else rest_a).reshape(n, -1, 3)

    return {"means": means.astype(np.float32), "scales": scales, "quats": quats,
            "opacities": opac, "sh_dc": sh_dc.astype(np.float32),
            "sh_rest": sh_rest.astype(np.float32)}


# ----------------------------------------------------------------------------- round trip

def _fake(seed: int = 0, n: int = 20000):
    rng = np.random.default_rng(seed)
    means = (rng.normal(size=(n, 3)) * 0.2).astype(np.float32)
    scales = np.exp((rng.normal(size=(n, 3)) * 0.3 - 1.0).astype(np.float32))
    q = rng.normal(size=(n, 4))
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    op = 1 / (1 + np.exp(-rng.normal(size=n)))
    sh0 = rng.normal(size=(n, 3)).astype(np.float32)
    rest = (rng.normal(size=(n, 45)) * 0.05).astype(np.float32)
    return {"means": means, "scales": scales, "quats": q.astype(np.float32), "opacities": op,
            "sh": {"sh0": sh0, "shN": rest.reshape(n, 15, 3)}}


def selftest() -> None:
    splats = _fake()
    meta, st, _ = encode(splats, target_ppa=8.0, rank=8, bits_total=32)
    out = decode(meta, st)
    for k in ("means", "scales", "quats", "opacities", "sh_dc", "sh_rest"):
        assert out[k].shape[0] == splats["means"].shape[0], (k, out[k].shape)
    assert out["sh_rest"].shape[1:] == (15, 3), out["sh_rest"].shape
    #: the container stores primitives grouped by anchor, so compare against the same permutation
    order = group(splats["means"], meta["voxel"])[0]
    err = float(np.abs(out["means"] - splats["means"][order]).max())
    assert err < 2.5 * meta["voxel"] / (1 << OFFSET_BITS), (err, meta["voxel"])
    assert 2.0 < meta["ppa_measured"] < 40.0, meta["ppa_measured"]
    print("m27 selftest ok  ppa=%.2f  mean err=%.4f  voxel=%.4f"
          % (meta["ppa_measured"], err, meta["voxel"]))


def main() -> int:
    ap = argparse.ArgumentParser(description="M27 anchor container")
    ap.add_argument("--ply")
    ap.add_argument("--out")
    ap.add_argument("--ppa", type=float, default=8.0)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--bits", type=int, default=48)
    ap.add_argument("--pos-bits", type=int, default=10)
    ap.add_argument("--attr-bits", type=int, default=8)
    ap.add_argument("--dc-bits", type=int, default=6)
    ap.add_argument("--offset-bits", type=int, default=OFFSET_BITS)
    ap.add_argument("--per-primitive", default="",
                    help="comma list of attributes to keep per primitive: scale,quat,opac,rest")
    ap.add_argument("--json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.ply or not a.out:
        ap.error("--ply and --out are required")
    import m20_model
    splats = m20_model.load_model(a.ply)
    keep = {x.strip() for x in a.per_primitive.split(",") if x.strip()}
    meta, st, _ = encode(splats, target_ppa=a.ppa, rank=a.rank, bits_total=a.bits,
                         pos_bits=a.pos_bits, attr_bits=a.attr_bits, dc_bits=a.dc_bits,
                         offset_bits=a.offset_bits, path=a.out,
                         share_scale="scale" not in keep, share_quat="quat" not in keep,
                         share_opacity="opac" not in keep, share_rest="rest" not in keep)
    size = os.path.getsize(a.out)
    n = int(meta["n"])
    row = {"file": a.out, "bytes": size, "n": n, "n_anchor": int(meta["n_anchor"]),
           "ppa": round(meta["ppa_measured"], 3), "b_per_prim": round(size / n, 3),
           "voxel": meta["voxel"], "rank": int(meta["rank"]), "bits": a.bits,
           "pos_bits": a.pos_bits, "attr_bits": a.attr_bits, "dc_bits": a.dc_bits, "offset_bits": a.offset_bits, "per_primitive": sorted(keep),
           "basis_energy": round(meta["basis_energy"], 5),
           "streams": {k: len(v) for k, v in st.items()}}
    print(json.dumps(row, indent=1))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(row, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
