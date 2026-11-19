"""M1 / QFP analysis (CPU): equal-byte rate-distortion table + D1/D2/D3 verdicts.

Reuses the certified coverage protocol of ``audit_bound.py`` through
``rd_analyse.variant_drops`` (per split: ``q`` from the clean calibration views,
``drop = coverage(edited, dep) - coverage(clean, dep)``) and adds the three
registered M1 criteria from ``experiments/METHOD_PLAN.md`` section M1.4:

D1  coverage dominance  -- QFP loses >= 3.0 pp less coverage than the prune
                           baseline at >= 3 matched byte rates, paired CI excludes
                           0, and >= 3/4 assets agree in sign;
D2  fidelity not worse  -- at the same bytes PSNR must not trail the prune
                           baseline by more than 0.3 dB and SSIM/LPIPS must not
                           go the wrong way;
D3  a near-lossless shelf exists -- >= 2 rates where a QFP setting is within
                           1.0 pp of the unedited asset and within 0.3 dB of its
                           PSNR.

Byte accounting lives in ``qfp_rd.py``.  The manifest written by that script is
the preferred source of ``bytes_per_prim``/``psnr``/``ssim``/``lpips``; but the
byte price of a variant is a pure function of its *name* under the preregistered
byte model, so a lost manifest degrades to ``spec_rate()`` instead of blocking
the coverage judgement (regression: the fallback path once referenced an
undefined local and only the ``nobytes`` self-test exercised it).

``M3`` (section M3.4 of the plan) adds three further criteria on the same
measurements, so that the pruning baseline can be compared all the way out to
20x and the two SH levers (drop a band vs. drop a bit) can be compared at equal
bytes:

E1  universal dominance -- same table as D1 but evaluated on the rate points the
                           two curves actually share, with a 4/5 rate and 6/8
                           asset threshold;
E2  degree vs. bits     -- inside the 25-45 B window, compare the best
                           degree-truncated member against the best
                           bit-truncated one; >= 0.5 pp apart is a win,
                           anything smaller is "the two levers are equivalent";
E3  frontier above 8x   -- a member that is near-lossless (<= 1.0 pp, <= 0.3 dB)
                           at a compression ratio of at least 8x.
"""

import argparse
import json
import os
import re
import sys

import numpy as np


def _C():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import common as C
    return C


TARGET_RATES = (2.0, 3.0, 5.0, 7.0, 9.0, 12.0, 16.0, 24.0)
FAMILIES = ("iso", "qfp", "prune", "joint")
FIDELITY_KEYS = ("psnr", "ssim", "lpips")

#: D2 tolerances.  PSNR in dB (higher better), SSIM unitless (higher better),
#: LPIPS unitless (lower better).  These are "must not be worse than the baseline
#: by more than" bounds, not targets.
TOL = {"psnr": 0.3, "ssim": 0.005, "lpips": 0.02}

#: M3 thresholds, all copied from the preregistration (METHOD_PLAN.md, M3.4 and
#: the M3.4a amendment) so that changing one here is visibly a change of plan.
E2_WINDOW = (25.0, 45.0)     # bytes/prim where both SH levers are available
E2_GAP_PP = 0.5              # below this the two levers are called equivalent
E3_MIN_RATE = 8.0            # M2's D3 only asked for >= 2x
E3_MAX_DROP_PP = 1.0
E3_MAX_DPSNR = 0.3
DEGREE_RE = re.compile(r"^d([0-3])_")


def _need(n: int, frac: float = 0.75) -> int:
    """How many assets must agree: the plan's "6/8" expressed as a fraction."""
    return max(1, int(np.ceil(frac * max(1, int(n)))))


def truncation_kind(name: str) -> str:
    """``"degree"`` for ``d<k>_...`` variants, ``"bits"`` for the rest of QFP.

    The two SH levers delete different things (whole angular bands vs. the low
    bits of every coefficient), so E2 compares the best member of each kind
    inside the same byte window.
    """
    if DEGREE_RE.match(name.strip()):
        return "degree"
    return "bits" if family_of(name) == "qfp" else ""


def _e2_block(scenes, window=E2_WINDOW, gap_pp=E2_GAP_PP, frac: float = 0.75) -> dict:
    """Degree-truncation vs. bit-truncation at equal bytes (criterion E2)."""
    lo, hi = float(window[0]), float(window[1])
    per_scene, diffs = {}, []
    for sc in scenes:
        best = {"degree": None, "bits": None}
        for row in sc["rows"]:
            kind = truncation_kind(row["variant"])
            bpp = row.get("bytes_per_prim")
            if not kind or bpp is None or not (lo <= float(bpp) <= hi):
                continue
            if best[kind] is None or row["drop_pp"] > best[kind]["drop_pp"]:
                best[kind] = row
        entry = {k: (None if v is None else dict(variant=v["variant"],
                                                bytes_per_prim=v["bytes_per_prim"],
                                                drop_pp=v["drop_pp"]))
                 for k, v in best.items()}
        if best["degree"] is not None and best["bits"] is not None:
            diff = float(best["degree"]["drop_pp"]) - float(best["bits"]["drop_pp"])
            entry["diff_pp"] = diff          # > 0: dropping a band loses less
            diffs.append(diff)
        per_scene[sc["scene"]] = entry
    out = dict(window_bytes=[lo, hi], gap_pp=gap_pp, per_scene=per_scene,
               n_scenes_with_both=len(diffs), threshold_n=_need(len(scenes), frac))
    if diffs:
        arr = np.asarray(diffs, dtype=np.float64)
        mean = float(arr.mean())
        agree = int((np.sign(arr) == np.sign(mean)).sum()) if mean != 0 else 0
        if abs(mean) < gap_pp:
            winner = "equivalent"
        else:
            winner = "degree" if mean > 0 else "bits"
        out.update(mean_pp=mean, min_pp=float(arr.min()), max_pp=float(arr.max()),
                   n_agree=agree,
                   winner=winner,
                   verdict=bool(winner != "equivalent" and agree >= out["threshold_n"]))
    else:
        out.update(winner=None, n_agree=0, verdict=False)
    return out


def _e3_block(scenes, min_rate=E3_MIN_RATE, max_drop_pp=E3_MAX_DROP_PP,
              max_dpsnr=E3_MAX_DPSNR, frac: float = 0.75) -> dict:
    """Is there a near-lossless member at a high compression ratio (E3)?"""
    per_scene, hits = {}, 0
    for sc in scenes:
        members, frontier = [], None
        for row in sc["rows"]:
            dp = row.get("d_psnr")
            if dp is None or row["drop_pp"] < -max_drop_pp or float(dp) > max_dpsnr:
                continue
            rate = row.get("rate")
            if rate is None:
                continue
            frontier = max(frontier or 0.0, float(rate))
            if float(rate) >= float(min_rate):
                members.append(dict(variant=row["variant"], rate=float(rate),
                                    drop_pp=row["drop_pp"], d_psnr=float(dp)))
        members.sort(key=lambda m: m["rate"])
        per_scene[sc["scene"]] = dict(members=members, frontier_rate=frontier)
        hits += int(bool(members))
    need = _need(len(scenes), frac)
    return dict(min_rate=float(min_rate), max_drop_pp=max_drop_pp,
                max_dpsnr=max_dpsnr, assets_with_member=int(hits),
                threshold_assets=int(need), per_scene=per_scene,
                verdict=bool(hits >= need))


def family_of(name: str) -> str:
    """Family of one variant name (must agree with ``qfp_rd.QSpec.family``).

    Derived from the parsed spec rather than from substrings, so that a hybrid whose
    quantising token is not ``_q`` (``c12_`` cluster codes, ``d2_`` band truncation,
    ``m16_`` lattices) is still recognised as a joint variant.
    """
    s = name.strip()
    if s == "clean":
        return "clean"
    if s.startswith("iso_"):
        return "iso"
    keep, sh_bits, geo, deg_out, cbits, _vq, _rvq, _msc, _pq, st3 = parse_spec(s)
    is_prune = keep < 1.0
    is_quant = (sh_bits < 32 or deg_out is not None or cbits is not None
                or st3 is not None
                or any(int(b) < 32 for b in geo.values()))
    if is_prune and is_quant:
        return "joint"
    if is_prune:
        return "prune"
    if is_quant:
        return "qfp"
    return "clean"


# ---------------------------------------------------------------------------
# byte model, mirrored from qfp_rd without importing torch
# ---------------------------------------------------------------------------
GEO_SCALARS = {"means": 3, "scales": 3, "quats": 4, "opacities": 1}
SH_SCALE_BYTES = 2
#: cluster-relative position headers: mirror of ``qfp_rd.CLUSTER_*``
CLUSTER_SIZE = 256
CLUSTER_HEADER_BYTES = 24.0
CLUSTER_HEADER_PER_PRIM = CLUSTER_HEADER_BYTES / float(CLUSTER_SIZE)
FP32_BITS = 32
#: 8 B per coded component of a grid-coded attribute
SH_HDR_BYTES = 8.0
#: vector-quantised SH: one dictionary index per primitive, 8-bit centroids
SH_VQ_CENTROID_BYTES = 1
VQ_NOMINAL_PRIMS = 4_000_000
MSC_FLAG_BITS = 2


def rvq_codebook_bytes(bits1: int, bits2: int, cols: int) -> float:
    """Two-stage dictionary: both codebooks are part of the file."""
    return vq_codebook_bytes(bits1, cols) + vq_codebook_bytes(bits2, cols)


def vq_codebook_bytes(bits: int, cols: int) -> float:
    return float((1 << int(bits)) * int(cols) * SH_VQ_CENTROID_BYTES)
_GEO_ALIAS = {"means": "means", "scales": "scales", "quats": "quats",
              "opac": "opacities", "opacity": "opacities", "opacities": "opacities"}


def sh_cols(sh_degree: int) -> int:
    return 3 * (sh_degree + 1) ** 2


def fp32_bytes_per_prim(sh_degree: int) -> float:
    return float(sum(GEO_SCALARS.values()) * 4 + sh_cols(sh_degree) * 4)


def pq_bytes_per_prim(sh_degree: int, m: int, b: int, n_stored: int = None) -> float:
    """Same PQ model as ``qfp_rd.pq_bytes_per_prim``."""
    cols = sh_cols(sh_degree)
    return float(m * b) / 8.0 + (1 << b) * cols / float(n_stored or VQ_NOMINAL_PRIMS)


def msc_bytes_per_prim(sh_degree: int, b_dict: int, b_scalar: int,
                       frac=(0.0, 1.0, 0.0), n_stored: int = None) -> float:
    """Same mode-mix model as ``qfp_rd.msc_bytes_per_prim``."""
    cols = sh_cols(sh_degree)
    n = float(n_stored or VQ_NOMINAL_PRIMS)
    c_dict = b_dict / 8.0
    c_scalar = cols * b_scalar / 8.0 + SH_SCALE_BYTES
    tot = sum(frac) or 1.0
    f = [x / tot for x in frac]
    return float(MSC_FLAG_BITS / 8.0 + f[1] * c_dict + f[2] * c_scalar
                 + vq_codebook_bytes(b_dict, cols) / n)


def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None, sh_vq_bits: int = None,
                   n_stored: int = None, sh_rvq: tuple = None,
                   sh_msc: dict = None, sh_pq: tuple = None,
                   quat_st3: int = None) -> float:
    """Literal bytes per kept primitive: ``11*b_geo/8 + 3K*b_sh/8 (+2)``.

    ``means_cbits`` replaces the three position components by cluster-relative
    offsets at that width, which also pays one 24-byte header per 256 primitives.
    ``quat_st3`` mirrors ``qfp_rd``: smallest-three quaternions cost ``2 + 3*b`` bits,
    three coded components plus the index that carries the fourth's value and sign.
    """
    cols = sh_cols(sh_degree)
    if sh_pq is not None:
        b_sh = pq_bytes_per_prim(sh_degree, int(sh_pq[0]), int(sh_pq[1]), n_stored)
    elif sh_msc is not None:
        b_sh = msc_bytes_per_prim(sh_degree, int(sh_msc["b_dict"]),
                                  int(sh_msc["b_scalar"]), sh_msc.get("frac")
                                  or (0.0, 1.0, 0.0), n_stored)
    elif sh_rvq is not None:
        b1, b2 = int(sh_rvq[0]), int(sh_rvq[1])
        b_sh = (b1 + b2) / 8.0 + rvq_codebook_bytes(b1, b2, cols) / float(
            n_stored or VQ_NOMINAL_PRIMS)
    elif sh_vq_bits is not None:
        b_sh = int(sh_vq_bits) / 8.0 + vq_codebook_bytes(sh_vq_bits, cols) / float(
            n_stored or VQ_NOMINAL_PRIMS)
    elif sh_bits >= 32:
        b_sh = cols * 4.0
    else:
        b_sh = cols * sh_bits / 8.0 + SH_SCALE_BYTES
    b_geo = 0.0
    for a, n in GEO_SCALARS.items():
        if a == "means" and means_cbits is not None:
            b_geo += 3 * int(means_cbits) / 8.0 + CLUSTER_HEADER_PER_PRIM
            continue
        if a == "quats" and quat_st3 is not None:
            b_geo += (2 + 3 * int(quat_st3)) / 8.0
            continue
        b_geo += n * int(geo.get(a, 32)) / 8.0
    # one-off per-file side information, charged per stored primitive: 8 B per coded
    # component of every grid-coded geometry attribute, plus the SH ladder's two scales
    b_side = 0.0
    _head = (("means", 3), ("scales", 3), ("quats", 4), ("opacities", 1))
    for _a, _c in _head:
        if _a == "means" and means_cbits is not None:
            continue                      # cluster coding carries its own per-block origin/step
        if int(geo.get(_a, FP32_BITS)) >= FP32_BITS:
            continue
        if _a == "quats" and quat_st3 is not None:
            continue                      # smallest-three carries a selector stream instead
        b_side += 8.0 * _c
    _ladder = (sh_pq is None and sh_msc is None and sh_rvq is None
               and sh_vq_bits is None and sh_bits < FP32_BITS)
    if _ladder:
        b_side += SH_HDR_BYTES
    # per-file, not per-primitive: without a primitive count the model quotes
    # the payload rate; with one it quotes the file rate, headers included.
    b_side = 0.0 if n_stored is None else b_side / float(n_stored)
    return float(b_geo + b_sh + b_side)


def parse_spec(name: str):
    """``(keep, sh_bits, geo, sh_degree_out, means_cbits, vq, rvq, msc, pq, st3)``.

    Mirrors ``qfp_rd.parse_spec``; ``sh_degree_out`` is ``None`` when the variant
    keeps every stored band, which is the only case where the scene's own degree
    decides the byte count.  ``st3`` is the smallest-three quaternion width (M15's
    ``gp<bq>-<bs>-<bo>`` token), or ``None`` when quaternions use the uniform grid.
    """
    s = name.strip()
    if s == "clean":
        return 1.0, 32, {}, None, None, None, None, None, None, None
    deg_out = None
    if s[:1] == "d" and s[1:2].isdigit():
        k = 1
        while k < len(s) and s[k].isdigit():
            k += 1
        deg_out = int(s[1:k])
        if not 0 <= deg_out <= 3:
            raise ValueError(f"bad SH degree in {name}")
        s = s[k:].lstrip("_")
    if s.startswith("iso_") and deg_out is None:
        body = s[4:]
        for alias, attr in _GEO_ALIAS.items():
            if body.startswith(alias):
                return (1.0, 32, {attr: int(body[len(alias):])}, None,
                        None, None, None, None, None, None)
        raise ValueError(f"unknown iso group in {name}")
    if s.startswith("geo") and deg_out is None:
        return (1.0, 32, {a: int(s[3:]) for a in GEO_SCALARS}, None,
                None, None, None, None, None, None)
    # attribute ladder m<bm>_o<bo>_sh<bs>, optional p<kk>_ prefix
    rest, keep_l = s, 1.0
    if rest.startswith("p") and len(rest) > 1 and rest[1].isdigit():
        i = 1
        while i < len(rest) and rest[i].isdigit():
            i += 1
        keep_l = int(rest[1:i]) / 100.0
        rest = rest[i:].lstrip("_")
    if rest[:1] == "d" and rest[1:2].isdigit() and deg_out is None:
        k = 1
        while k < len(rest) and rest[k].isdigit():
            k += 1
        deg_out = int(rest[1:k])
        rest = rest[k:].lstrip("_")
    if ((rest[:1] in ("m", "c") and rest[1:2].isdigit())
            or (rest.startswith("vq") and rest[2:3].isdigit())
            or (rest.startswith("rvq") and rest[3:4].isdigit())
            or (rest.startswith("msc") and "-" in rest)
            or (rest.startswith("pq") and "-" in rest)
            or (rest.startswith("gp") and "-" in rest)):
        (geo_l, sh_l, cbits, vq_l, rvq_l, msc_l, pq_l,
         st3_l) = {}, 32, None, None, None, None, None, None
        seen = set()
        for tok in rest.split("_"):
            if not tok:
                continue
            if tok[0] == "m" and tok[1:].isdigit():
                geo_l["means"] = int(tok[1:])
                seen.add("m")
            elif tok[0] == "c" and tok[1:].isdigit():
                cbits = int(tok[1:])
                geo_l.pop("means", None)
                seen.add("m")
            elif tok[0] == "o" and tok[1:].isdigit():
                for a in ("scales", "quats", "opacities"):
                    geo_l[a] = int(tok[1:])
                seen.add("o")
            elif tok.startswith("gp") and tok.count("-") == 2:
                # M15 packed geometry: smallest-three quaternions + tight lattices on
                # the two smooth groups.  Mirrors ``qfp_rd``'s token exactly.
                p_q, p_s, p_o = tok[2:].split("-")
                st3_l = int(p_q)
                geo_l["scales"] = int(p_s)
                geo_l["opacities"] = int(p_o)
                seen.add("gp")
            elif tok.startswith("sh") and tok[2:].isdigit():
                sh_l = int(tok[2:])
                seen.add("sh")
            elif tok.startswith("vq") and tok[2:].isdigit():
                vq_l = int(tok[2:])
                seen.add("sh")
            elif tok.startswith("rvq") and "-" in tok:
                p, _, q = tok[3:].partition("-")
                rvq_l = (int(p), int(q))
                seen.add("sh")
            elif tok.startswith("pq") and "-" in tok:
                p, _, q = tok[2:].partition("-")
                pq_l = (int(p), int(q))
                seen.add("sh")
            elif tok.startswith("msc") and "-" in tok:
                parts = tok[3:].split("-")
                msc_l = {"b_dict": int(parts[0]), "b_scalar": int(parts[1]),
                         "alpha": int(parts[2].lstrip("a"))}
                seen.add("sh")
            else:
                raise ValueError(f"cannot parse ladder token {tok!r} of {name}")
        if "m" not in seen or not ({"sh", "gp"} & seen):
            raise ValueError(f"ladder form needs m|c and sh|gp groups: {name}")
        if vq_l is not None and sh_l < 32:
            raise ValueError(f"vq and sh are exclusive in {name}")
        if rvq_l is not None and (vq_l is not None or sh_l < 32):
            raise ValueError(f"rvq excludes both vq and sh in {name}")
        return (keep_l, sh_l, geo_l, deg_out, cbits, vq_l, rvq_l, msc_l, pq_l, st3_l)
    keep, sh_bits, geo, rest = 1.0, 32, {}, s
    if rest.startswith("p"):
        i = 1
        while i < len(rest) and rest[i].isdigit():
            i += 1
        keep = int(rest[1:i]) / 100.0
        rest = rest[i:]
    rest = rest.lstrip("_")
    if not rest:
        return keep, sh_bits, geo, deg_out, None, None, None, None, None, None
    if not (rest.startswith("q") or rest.startswith("sh")):
        raise ValueError(f"cannot parse quant part {rest!r} of {name}")
    rest = rest[1:] if rest.startswith("q") else rest[2:]
    j = 0
    while j < len(rest) and rest[j].isdigit():
        j += 1
    sh_bits = int(rest[:j])
    rest = rest[j:]
    if not rest.startswith("_g"):
        raise ValueError(f"expected _g<bits> in {name}")
    geo = {a: int(rest[2:]) for a in GEO_SCALARS}
    return keep, sh_bits, geo, deg_out, None, None, None, None, None, None


def spec_rate(name: str, sh_degree: int = 3, n_stored: int = None):
    """``(rate_vs_fp32, bytes_per_prim)`` from the name alone.

    ``sh_degree`` is the degree of the reference checkpoint; a variant that stores
    fewer bands is charged for the bands it actually stores, while the numerator
    stays the full fp32 checkpoint.
    """
    (keep, sh_bits, geo, deg_out, cbits, vq_bits, rvq_bits, msc_bits, pq_bits,
     st3) = parse_spec(name)
    deg = int(sh_degree if deg_out is None else min(deg_out, sh_degree))
    bpp = bytes_per_prim(deg, sh_bits, geo, means_cbits=cbits,
                         sh_vq_bits=vq_bits, n_stored=n_stored, sh_rvq=rvq_bits,
                         sh_msc=msc_bits, sh_pq=pq_bits, quat_st3=st3)
    return fp32_bytes_per_prim(sh_degree) / (bpp * keep), bpp


#: bytes per primitive the older ``m4_bytes`` runs did not charge for the two SH block scales
SCALE_BYTES_MISSING = 2.0


def load_measured_rates(path: str, sh_degree: int = 3) -> dict:
    """``{(scene, spec): {rate, bpp}}`` from an ``m4_bytes.json`` measurement.

    The measured format is the one we would actually ship: attributes bit-packed at
    the registered widths, primitives reordered by Morton code of their reconstructed
    position, streams compressed with zstd.  ``rate`` is therefore the *real*
    compression ratio against the fp32 checkpoint of the same scene, and ``bpp`` is
    the real cost of one stored primitive -- neither is read off the analytic model.
    """
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    out = {}
    for sc in doc.get("scenes", []):
        scene = sc.get("scene")
        n = int(sc.get("n") or 0)
        deg = int(sc.get("sh_degree", sh_degree) or sh_degree)
        if not scene or not n:
            continue
        fp32_total = n * fp32_bytes_per_prim(deg)
        for row in sc.get("rows", []):
            stored = int(row.get("stored") or 0)
            bpp = row.get("zstd_morton_bytes_per_prim")
            if not stored or bpp is None:
                continue
            bpp = float(bpp)
            spec = str(row.get("spec"))
            streams = row.get("streams") or {}
            # Measurements taken before the SH scale stream was charged report only the
            # coefficient payload; the shipping format also stores one byte per SH block
            # (the model charges SH_SCALE_BYTES for exactly that).  Charge it here so an
            # older measurement lands on the same axis, and record that we did.
            if streams and "sh_scale" not in streams:
                try:
                    (keep, sh_bits, _geo, _deg, _cb, _vq, _rvq, _msc, _pq,
                     _st3) = parse_spec(spec)
                    if sh_bits is not None and int(sh_bits) < 32:
                        bpp += SCALE_BYTES_MISSING
                except Exception:
                    pass
            out[(str(scene), spec)] = dict(
                rate=float(fp32_total) / (bpp * stored), bpp=bpp)
    return out


def _load_manifest(dump_dir: str):
    for fn in ("m1_manifest.json", "rd_manifest.json", "dump_summary.json"):
        p = os.path.join(dump_dir, fn)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return None


def _scene_variants(manifest, scene: str) -> dict:
    if not manifest:
        return {}
    for row in manifest.get("scenes", []):
        if row.get("scene") == scene:
            return row.get("variants") or {}
    return {}


def interp_points(points, target: float):
    """Interpolate vectors over ``(x, vector)`` points; never extrapolates."""
    pts = sorted([p for p in points if p[0] is not None], key=lambda t: t[0])
    if len(pts) < 2:
        return None, False
    xs = np.asarray([p[0] for p in pts], dtype=np.float64)
    ys = np.stack([np.asarray(p[1], dtype=np.float64) for p in pts], axis=0)
    covered = bool(xs.min() - 1e-9 <= target <= xs.max() + 1e-9)
    at = np.empty(ys.shape[1])
    for s in range(ys.shape[1]):
        at[s] = float(np.interp(target, xs, ys[:, s]))
    return at, covered


def interp_scalar(points, target: float):
    """Interpolate a scalar metric over ``(x, value)`` points; never extrapolates."""
    pts = sorted([p for p in points if p[1] is not None], key=lambda t: t[0])
    if len(pts) < 2:
        return None, False
    xs = np.asarray([p[0] for p in pts], dtype=np.float64)
    ys = np.asarray([float(p[1]) for p in pts], dtype=np.float64)
    covered = bool(xs.min() - 1e-9 <= target <= xs.max() + 1e-9)
    return float(np.interp(target, xs, ys)), covered


def _paired(d):
    return dict(mean_pp=100.0 * float(d.mean()),
                lo_pp=100.0 * float(np.percentile(d, 2.5)),
                hi_pp=100.0 * float(np.percentile(d, 97.5)),
                n_splits=int(d.size))


def analyse_dump(dump_dir: str, rates=TARGET_RATES, n_splits: int = 400,
                 alpha: float = None, verbose: bool = True, seed: int = 0,
                 rate_need: int = 3, agree_frac: float = 0.75,
                 protocol: str = "m1", bytes_json: str = None) -> dict:
    C = _C()
    import rd_analyse as R

    alpha = C.ALPHA if alpha is None else float(alpha)
    manifest = _load_manifest(dump_dir)
    measured = load_measured_rates(bytes_json) if bytes_json else {}
    paths = C.discover_npz(dump_dir)
    if not paths:
        raise SystemExit(f"no npz in {dump_dir}")

    scenes = []
    pooled = {r: {"d1": [], "d2": []} for r in rates}
    d3_hits = {r: [] for r in rates}

    for path in paths:
        sc = C.load_npz_scene(path)
        meta = sc["meta"]
        scene = meta.get("scene", os.path.basename(path)[:-4])
        names = [str(v) for v in sc["variant_names"]]
        var = _scene_variants(manifest, scene)
        resid = np.asarray(sc["resid"])
        m = resid.shape[1]
        deg_scene = int(meta.get("sh_degree", 3) or 3)
        # A degenerate configuration (e.g. a 1-bit min-max grid, whose qmax is 0)
        # renders NaN, and a NaN row would poison every pooled statistic it enters.
        # Drop such variants loudly instead of letting them ride along.
        finite = np.isfinite(resid).all(axis=(1, 2, 3))
        if not finite.all():
            bad = [names[i] for i in range(len(names)) if not finite[i]]
            if any(b == "clean" for b in bad):
                raise SystemExit(f"{scene}: the clean reference itself is non-finite")
            C.log(f"{scene}: dropping {len(bad)} non-finite variant(s) {bad}")
            keep_i = [i for i in range(len(names)) if finite[i]]
            names = [names[i] for i in keep_i]
            resid = resid[keep_i]
        splits = C.split_perms(m, n_splits, seed)
        drops, clean_cov, _qs, qarr = R.variant_drops(resid, names, splits, alpha)

        clean_psnr = (var.get("clean") or {}).get("psnr")
        # The manifest is a convenience: bytes/prim and the compression ratio are
        # pure functions of the variant *name* under the preregistered byte model,
        # so a lost or partial manifest must not block the primary judgement.  The
        # measurements (psnr/ssim/lpips) still come from the manifest; when they are
        # absent the fidelity criteria report "not covered" instead of guessing.
        missing = [n for n in names
                   if n != "clean" and (var.get(n) or {}).get("ratio_vs_fp32") is None]
        if missing and not measured:
            C.log(f"{scene}: manifest lacks byte accounting for {len(missing)} "
                  f"variant(s) (e.g. {missing[:3]}); deriving it from the names")

        def _rate_of(name):
            """Rate and bytes/prim of one variant: measured bytes win over the model."""
            got = measured.get((scene, name))
            if got:
                return got["rate"], got["bpp"]
            vm = var.get(name) or {}
            rate, bpp = vm.get("ratio_vs_fp32"), vm.get("bytes_per_prim")
            if rate is None:
                rate, bpp = spec_rate(name, deg_scene)
            return rate, bpp
        rows, fam_cov = [], {f: [] for f in FAMILIES}
        fam_fid = {f: {k: [] for k in FIDELITY_KEYS} for f in FAMILIES}
        for name in names:
            if name == "clean":
                continue
            fam = family_of(name)
            vm = var.get(name) or {}
            rate, bpp = _rate_of(name)
            d = drops[name]
            rows.append(dict(variant=name, family=fam,
                             bytes_per_prim=None if bpp is None else float(bpp),
                             rate=None if rate is None else float(rate),
                             drop_pp=100.0 * float(d.mean()),
                             drop_lo_pp=100.0 * float(np.percentile(d, 2.5)),
                             drop_hi_pp=100.0 * float(np.percentile(d, 97.5)),
                             psnr=vm.get("psnr"), ssim=vm.get("ssim"),
                             lpips=vm.get("lpips"),
                             d_psnr=None if (vm.get("psnr") is None or clean_psnr is None)
                             else float(clean_psnr) - float(vm["psnr"])))
            if fam not in FAMILIES or rate is None:
                continue
            fam_cov[fam].append((float(rate), d))
            for k in FIDELITY_KEYS:
                fam_fid[fam][k].append((float(rate), vm.get(k)))

        matched, comp = {}, {}
        for r in rates:
            matched[str(r)] = {}
            cov = {}
            for fam in FAMILIES:
                v, ok = interp_points(fam_cov[fam], r)
                if v is None:
                    continue
                cov[fam] = (v, ok)
                entry = dict(drop_pp=100.0 * float(v.mean()),
                             lo_pp=100.0 * float(np.percentile(v, 2.5)),
                             hi_pp=100.0 * float(np.percentile(v, 97.5)),
                             covered=bool(ok))
                for k in FIDELITY_KEYS:
                    entry[k] = interp_scalar(fam_fid[fam][k], r)[0]
                matched[str(r)][fam] = entry
            pr = cov.get("prune")
            qf = cov.get("qfp")
            if pr and qf and pr[1] and qf[1]:
                diff = qf[0] - pr[0]                    # >0: QFP loses less coverage
                entry = dict(coverage=_paired(diff),
                             nearest_qfp=_nearest(fam_cov["qfp"], r),
                             nearest_prune=_nearest(fam_cov["prune"], r))
                for k in FIDELITY_KEYS:
                    a = interp_scalar(fam_fid["qfp"][k], r)[0]
                    b = interp_scalar(fam_fid["prune"][k], r)[0]
                    entry[k] = None if (a is None or b is None) else \
                        dict(qfp=float(a), prune=float(b), diff=float(a) - float(b))
                comp[str(r)] = entry
                pooled[r]["d1"].append(100.0 * float(diff.mean()))
                if entry["psnr"] is not None:
                    pooled[r]["d2"].append(dict(
                        psnr=entry["psnr"]["diff"],
                        ssim=None if entry["ssim"] is None else entry["ssim"]["diff"],
                        lpips=None if entry["lpips"] is None else entry["lpips"]["diff"]))
            d3_hits[r].append(_near_lossless(names, drops, var, clean_psnr, r, deg_scene,
                                             rate_of=_rate_of))

        scenes.append(dict(scene=scene, n_views=int(m),
                           sh_degree=int(meta.get("sh_degree", 3) or 3),
                           clean_coverage=float(clean_cov.mean()),
                           q_mean=float(qarr.mean()), clean_psnr=clean_psnr,
                           # The clean row is the reference, not a variant, so its fidelity
                           # columns would otherwise never reach the json -- and an external
                           # comparison (M16's C1) needs clean SSIM/LPIPS as well as PSNR.
                           clean_ssim=None if not var.get("clean") else var["clean"].get("ssim"),
                           clean_lpips=None if not var.get("clean") else var["clean"].get("lpips"),
                           rows=rows, matched=matched, comparisons=comp))
        if verbose:
            C.log(f"  [{C.stamp()}] {scene}: clean cov {100 * clean_cov.mean():.1f}% "
                  f"q={qarr.mean():.4f} psnr={clean_psnr} variants={len(rows)}")
            for row in rows:
                C.log(f"    {row['variant']:12s} "
                      f"{'--' if row['rate'] is None else format(row['rate'], '6.2f')}x "
                      f"drop={row['drop_pp']:7.2f}pp "
                      f"PSNR={'-' if row['psnr'] is None else format(row['psnr'], '6.2f')}"
                      f" dPSNR={'-' if row['d_psnr'] is None else format(row['d_psnr'], '+7.3f')}"
                      f" ssim={row['ssim']} lpips={row['lpips']}")
            for r in rates:
                e = comp.get(str(r))
                if not e:
                    C.log(f"    rate {r:5.1f}x  (no matched prune/QFP pair)")
                    continue
                c = e["coverage"]
                C.log(f"    rate {r:5.1f}x  nearest QFP {e['nearest_qfp']:<12s} "
                      f"D1 {c['mean_pp']:+7.2f}pp [{c['lo_pp']:+6.2f},{c['hi_pp']:+6.2f}]")
                if e.get("psnr"):
                    C.log(f"                D2 dPSNR {e['psnr']['diff']:+8.4f} dB"
                          + (f"  dSSIM {e['ssim']['diff']:+8.5f}" if e.get("ssim") else "")
                          + (f"  dLPIPS {e['lpips']['diff']:+8.5f}" if e.get("lpips") else ""))

    summary = dict(n_scenes=len(scenes), rates=[float(r) for r in rates],
                   criteria={}, protocol=protocol)

    per_rate = {}
    for r in rates:
        arr = np.asarray(pooled[r]["d1"], dtype=np.float64)
        if arr.size == 0:
            per_rate[str(r)] = dict(n_scenes=0, passes=False)
            continue
        per_rate[str(r)] = dict(mean_pp=float(arr.mean()), min_scene_pp=float(arr.min()),
                                n_positive=int((arr > 0).sum()), n_scenes=int(arr.size))

    def _dominance(need_rates: int, frac: float, name_n: int) -> dict:
        """Count rates whose paired advantage clears 3 pp with a positive CI."""
        need = _need(name_n, frac)
        passing = {k: bool(v.get("n_scenes") and v["mean_pp"] >= 3.0
                           and v["min_scene_pp"] > 0 and v["n_positive"] >= need)
                   for k, v in per_rate.items()}
        n_ok = sum(passing.values())
        return dict(threshold_pp=3.0, threshold_rates_needed=int(need_rates),
                    rates_passing=int(n_ok), rates_total=len(rates),
                    threshold_assets_agree=int(need) if name_n else None,
                    verdict=bool(n_ok >= int(need_rates)),
                    passing_rates=[k for k, ok in passing.items() if ok],
                    per_rate=per_rate)

    # D1 is the M1 registration (3 of 8 rates, 3/4 assets); E1 is M3's stricter
    # reading of the same table (4 of the 5 shared rates, 6/8 assets).
    summary["criteria"]["D1_coverage_dominance"] = _dominance(3, 0.75, len(scenes))
    summary["criteria"]["E1_universal_dominance"] = _dominance(rate_need, agree_frac,
                                                               len(scenes))

    per_rate2, n_ok2 = {}, 0
    for r in rates:
        vals = pooled[r]["d2"]
        if not vals:
            per_rate2[str(r)] = dict(n_scenes=0, passes=False)
            continue
        psnr = np.asarray([v["psnr"] for v in vals], dtype=np.float64)
        ssim = [v["ssim"] for v in vals if v["ssim"] is not None]
        lpips = [v["lpips"] for v in vals if v["lpips"] is not None]
        need = 2 if psnr.size >= 4 else int(psnr.size)
        ok_psnr = bool(int((psnr >= -TOL["psnr"]).sum()) >= need)
        ok_ssim = (not ssim) or bool(int((np.asarray(ssim) >= -TOL["ssim"]).sum()) >= need)
        ok_lpips = (not lpips) or bool(int((np.asarray(lpips) <= TOL["lpips"]).sum()) >= need)
        ok = bool(ok_psnr and ok_ssim and ok_lpips)
        per_rate2[str(r)] = dict(min_dPSNR=float(psnr.min()), mean_dPSNR=float(psnr.mean()),
                                 min_dSSIM=float(np.min(ssim)) if ssim else None,
                                 max_dLPIPS=float(np.max(lpips)) if lpips else None,
                                 n_scenes=int(psnr.size), passes=ok)
        n_ok2 += int(ok)
    summary["criteria"]["D2_fidelity_not_worse"] = dict(
        tol=TOL, rates_passing=int(n_ok2), rates_total=len(rates),
        threshold_rates_needed=3, verdict=bool(n_ok2 >= 3), per_rate=per_rate2)

    shelf, n_shelf = {}, 0
    for r in rates:
        hits = [h for h in d3_hits[r] if h is not None]
        shelf[str(r)] = [dict(scene=scenes[i]["scene"], variant=h[0], drop_pp=h[1],
                              d_psnr=h[2])
                         for i, h in enumerate(d3_hits[r]) if h is not None]
        need = 2 if len(scenes) >= 4 else len(scenes)
        if len(hits) >= need:
            n_shelf += 1
    summary["criteria"]["D3_near_lossless_shelf"] = dict(
        max_drop_pp=1.0, max_dpsnr=0.3, rates_with_shelf=int(n_shelf),
        threshold_rates_needed=2, verdict=bool(n_shelf >= 2), per_rate=shelf)

    summary["criteria"]["E2_degree_vs_bits"] = _e2_block(scenes, frac=agree_frac)
    summary["criteria"]["E3_frontier_above_8x"] = _e3_block(scenes, frac=agree_frac)

    crit = summary["criteria"]
    d1 = crit["D1_coverage_dominance"]["verdict"]
    d2 = crit["D2_fidelity_not_worse"]["verdict"]
    d3 = crit["D3_near_lossless_shelf"]["verdict"]
    e1 = crit["E1_universal_dominance"]["verdict"]
    e3 = crit["E3_frontier_above_8x"]["verdict"]
    if protocol == "m3":
        # The M3 outcome table: E1 decides, E3 only upgrades the claim.
        summary["outcome"] = ("m3_dominance_and_frontier" if (e1 and e3)
                              else "m3_dominance_only" if e1
                              else "regress_to_m1_claims")
    else:
        summary["outcome"] = ("method_holds" if (d1 and d2 and d3)
                              else "coverage_only" if d1 else "dead_write_N14")
    return dict(meta=dict(npz=os.path.abspath(dump_dir), alpha=alpha, n_splits=n_splits,
                          seed=seed,
                          note="equal-byte RD; coverage paired by split; no extrapolation",
                          manifest="m1_manifest.json" if manifest else None,
                          rate_source="measured" if measured else "model",
                          bytes_json=os.path.abspath(bytes_json) if bytes_json else None,
                          n_measured=len(measured)),
                scenes=scenes, summary=summary)


def _nearest(points, target: float) -> str:
    """Rate label of the member closest to ``target`` (naming only, not a curve)."""
    if not points:
        return ""
    x = min((p[0] for p in points), key=lambda v: abs(v - target))
    return f"{x:.2f}x"


def _near_lossless(names, drops, var, clean_psnr, r, deg_scene: int = 3, rate_of=None):
    """Best QFP setting within 12 % of ``r`` that is still near-lossless, if any."""
    best = None
    for name in names:
        if family_of(name) != "qfp":
            continue
        vm = var.get(name) or {}
        if rate_of is not None:
            rate = rate_of(name)[0]
        else:
            rate = vm.get("ratio_vs_fp32")
            if rate is None:
                # Same fallback as the row builder: the price is in the name.
                rate, _ = spec_rate(name, deg_scene)
        if rate is None or abs(float(rate) - r) > 0.12 * r:
            continue
        drop = 100.0 * float(drops[name].mean())
        dp = (None if (vm.get("psnr") is None or clean_psnr is None)
              else float(clean_psnr) - float(vm["psnr"]))
        if drop >= -1.0 and (dp is None or dp <= 0.3):
            if best is None or drop > best[1]:
                best = (name, drop, dp)
    return best


def _summarise(res: dict) -> dict:
    out = dict(outcome=res["summary"]["outcome"], n_scenes=res["summary"]["n_scenes"],
               criteria=res["summary"]["criteria"], scenes=[])
    for sc in res["scenes"]:
        rows = [dict(variant=r["variant"], family=r["family"], rate=r["rate"],
                     drop_pp=round(r["drop_pp"], 2),
                     d_psnr=None if r["d_psnr"] is None else round(r["d_psnr"], 3),
                     ssim=None if r["ssim"] is None else round(r["ssim"], 4),
                     lpips=None if r["lpips"] is None else round(r["lpips"], 4))
                for r in sc["rows"]]
        out["scenes"].append(dict(scene=sc["scene"], clean_coverage=sc["clean_coverage"],
                                  clean_psnr=sc["clean_psnr"], rows=rows,
                                  comparisons=sc["comparisons"]))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="M1/QFP equal-byte RD analysis")
    ap.add_argument("--dump", default="/workspace/res/m1/dump")
    ap.add_argument("--out", default=None)
    ap.add_argument("--rates", default=",".join(f"{r:g}" for r in TARGET_RATES))
    ap.add_argument("--n-splits", type=int, default=400)
    ap.add_argument("--alpha", type=float, default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--protocol", default="m1", choices=("m1", "m3"),
                    help="m1: verdict from D1/D2/D3; m3: from E1/E3 (M3.4 table)")
    ap.add_argument("--rate-need", type=int, default=3,
                    help="E1: how many of the evaluated rates must pass (M3: 4)")
    ap.add_argument("--agree-frac", type=float, default=0.75,
                    help="E1/E2/E3: fraction of assets that must agree (6/8 = 0.75)")
    ap.add_argument("--bytes-json", default=None,
                    help="m4_bytes.json: use measured (zstd+morton) bytes as the rate "
                         "axis instead of the analytic byte model")
    ap.add_argument("--selftest", action="store_true")
    return ap


def main(argv=None) -> int:
    C = _C()
    args = build_parser().parse_args(argv)
    if args.selftest:
        return selftest()
    rates = tuple(float(x) for x in args.rates.split(",") if x.strip())
    res = analyse_dump(args.dump, rates=rates, n_splits=args.n_splits,
                       alpha=args.alpha, verbose=True, seed=args.seed,
                       rate_need=args.rate_need, agree_frac=args.agree_frac,
                       protocol=args.protocol, bytes_json=args.bytes_json)
    out = args.out or os.path.join(args.dump, "m1_rd.json")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    C.json_dump(out, res)
    C.json_dump(out[:-5] + "_digest.json", _summarise(res))
    c = res["summary"]["criteria"]
    C.log("=" * 70)
    C.log(f"outcome: {res['summary']['outcome']}  (protocol {args.protocol})")
    C.log(f"  D1 coverage dominance : verdict={c['D1_coverage_dominance']['verdict']} "
          f"({c['D1_coverage_dominance']['rates_passing']}/{len(rates)} rates)")
    C.log(f"  D2 fidelity not worse : verdict={c['D2_fidelity_not_worse']['verdict']} "
          f"({c['D2_fidelity_not_worse']['rates_passing']}/{len(rates)} rates)")
    C.log(f"  D3 near-lossless shelf: verdict={c['D3_near_lossless_shelf']['verdict']} "
          f"({c['D3_near_lossless_shelf']['rates_with_shelf']}/{len(rates)} rates)")
    e1 = c["E1_universal_dominance"]
    C.log(f"  E1 universal dominance: verdict={e1['verdict']} "
          f"({e1['rates_passing']}/{len(rates)} rates, need {e1['threshold_rates_needed']}; "
          f"passing {e1['passing_rates']})")
    e2 = c["E2_degree_vs_bits"]
    C.log(f"  E2 degree vs. bits    : winner={e2['winner']} "
          f"mean={e2.get('mean_pp')} pp agree={e2['n_agree']}/{e2['n_scenes_with_both']}")
    e3 = c["E3_frontier_above_8x"]
    C.log(f"  E3 frontier >= {e3['min_rate']:g}x  : verdict={e3['verdict']} "
          f"({e3['assets_with_member']}/{res['summary']['n_scenes']} assets, "
          f"need {e3['threshold_assets']})")
    C.log(f"WROTE {out}")
    return 0


# ---------------------------------------------------------------------------
# self-test: synthetic dump with a known ordering, no GPU
# ---------------------------------------------------------------------------


def selftest() -> int:
    C = _C()
    import qfp_rd

    fails = []

    def check(name, cond, detail=""):
        C.log(f"  [{'ok' if cond else 'FAIL'}] {name} {detail}")
        if not cond:
            fails.append(name)

    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts", "_m1_selftest")
    qfp_rd._write_synth_dump(d, flip=False)
    res = analyse_dump(d, rates=(2.0, 3.0, 5.0), n_splits=40, verbose=False)
    c = res["summary"]["criteria"]
    check("D1 true on synthetic ordering", c["D1_coverage_dominance"]["verdict"],
          json.dumps({k: round(v.get("mean_pp", 0), 2)
                      for k, v in c["D1_coverage_dominance"]["per_rate"].items()}))
    check("D2 true (fidelity not worse)", c["D2_fidelity_not_worse"]["verdict"],
          json.dumps({k: v.get("min_dPSNR") for k, v in c["D2_fidelity_not_worse"]["per_rate"].items()}))
    check("D3 shelf found", c["D3_near_lossless_shelf"]["rates_with_shelf"] >= 2,
          str(c["D3_near_lossless_shelf"]["rates_with_shelf"]))
    check("outcome method_holds", res["summary"]["outcome"] == "method_holds",
          res["summary"]["outcome"])
    fams = {r["family"] for r in res["scenes"][0]["rows"]}
    check("families present", fams == {"qfp", "prune", "joint", "iso"}, str(sorted(fams)))
    check("comparisons are paired and non-extrapolated",
          all(v["coverage"]["n_splits"] == 40 for v in res["scenes"][0]["comparisons"].values()))

    d2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts", "_m1_selftest_flip")
    qfp_rd._write_synth_dump(d2, flip=True)
    res2 = analyse_dump(d2, rates=(2.0, 3.0, 5.0), n_splits=40, verbose=False)
    check("D1 false when pruning wins",
          not res2["summary"]["criteria"]["D1_coverage_dominance"]["verdict"],
          json.dumps({k: round(v.get("mean_pp", 0), 2)
                      for k, v in res2["summary"]["criteria"]["D1_coverage_dominance"]["per_rate"].items()}))
    check("outcome dead on flipped world", res2["summary"]["outcome"] == "dead_write_N14",
          res2["summary"]["outcome"])

    # A lost manifest must not block the coverage judgement: the byte price is a
    # pure function of the variant name.  (Regression: the fallback path once
    # referenced an undefined local and only this case exercises it.)
    d3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts", "_m1_selftest_nobytes")
    qfp_rd._write_synth_dump(d3, flip=False)
    mp = os.path.join(d3, "m1_manifest.json")
    with open(mp, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    for scene in doc.get("scenes", []):
        for vm in (scene.get("variants") or {}).values():
            vm.pop("ratio_vs_fp32", None)
            vm.pop("bytes_per_prim", None)
    with open(mp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    res3 = analyse_dump(d3, rates=(2.0, 3.0, 5.0), n_splits=40, verbose=False)
    rates_seen = [r["rate"] for r in res3["scenes"][0]["rows"]]
    check("rates survive a manifest without byte accounting",
          all(x is not None for x in rates_seen) and len(rates_seen) == len([r for r in rates_seen]),
          f"{sum(x is None for x in rates_seen)} missing of {len(rates_seen)}")
    check("verdict unchanged when bytes are derived from names",
          res3["summary"]["outcome"] == res["summary"]["outcome"],
          f"{res3['summary']['outcome']} vs {res['summary']['outcome']}")

    # ---- measured bytes replace the analytic model on the rate axis ---------
    # The measurement says every variant stores 2x fewer bytes than the model
    # charges, so every rate must double (and the rate_source must say so).
    scene0 = res["scenes"][0]["scene"]
    deg0 = res["scenes"][0]["sh_degree"]
    mj = os.path.join(d, "m4_like.json")
    rows_m = []
    for row in res["scenes"][0]["rows"]:
        rate_model = row["rate"]
        fp32 = fp32_bytes_per_prim(deg0)
        keep = parse_spec(row["variant"])[0]
        bpp = fp32 / (rate_model * keep)
        rows_m.append(dict(spec=row["variant"], keep=keep, stored=1000,
                           n=1000, model_bytes_per_prim=bpp * keep,
                           zstd_morton_bytes_per_prim=bpp / 2.0))
    with open(mj, "w", encoding="utf-8") as fh:
        json.dump(dict(scenes=[dict(scene=scene0, n=1000, sh_degree=deg0, rows=rows_m)]), fh)
    meas = load_measured_rates(mj)
    probe = next(iter(meas.values()))
    check("load_measured_rates reads a rate and a bpp per (scene, spec)",
          len(meas) == len(rows_m) and probe["rate"] > 1.0 and probe["bpp"] > 0.0,
          f"{len(meas)} entries")
    res5 = analyse_dump(d, rates=(4.0, 6.0, 10.0), n_splits=40, verbose=False,
                        bytes_json=mj)
    got = {r["variant"]: r["rate"] for r in res5["scenes"][0]["rows"]}
    want = {r["variant"]: round(meas[(scene0, r["variant"])]["rate"], 6)
            for r in res5["scenes"][0]["rows"]}
    check("measured rates override the model on the analysed rows",
          all(abs(got[k] - want[k]) < 1e-6 for k in want),
          f"{sum(abs(got[k] - want[k]) > 1e-6 for k in want)} mismatch")
    check("meta records where the rate axis came from",
          res5["meta"]["rate_source"] == "measured"
          and res5["meta"]["n_measured"] == len(rows_m),
          f"{res5['meta']['rate_source']} n={res5['meta']['n_measured']}")

    # A variant that renders NaN (1-bit min-max grid) must be dropped, not pooled.
    import numpy as np
    d4 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts", "_m1_selftest_nan")
    qfp_rd._write_synth_dump(d4, flip=False)
    npz = os.path.join(d4, "synth.npz")
    with np.load(npz, allow_pickle=True) as z:
        blob = {k: z[k] for k in z.files}
    blob["resid"] = np.array(blob["resid"], dtype=np.float32)
    _bad = [i for i, n in enumerate(blob["variant_names"]) if str(n) != "clean"][0]
    blob["resid"][_bad] = np.nan                    # one non-reference variant -> NaN
    np.savez_compressed(npz, **blob)
    res4 = analyse_dump(d4, rates=(2.0, 3.0, 5.0), n_splits=40, verbose=False)
    seen = {r["variant"] for r in res4["scenes"][0]["rows"]}
    check("NaN variant is dropped from the rows", len(seen) == len(res["scenes"][0]["rows"]) - 1,
          f"{len(seen)} rows, expected {len(res['scenes'][0]['rows']) - 1}")

    # ---- E2 / E3: unit tests on fabricated rows (no dump needed) ------------
    def _row(name, bpp, drop, d_psnr=None, rate=None):
        return dict(variant=name, family=family_of(name), bytes_per_prim=bpp,
                    drop_pp=drop, d_psnr=d_psnr, rate=rate)

    def _scene(tag, deg_drop, bit_drop, deg_dpsnr=0.2, deg_rate=9.44):
        # One degree-truncated and one bit-truncated member inside 25-45 B; the
        # pruner sits outside the window and must never be picked by E2.
        return dict(scene=tag, rows=[
            _row("d1_m16_o8_sh4", 22.0, deg_drop - 9.0, deg_dpsnr, deg_rate),
            _row("d2_m16_o8_sh8", 43.0, deg_drop, deg_dpsnr, deg_rate),
            _row("m16_o8_sh3", 36.0, bit_drop, max(deg_dpsnr, 0.0) + 0.1, 6.94),
            _row("m16_o8_sh4", 40.0, bit_drop - 1.0, 0.8, 5.90),
            _row("p50", 118.0, -9.0, 3.0, 2.00),
        ])

    four = [_scene(f"s{i}", -0.5, -2.0) for i in range(4)]
    e2 = _e2_block(four)
    check("E2 picks the degree winner when it loses less coverage",
          e2["winner"] == "degree" and e2["verdict"] and abs(e2["mean_pp"] - 1.5) < 1e-9,
          f"winner={e2['winner']} mean={e2.get('mean_pp')} agree={e2['n_agree']}")
    check("E2 never compares against the pruner outside the window",
          all(v["bits"]["variant"] in ("m16_o8_sh3", "m16_o8_sh4")
              for v in e2["per_scene"].values()), "")
    e2b = _e2_block([_scene(f"s{i}", -2.0, -0.5) for i in range(4)])
    check("E2 flips to bits when the bit-truncated member is better",
          e2b["winner"] == "bits" and e2b["verdict"], e2b["winner"])
    e2c = _e2_block([_scene(f"s{i}", -1.0, -1.2) for i in range(4)])
    check("E2 calls a < 0.5 pp gap equivalent, not a win",
          e2c["winner"] == "equivalent" and not e2c["verdict"],
          f"winner={e2c['winner']} mean={e2c.get('mean_pp')}")

    e3 = _e3_block(four)
    check("E3 finds a near-lossless member above 8x",
          e3["verdict"] and e3["assets_with_member"] == 4,
          f"{e3['assets_with_member']}/{len(four)}")
    e3b = _e3_block([_scene(f"s{i}", -0.5, -2.0, deg_dpsnr=0.5) for i in range(4)])
    check("E3 rejects a member that is 0.5 dB off even at 9.4x",
          not e3b["verdict"] and e3b["assets_with_member"] == 0,
          f"{e3b['assets_with_member']}/{len(four)}")

    C.log("=" * 60)
    if fails:
        C.log(f"FAILED {len(fails)}: {fails}")
        return 1
    C.log("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
