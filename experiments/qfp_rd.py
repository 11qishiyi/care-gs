"""M1 / QFP: precision-first rate-distortion for 3DGS attributes.

The A-series established (``experiments/A4_RESULTS.md``, N13) that at *matched
bytes* spending bytes on coefficient precision beats spending them on primitive
count by 6-11 coverage points, and that a 4-bit SH grid is essentially free
(0.02-0.05 pp, -0.03 dB) while a 30 % Fisher prune (same 3.3x) costs 6.6-19.2 pp
and 4.2 dB.  That experiment, however, deliberately kept two things out of the
byte ledger: the 11 geometric scalars were treated as an incompressible fp32
44 B block, and the per-primitive SH scales were assumed free.  Both are real
bytes in a deployed codec, and both are exactly where a precision-first pipeline
can win more.

This script implements the M1 measurement (preregistered in
``experiments/METHOD_PLAN.md`` section M1):

    bytes/prim = 11*b_geo/8 + 3K*b_sh/8 + 2        (fp32 baseline = 236 B, K=16)

with a *scene-level exact min-max grid per attribute component* -- no
per-primitive scale table for geometry, so the ledger is literal.  ``quats`` are
renormalised after quantisation, ``scales`` are quantised in the log domain and
``opacities`` in the logit domain, which is the convention a real codec uses.

Variants (see ``DEFAULT_VARIANTS``): one ``clean`` anchor, eight single-group
probes, four all-geometry levels, seven SH levels at 16-bit geometry, five
candidate QFP settings, eight Fisher-prune baselines and three prune+quantise
hybrids.

Output is exactly the A4 npz layout (via ``dump_artifacts.pack_and_save``) so
``experiments/m1_analyse.py`` can reuse the certified coverage protocol
unchanged.
"""

import argparse
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field

import numpy as np


def _C():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import common as C
    return C


# ---------------------------------------------------------------------------
# byte model
# ---------------------------------------------------------------------------

#: scalar count per geometric attribute group (means 3 + scales 3 + quats 4 + opacity 1)
GEO_SCALARS = {"means": 3, "scales": 3, "quats": 4, "opacities": 1}
GEO_TOTAL = sum(GEO_SCALARS.values())          # 11
FP32_BITS = 32
#: two per-primitive SH scale factors (sh0 block, shN block) stored as 8-bit fixed point
SH_SCALE_BYTES = 2
#: cluster-relative position coding: primitives are cut into Morton-ordered blocks and
#: each block carries its own origin and per-component step.  The overhead is
#: ``CLUSTER_HEADER_BYTES`` per block, i.e. 3 fp32 origin + 3 fp32 step.
CLUSTER_SIZE = 256
CLUSTER_HEADER_BYTES = 24.0
CLUSTER_HEADER_PER_PRIM = CLUSTER_HEADER_BYTES / float(CLUSTER_SIZE)
#: per-file side information: the min/step pair of every mesh-coded geometry
#: attribute (float32) and, for the scalar SH ladder, the two block scales.
#: 8 B per coded component of a grid-coded attribute
SH_HDR_BYTES = 8.0
#: vector-quantised SH: every primitive stores an index into a per-asset codebook
#: instead of 48 independent coefficients.  Centroids are kept at 8 bit (one byte per
#: coefficient), so a codebook of ``2**b`` centres costs ``2**b * cols`` bytes and is
#: charged to the asset -- a dictionary that is not paid for is not a codec.
SH_VQ_CENTROID_BYTES = 1
#: only used to rebuild byte accounting when the asset is not at hand; the manifest
#: always carries the real primitive count, and that is what the analysis reads.
VQ_NOMINAL_PRIMS = 4_000_000


def vq_codebook_bytes(bits: int, cols: int) -> float:
    """Bytes of a codebook with ``2**bits`` centres of ``cols`` coefficients each."""
    return float((1 << int(bits)) * int(cols) * SH_VQ_CENTROID_BYTES)


def pq_codebook_bytes(m: int, b: int, cols: int) -> int:
    """One codebook per sub-vector, 8-bit centres: ``2**b`` centres over ``cols`` dims."""
    if cols % m:
        raise ValueError(f"{cols} coefficients do not split into {m} groups")
    return int((1 << b) * cols)


def pq_bytes_per_prim(m: int, b: int, n_stored: int, cols: int) -> float:
    """``m`` codes of ``b`` bits each, plus the amortised codebooks."""
    return float(m * b) / 8.0 + pq_codebook_bytes(m, b, cols) / float(
        n_stored or VQ_NOMINAL_PRIMS)


def rvq_codebook_bytes(bits1: int, bits2: int, cols: int) -> float:
    """Bytes of a *two-stage* dictionary: the first codebook plus the residual one."""
    return vq_codebook_bytes(bits1, cols) + vq_codebook_bytes(bits2, cols)


#: mode flags for the per-primitive selector (M11): 2 bits, one code left spare.
MSC_FLAG_BITS = 2
MSC_ZERO, MSC_DICT, MSC_SCALAR = 0, 1, 2


def sh_cols(sh_degree: int) -> int:
    return 3 * (sh_degree + 1) ** 2


def fp32_bytes_per_prim(sh_degree: int) -> float:
    """INRIA checkpoint layout in fp32: 11 scalars + 3K SH coefficients."""
    return float(GEO_TOTAL * 4 + sh_cols(sh_degree) * 4)


def msc_bytes(sh_degree: int, b_dict: int, b_scalar: int, n_stored: int) -> tuple:
    """``(c_dict, c_scalar, c_zero)`` in bytes per primitive, codebook excluded.

    The codebook is a *fixed* cost for the asset, so it is divided by the stored
    primitive count once (see :func:`msc_bytes_per_prim`) rather than being weighted
    by the share of dictionary-coded primitives.
    """
    cols = sh_cols(sh_degree)
    c_dict = b_dict / 8.0
    c_scalar = cols * b_scalar / 8.0 + SH_SCALE_BYTES
    return float(c_dict), float(c_scalar), 0.0


def msc_codebook_per_prim(sh_degree: int, b_dict: int, n_stored: int) -> float:
    return float(vq_codebook_bytes(b_dict, sh_cols(sh_degree))) / float(
        n_stored or VQ_NOMINAL_PRIMS)


def msc_bytes_per_prim(sh_degree: int, b_dict: int, b_scalar: int,
                       frac=(0.0, 1.0, 0.0), n_stored: int = None) -> float:
    """Byte model for a mix: ``frac = (zero, dict, scalar)`` shares."""
    total = sum(frac)
    if total <= 0:
        raise ValueError("empty mode mix")
    f = [float(x) / total for x in frac]
    c_dict, c_scalar, c_zero = msc_bytes(sh_degree, b_dict, b_scalar,
                                         n_stored or VQ_NOMINAL_PRIMS)
    return float(MSC_FLAG_BITS / 8.0 + f[0] * c_zero + f[1] * c_dict + f[2] * c_scalar
                 + msc_codebook_per_prim(sh_degree, b_dict, n_stored))


def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None, sh_vq_bits: int = None,
                   n_stored: int = None, sh_rvq: tuple = None,
                   sh_msc: dict = None, sh_pq: tuple = None,
                   quat_st3: int = None) -> float:
    """Literal bytes for one primitive.

    ``sh_bits == 32`` means the SH block is stored as fp32 and therefore carries no
    per-primitive scale; any coarser grid costs ``SH_SCALE_BYTES`` for the two
    block-max scales.  Geometry attributes absent from ``geo`` are stored fp32.
    ``means_cbits`` switches the three position components to cluster-relative coding
    at that many bits each (the grid entry for ``means`` is then ignored).
    ``quat_st3`` replaces the four quaternion components by smallest-three coding at
    that many bits per stored component: ``2 + 3*b`` bits, one selector plus three
    codes (the fourth component is a square root, not a payload).
    """
    cols = sh_cols(sh_degree)
    if sh_pq is not None:
        m_pq, b_pq = int(sh_pq[0]), int(sh_pq[1])
        b_sh = pq_bytes_per_prim(m_pq, b_pq, n_stored, cols)
    elif sh_msc is not None:
        b_sh = msc_bytes_per_prim(sh_degree, int(sh_msc["b_dict"]),
                                  int(sh_msc["b_scalar"]), sh_msc["frac"], n_stored)
    elif sh_rvq is not None:
        b1, b2 = int(sh_rvq[0]), int(sh_rvq[1])
        b_sh = (b1 + b2) / 8.0
        b_sh += (rvq_codebook_bytes(b1, b2, cols)
                 / float(n_stored or VQ_NOMINAL_PRIMS))
    elif sh_vq_bits is not None:
        b_sh = int(sh_vq_bits) / 8.0
        b_sh += vq_codebook_bytes(sh_vq_bits, cols) / float(n_stored or VQ_NOMINAL_PRIMS)
    elif sh_bits >= FP32_BITS:
        b_sh = cols * 4.0
    else:
        b_sh = cols * sh_bits / 8.0 + SH_SCALE_BYTES
    b_geo = 0.0
    for name, n in GEO_SCALARS.items():
        if name == "means" and means_cbits is not None:
            b_geo += 3 * means_cbits / 8.0 + CLUSTER_HEADER_PER_PRIM
            continue
        if name == "quats" and quat_st3 is not None:
            b_geo += (2 + 3 * int(quat_st3)) / 8.0
            continue
        bits = int(geo.get(name, FP32_BITS))
        b_geo += n * bits / 8.0
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


# ---------------------------------------------------------------------------
# spec
# ---------------------------------------------------------------------------


@dataclass
class QSpec:
    name: str
    keep: float = 1.0
    sh_bits: int = FP32_BITS
    geo: dict = field(default_factory=dict)
    #: SH degree actually *stored and rendered* (None = whatever the scene holds).
    #: Dropping a band removes 3(2d+1) coefficients outright, which is a different
    #: lever from narrowing every coefficient's grid, and the two must be compared
    #: at matched bytes rather than assumed equivalent.
    sh_degree_out: int = None
    #: position components coded relative to a per-cluster origin/step instead of the
    #: scene-wide grid.  Error then scales with *local* extent rather than scene size,
    #: which is the lever M2's ``iso_means*`` rows pointed at.
    means_cluster_bits: int = None
    #: width of the codebook index: SH is then stored as one dictionary entry per
    #: primitive instead of ``sh_cols`` independent coefficients.  Mutually exclusive
    #: with ``sh_bits``; the codebook itself is charged per asset.
    sh_vq_bits: int = None
    #: two-stage dictionary: ``(b1, b2)`` index widths.  The second codebook is trained
    #: on the residual of the first, which is how the granularity problem M9 found is
    #: supposed to be attacked: the same total bits, split between a coarse centre and
    #: a local correction.
    sh_rvq_bits: tuple = None
    #: product quantisation ``(groups, bits)`` of the SH block
    sh_pq: tuple = None
    #: per-primitive mode selection ``{"b_dict", "b_scalar", "alpha"}``; ``frac`` is
    #: filled in at encode time because the mode mix is data dependent.
    sh_msc: dict = None
    msc_frac: tuple = None
    #: smallest-three quaternion coding at this many bits per stored component
    #: (``2 + 3*b`` bits total).  The fourth component is reconstructed as
    #: ``sqrt(1 - |abc|^2)``, and the index of the largest component doubles as the
    #: sign carrier, so the payload is three codes plus a 2-bit selector.
    quat_st3: int = None

    def out_degree(self, scene_degree: int) -> int:
        deg = int(scene_degree if self.sh_degree_out is None else self.sh_degree_out)
        return max(0, min(deg, int(scene_degree)))

    @property
    def family(self) -> str:
        if self.name == "clean":
            return "clean"
        is_prune = self.keep < 1.0
        is_quant = (self.sh_bits < FP32_BITS or self.sh_vq_bits is not None
                    or self.sh_rvq_bits is not None or self.sh_msc is not None
                    or self.sh_pq is not None
                    or self.sh_degree_out is not None
                    or self.means_cluster_bits is not None
                    or self.quat_st3 is not None
                    or any(int(b) < FP32_BITS for b in self.geo.values()))
        if self.name.startswith("iso_"):
            return "iso"
        if is_prune and is_quant:
            return "joint"
        if is_prune:
            return "prune"
        if is_quant:
            return "qfp"
        return "clean"

    def bytes_per_prim(self, sh_degree: int, n_stored: int = None) -> float:
        """Bytes for one *kept* primitive, at the degree the variant stores."""
        return bytes_per_prim(self.out_degree(sh_degree), self.sh_bits, self.geo,
                              means_cbits=self.means_cluster_bits,
                              sh_vq_bits=self.sh_vq_bits, n_stored=n_stored,
                              sh_rvq=self.sh_rvq_bits, sh_pq=self.sh_pq,
                              sh_msc=(None if self.sh_msc is None else
                                      dict(self.sh_msc,
                                           frac=self.msc_frac or (0.0, 1.0, 0.0))),
                              quat_st3=self.quat_st3)

    def codebook_bytes(self, sh_degree: int, n_stored: int = None) -> float:
        """Share of the file that the SH dictionary takes (0 for scalar variants)."""
        if self.sh_pq is not None:
            cols = sh_cols(self.out_degree(sh_degree))
            return pq_codebook_bytes(int(self.sh_pq[0]), int(self.sh_pq[1]), cols)
        if self.sh_msc is not None:
            cols = sh_cols(self.out_degree(sh_degree))
            return (vq_codebook_bytes(int(self.sh_msc["b_dict"]), cols)
                    if self.msc_frac is None else 0.0)
        if self.sh_rvq_bits is not None:
            cols = sh_cols(self.out_degree(sh_degree))
            return rvq_codebook_bytes(int(self.sh_rvq_bits[0]),
                                      int(self.sh_rvq_bits[1]), cols)
        if self.sh_vq_bits is None:
            return 0.0
        return vq_codebook_bytes(self.sh_vq_bits, sh_cols(self.out_degree(sh_degree)))

    def rate_vs_fp32(self, sh_degree: int, n_stored: int = None) -> float:
        """Total-file compression ratio: a prune variant keeps only ``keep`` of them."""
        bpp = self.bytes_per_prim(sh_degree, n_stored=n_stored)
        return fp32_bytes_per_prim(sh_degree) / (bpp * self.keep)


GEO_ALIAS = {"means": "means", "scales": "scales", "quats": "quats",
             "opac": "opacities", "opacity": "opacities", "opacities": "opacities"}


def parse_spec(name: str) -> QSpec:
    """Parse one variant name.

    Grammar::

        clean
        p<kk>                       Fisher prune to kk % (fp32 SH, fp32 geometry)
        iso_<attr><bits>            one attribute group at <bits>, rest fp32
        geo<bits>                   all four geometric groups at <bits>
        sh<b>_g<g>  |  q<b>_g<g>    SH at b bits + all geometry at g bits
        p<kk>_q<b>_g<g>             prune, then the same quantisation
        gp<bq>-<bs>-<bo>[_c<k>][_sh<b>]
                                     packed geometry: smallest-three quaternions at
                                     <bq> bits per stored component, log-scales at
                                     <bs>, opacity at <bo>, cluster positions at <k>
                                     (the ``c`` token supplies those).  Without an
                                     ``_sh`` token the SH block stays fp32.
    """
    s = name.strip()
    if s == "clean":
        return QSpec(name=s)
    # optional leading band-truncation token: d<deg>_  (deg in 0..3)
    deg_out = None
    if s[:1] == "d" and s[1:2].isdigit():
        k = 1
        while k < len(s) and s[k].isdigit():
            k += 1
        deg_out = int(s[1:k])
        if not 0 <= deg_out <= 3:
            raise ValueError(f"bad SH degree in {name}")
        s = s[k:].lstrip("_")
        if not s:
            raise ValueError(f"degree-only variant {name} needs a bit spec")
    name0 = s if deg_out is None else name.strip()

    def mk(**kw):
        kw.setdefault("sh_degree_out", deg_out)
        return QSpec(name=name0, **kw)

    if s.startswith("iso_") and deg_out is None:
        body = s[4:]
        for alias, attr in GEO_ALIAS.items():
            if body.startswith(alias):
                bits = int(body[len(alias):])
                if not 1 <= bits <= 32:
                    raise ValueError(f"bad bits in {name}")
                return mk(geo={attr: bits})
        raise ValueError(f"unknown iso group in {name}")
    if s.startswith("geo") and deg_out is None:
        bits = int(s[3:])
        if not 1 <= bits <= 32:
            raise ValueError(f"bad bits in {name}")
        return mk(geo={a: bits for a in GEO_SCALARS})
    # attribute ladder: m<bm>_o<bo>_sh<bs>  (optional p<kk>_ prefix for a hybrid)
    _rest, _keep = s, 1.0
    if _rest.startswith("p") and len(_rest) > 1 and _rest[1:2].isdigit():
        i = 1
        while i < len(_rest) and _rest[i].isdigit():
            i += 1
        _keep = int(_rest[1:i]) / 100.0
        _rest = _rest[i:].lstrip("_")
    # a band-truncation token may also appear inside the ladder (``p50_d1_c8_...``)
    if _rest[:1] == "d" and _rest[1:2].isdigit() and deg_out is None:
        k = 1
        while k < len(_rest) and _rest[k].isdigit():
            k += 1
        deg_out = int(_rest[1:k])
        if not 0 <= deg_out <= 3:
            raise ValueError(f"bad SH degree in {name}")
        _rest = _rest[k:].lstrip("_")
    if ((_rest[:1] in ("m", "c") and _rest[1:2].isdigit())
            or (_rest.startswith("vq") and _rest[2:3].isdigit())
            or (_rest.startswith("rvq") and _rest[3:4].isdigit())
            or (_rest.startswith("msc") and "-" in _rest)
            or (_rest.startswith("pq") and "-" in _rest)
            or (_rest.startswith("gp") and "-" in _rest)):
        geo, sh_bits, seen = {}, FP32_BITS, set()
        cbits = None
        vq_bits = None
        rvq = None
        msc = None
        pq = None
        quat_st3 = None
        for tok in _rest.split("_"):
            if not tok:
                continue
            if tok[0] == "m" and tok[1:].isdigit():
                geo["means"] = int(tok[1:])
                seen.add("m")
            elif tok[0] == "c" and tok[1:].isdigit():
                cbits = int(tok[1:])
                geo.pop("means", None)
                seen.add("m")
            elif tok[0] == "o" and tok[1:].isdigit():
                for a in ("scales", "quats", "opacities"):
                    geo[a] = int(tok[1:])
                seen.add("o")
            elif tok.startswith("gp") and tok.count("-") == 2:
                # packed geometry: quaternions by smallest-three, the two smooth
                # positive groups on tight lattices.  The position grouping is still
                # supplied by the ``c``/``m`` token, so the token only prices three
                # of the four groups.
                p_q, p_s, p_o = tok[2:].split("-")
                if not (p_q.isdigit() and p_s.isdigit() and p_o.isdigit()):
                    raise ValueError(f"bad geometry-pack token {tok!r} in {name}")
                quat_st3, b_s, b_o = int(p_q), int(p_s), int(p_o)
                if not 4 <= quat_st3 <= 12:
                    raise ValueError(f"st3 width out of range in {name}")
                if not 2 <= b_s <= 8 or not 2 <= b_o <= 8:
                    raise ValueError(f"packed scale/opacity width out of range in {name}")
                geo["scales"] = b_s
                geo["opacities"] = b_o
                seen.add("gp")
            elif tok.startswith("sh") and tok[2:].isdigit():
                sh_bits = int(tok[2:])
                seen.add("sh")
            elif tok.startswith("vq") and tok[2:].isdigit():
                vq_bits = int(tok[2:])
                if not 4 <= vq_bits <= 16:
                    raise ValueError(f"codebook index width out of range in {name}")
                seen.add("sh")
            elif tok.startswith("pq") and "-" in tok:
                p, _, q = tok[2:].partition("-")
                m_pq, b_pq = int(p), int(q)
                if m_pq not in (2, 3, 4, 6, 8) or not 2 <= b_pq <= 8:
                    raise ValueError(f"pq widths out of range in {name}")
                if 48 % m_pq:
                    raise ValueError(f"pq groups must divide 48 in {name}")
                pq = (m_pq, b_pq)
                seen.add("sh")
            elif tok.startswith("msc") and "-" in tok:
                parts = tok[3:].split("-")
                if len(parts) != 3 or not all(p for p in parts):
                    raise ValueError(f"bad msc token {tok!r} in {name}")
                b_d, b_s, a = int(parts[0]), int(parts[1]), parts[2]
                if not (a[0] == "a" and a[1:].isdigit()):
                    raise ValueError(f"bad msc alpha {a!r} in {name}")
                if not 6 <= b_d <= 16 or not 2 <= b_s <= 8:
                    raise ValueError(f"msc widths out of range in {name}")
                msc = {"b_dict": b_d, "b_scalar": b_s, "alpha": int(a[1:])}
                seen.add("sh")
            elif tok.startswith("rvq") and "-" in tok:
                a, _, b = tok[3:].partition("-")
                if not (a.isdigit() and b.isdigit()):
                    raise ValueError(f"bad residual-codebook token {tok!r} in {name}")
                rvq = (int(a), int(b))
                for x in rvq:
                    if not 2 <= x <= 14:
                        raise ValueError(f"rvq index width out of range in {name}")
                seen.add("sh")
            else:
                raise ValueError(f"cannot parse ladder token {tok!r} of {name}")
        if "m" not in seen or not ({"sh", "gp"} & seen):
            raise ValueError(f"ladder form needs m|c and sh|gp groups: {name}")
        if "gp" in seen and "o" in seen:
            raise ValueError(f"gp already prices scales/opacity; drop the o token: {name}")
        if vq_bits is not None and sh_bits < FP32_BITS:
            raise ValueError(f"vq and sh are exclusive in {name}")
        if rvq is not None and (vq_bits is not None or sh_bits < FP32_BITS):
            raise ValueError(f"rvq excludes both vq and sh in {name}")
        if msc is not None and (vq_bits is not None or rvq is not None
                                or sh_bits < FP32_BITS):
            raise ValueError(f"msc excludes vq/rvq/sh in {name}")
        if pq is not None and (vq_bits is not None or rvq is not None
                               or msc is not None or sh_bits < FP32_BITS):
            raise ValueError(f"pq excludes vq/rvq/msc/sh in {name}")
        for b in list(geo.values()) + [sh_bits] + ([cbits] if cbits else []):
            if not 1 <= b <= 32:
                raise ValueError(f"bad bits in {name}")
        if cbits is not None and not 6 <= cbits <= 24:
            raise ValueError(f"cluster position bits out of range in {name}")
        return mk(keep=_keep, sh_bits=sh_bits, geo=geo, means_cluster_bits=cbits,
                  sh_vq_bits=vq_bits, sh_rvq_bits=rvq, sh_msc=msc, sh_pq=pq,
                  quat_st3=quat_st3)
    keep = 1.0
    rest = s
    if rest.startswith("p"):
        i = 1
        while i < len(rest) and rest[i].isdigit():
            i += 1
        keep = int(rest[1:i]) / 100.0
        if not 0.05 <= keep <= 1.0:
            raise ValueError(f"keep out of range in {name}")
        rest = rest[i:]
    rest = rest.lstrip("_")
    if not rest:
        return mk(keep=keep)
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
    geo_bits = int(rest[2:])
    if not 1 <= sh_bits <= 32 or not 1 <= geo_bits <= 32:
        raise ValueError(f"bad bits in {name}")
    return mk(keep=keep, sh_bits=sh_bits, geo={a: geo_bits for a in GEO_SCALARS})


DEFAULT_VARIANTS = ",".join([
    "clean",
    # single-group probes (everything else fp32): which attribute is cheap?
    "iso_means10", "iso_means12", "iso_scales8", "iso_scales10",
    "iso_quats8", "iso_quats10", "iso_opac6", "iso_opac8",
    # geometry all at one precision (SH fp32)
    "geo8", "geo10", "geo12", "geo16",
    # the precision frontier at 16-bit geometry (covers 2x..5x)
    "sh16_g16", "sh12_g16", "sh8_g16", "sh6_g16", "sh4_g16",
    # candidate QFP settings (geometry down to 6 bits at the extreme corner)
    "q6_g12", "q4_g12", "q3_g12", "q2_g12", "q2_g10", "q2_g6",
    # prune-first baselines (the paper's / PUP's action space)
    "p90", "p80", "p70", "p60", "p50", "p40", "p30", "p20",
    # prune + quantise hybrids: where does the knee sit, and is the win
    # ordering or just quantisation?  (diagnostic, not the baseline)
    "p70_q4_g12", "p50_q4_g12", "p30_q4_g12",
])


#: M7 grid: positions relative to a local cluster instead of the scene bounding box.
#: M2 showed the position budget must be judged against a primitive's own footprint
#: (leaves ~1-2 mm), not against the scene extent (10 m / 2**16 = 0.15 mm is already
#: too coarse there); a per-cluster origin is the cheapest way to make the grid local.
M7_VARIANTS = ",".join([
    "clean",
    # prune baseline across the same byte range as the new codec
    "p50", "p30", "p20", "p10", "p05",
    # global-grid anchors: the M2/M5 near-lossless shelf
    "m16_o8_sh3", "m16_o8_sh4", "m16_o8_sh2",
    # cluster-relative positions, swept over the local bit budget
    "c8_o8_sh3", "c10_o8_sh3", "c12_o8_sh3", "c14_o8_sh3",
    "c12_o8_sh4", "c12_o8_sh2", "c10_o8_sh2",
    # hybrids: prune first, then the local codec
    "p50_c12_o8_sh3", "p30_c10_o8_sh3",
])


#: M8 grid: the high-rate corner.  At 12x the budget per primitive is ~19.7 B, and the
#: only term that still costs quality there is the view-dependent block: keeping all 48
#: coefficients at 1-2 bits loses more than dropping the upper bands and spending the
#: bytes on the low ones.  Cluster positions (M7) are what make the arithmetic fit.
M8_VARIANTS = ",".join([
    "clean",
    # prune baseline across the same byte range
    "p30", "p20", "p10", "p05",
    # near-lossless anchors carried over from M7
    "c8_o8_sh3", "c10_o8_sh3", "c12_o8_sh2",
    # high-rate candidates: fewer bands, more bits on the ones kept
    "d1_c8_o8_sh4", "d1_c10_o8_sh4", "d1_c8_o8_sh5",
    "d2_c8_o8_sh4", "d2_c10_o8_sh3", "d1_c12_o8_sh4",
    # hybrid at the top of the range
    "p50_d1_c8_o8_sh4",
])


#: M9 grid: the view-dependent block is now a dictionary lookup.  M7 left the 7-13x
#: region constrained by SH bit width (3->2 bits costs 1.86 pp), and M8 showed that
#: spending the same bytes on fewer bands is a wash; the remaining redundancy is
#: *across* primitives (most blocks are near zero, similar materials share a curve),
#: which is exactly what a vector quantiser can take.
M9_VARIANTS = ",".join([
    "clean",
    # scalar anchors from M7/M8: the frontier the dictionary has to beat
    "c10_o8_sh3", "c12_o8_sh2",
    # scalar SH at the *same* bytes as the dictionary (K2 needs a matched-byte row in
    # the 12-18 B range; without these the comparison is unmeasurable -- the lesson
    # N16 recorded after M2 and M7 both ran out of coverage)
    "d0_c8_o6_sh2", "d0_c8_o8_sh2", "d0_c10_o6_sh2", "d0_c12_o8_sh2", "d1_c8_o6_sh2",
    # dictionary width sweep at cluster-8 positions
    "vq6_c8_o8", "vq8_c8_o8", "vq10_c8_o8", "vq12_c8_o8", "vq14_c8_o8",
    # positions matter less once the dictionary does the work
    "vq10_c10_o8", "vq12_c10_o8", "vq12_c12_o8",
    # band truncation on top of the dictionary
    "d2_vq12_c8_o8",
    # hybrid at the top of the range
    "p30_vq12_c8_o8",
])


#: M12 grid: product quantisation.  M9-M11 pushed one 48-d codebook as far as it goes
#: (0.3-2.4 pp at 19x) and neither a second stage nor per-primitive scheduling moved it.
#: PQ changes the codebook's *shape*: interleaved sub-vectors, one small codebook each.
M12_VARIANTS = ",".join([
    "clean",
    # single-codebook anchors at the same bytes
    "vq12_c8_o8", "vq14_c8_o8", "vq16_c8_o8",
    # scalar anchors
    "c8_o8_sh2", "c8_o8_sh3",
    # prune anchors (the family every coverage claim is measured against)
    "p50", "p30", "p20",
    # PQ at 1.0-1.5 B: matched with vq12/14
    "pq2-4_c8_o8", "pq3-4_c8_o8", "pq2-6_c8_o8",
    # PQ at 2.0-3.0 B: matched with vq16
    "pq4-4_c8_o8", "pq3-6_c8_o8", "pq6-4_c8_o8", "pq8-3_c8_o8",
    # the expensive end, where a finer partition should pay
    "pq4-6_c8_o8", "pq4-8_c8_o8",
])

#: Published-format baselines, expressed in the same grammar so they go through the
#: same quantiser, the same renderer and the same byte meter as our own ladder.  The
#: point is a rate-matched comparison on these assets, not a reproduction of another
#: pipeline: ``g32`` keeps geometry at fp32, which is what a SH-only quantiser ships.
SOTA_VARIANTS = ",".join([
    "clean",
    # the published 8-bit SH quantiser: per-block scale, geometry untouched
    "sh8_g32", "sh4_g32",
    # prune-then-quantise, i.e. the usual compression recipe: delete by importance,
    # then round the surviving coefficients
    "p50_q8_g32", "p50_q4_g32", "p30_q4_g32", "p30_q2_g32",
])


#: M11 grid: per-primitive mode selection.  M9 and M10 pushed uniform coding to its
#: limit (19x at 0.3-2.4 pp), and the matched-rate curves show the best family depends on
#: the rate; the remaining freedom is letting each primitive choose its own mode.
M11_VARIANTS = ",".join([
    "clean",
    # single-family anchors at the same bytes
    "c8_o8_sh2", "c8_o8_sh3", "vq12_c8_o8", "rvq10-4_c8_o8",
    # the selector: dict width 12, scalar width 4, three prices for a byte
    "msc12-4-a1_c8_o8", "msc12-4-a2_c8_o8", "msc12-4-a4_c8_o8",
    # a wider scalar option should help the primitives the dictionary serves badly
    "msc12-6-a1_c8_o8", "msc12-6-a4_c8_o8",
    # cheaper dictionary, narrower scalar
    "msc10-4-a2_c8_o8", "msc12-2-a1_c8_o8",
    # buy back 2 B from the nine scalars and spend it on SH
    "msc12-4-a1_c8_o6", "msc12-6-a4_c8_o6",
    # M11.4b: the realised mixes at 4-6 bits per scalar coefficient land at 5-8x,
    # because a scalar-coded primitive then costs 26-38 B and the selector almost
    # always pays it.  The 12-20x region the criteria live in needs 2-3 bit scalars.
    "msc12-2-a2_c8_o8", "msc12-2-a4_c8_o8", "msc12-2-a8_c8_o8",
    "msc12-3-a1_c8_o8", "msc12-3-a4_c8_o8", "msc10-2-a2_c8_o8",
    "msc12-2-a2_c8_o6",
    # low-rate corner
    "p30_msc12-4-a1_c8_o8",
])


#: M10 grid: two-stage dictionary.  M9 left the single-dictionary curve 0.13-1.10 pp
#: short of the 1 pp near-lossless gate at 18-20x; the diagnosis was granularity, not
#: representation, so the next lever is the *split* of the same bits between a coarse
#: centre and a residual centre.
M10_VARIANTS = ",".join([
    "clean",
    # scalar and single-stage anchors at the same bytes
    "c8_o8_sh2", "c8_o8_sh3", "vq10_c8_o8", "vq12_c8_o8",
    # residual ladder at 8, 10, 12 and 14 total index bits
    "rvq6-2_c8_o8", "rvq8-2_c8_o8", "rvq8-4_c8_o8", "rvq10-2_c8_o8",
    "rvq10-4_c8_o8", "rvq8-6_c8_o8", "rvq12-4_c8_o8", "rvq10-6_c8_o8",
    # is the residual codebook still worth it when positions get cheaper?
    "rvq8-4_c10_o8", "rvq10-4_c10_o8",
    # hybrid at the low-rate corner
    "p30_rvq10-4_c8_o8",
])


#: M15 grid: geometry packing.  The nine non-position scalars are lattice-coded at 8
#: bits each (11 B) and the positions at c=10 (3.75 B), so geometry is 14.84 B of the
#: 25.4 B near-lossless file.  The local gate (``geom_pack.py``) measured that a
#: quaternion needs 26 bits rather than 32 (0.34 deg, against 0.43 deg for the 32-bit
#: grid), and that 5-bit log-scales, 4-bit opacity and c=6 positions each sit one step
#: below a width M2/M7 already measured as free: 7.97 B, i.e. 6.88 B of model bytes.
#: The rows below separate the three questions the judgement asks: is packing free at
#: all (bare ``gp`` rows keep SH at fp32, so only geometry moves), where does the
#: lossless shelf land once packing is on (``_sh4/_sh3/_sh2``), and does 12x exist at
#: <=0.3 dB (the last row).
M15_VARIANTS = ",".join([
    "clean",
    # the full packing, SH untouched: geometry-only attribution at 1.2x
    "gp8-5-4_c6",
    # one group relaxed at a time, everything else packed
    "gp8-8-4_c6", "gp6-5-4_c6", "gp8-5-4_c8", "gp8-5-6_c6",
    # the shelf: the same packing under a 4-, 3- and 2-bit SH block
    "gp8-5-4_c6_sh4", "gp8-5-4_c6_sh3", "gp8-5-4_c6_sh2",
    # the two unpacked anchors the frontier is measured against
    "c10_o8_sh3", "c8_o8_sh3",
    # the 12x target (same spec as the shelf row, named for the criterion it serves)
    "gp8-5-4_c6_sh3",
])


#: M16 grid: the *spanning* lattice for an external comparison, not a new hypothesis.
#:
#: M15 closed the question "does geometry packing buy 12x" (no).  What is left is a
#: question about range: every published compressed-3DGS number (HAC 15.3 MB, ContextGS
#: 12.7 MB, PCGS 12.2 MB on MipNeRF360) sits at 40-60x of the fp32 PLY, while our own
#: shelf saturates near 10x (23.7 B/prim at 3-bit SH).  The only way to know where our
#: curve actually crosses theirs is to measure the whole span on the *standard* checkpoints
#: (official 30k PLYs, images_4 protocol) with the fidelity columns they report.
#:
#: The rows are the per-tier winners of M5/M9-M12 plus two dictionary rungs and two
#: prune-plus-codec rungs, so the measured curve is the best we can currently do at each
#: size rather than one family's projection.  Ordered cheapest-first by nominal bytes.
M16_VARIANTS = ",".join([
    "clean",
    # near-lossless low end: SH 16/8 bit + 16-bit geometry
    "sh16_g16", "sh8_g16",
    # the 4-5x knee
    "m16_o8_sh4", "msc12-6-a1_c8_o8",
    # the 8-10x shelf
    "m16_o8_sh2", "c10_o8_sh3", "c8_o8_sh3",
    # 14-20x: 2-bit SH and the two dictionary coders
    "c8_o8_sh2", "vq12_c8_o8", "rvq10-4_c8_o8",
    # 25x and beyond: the only way there is to spend primitive count as well as bits,
    # so the last three rows pair the dictionary codec with a Fisher prune.  These are
    # the rows that can actually meet HAC/PCGS on the size axis, which is why they are
    # in the grid even though the M-series never claimed anything about them.
    "p50_vq12_c8_o8", "p30_vq12_c8_o8", "p10_vq12_c8_o8",
])

def _variants(args) -> list:
    preset = getattr(args, "variant_set", None)
    if preset and preset != "custom":
        # An explicit --variants still wins, so a smoke run can name a subset of a
        # registered grid without inventing a new one.
        if getattr(args, "variants", None) not in (None, DEFAULT_VARIANTS,
                                                  AFQ_VARIANTS, M3_VARIANTS,
                                                  M7_VARIANTS, M8_VARIANTS,
                                                  M9_VARIANTS, M10_VARIANTS,
                                                  M11_VARIANTS, M12_VARIANTS,
                                                  M15_VARIANTS, M16_VARIANTS,
                                                  SOTA_VARIANTS):
            return [v.strip() for v in args.variants.split(",") if v.strip()]
        grid = dict(VARIANT_SETS)[preset]
        return _dedupe(v.strip() for v in grid.split(",") if v.strip())
    return _dedupe(v.strip() for v in args.variants.split(",") if v.strip())


def _dedupe(names) -> list:
    """Drop repeated names, keeping the first occurrence's position.

    A pre-registered grid may name one specification twice -- the M15 grid lists the
    12x target (``gp8-5-4_c6_sh3``) next to the shelf row it is identical to, because
    the two serve different criteria.  Rendering it twice would only produce a second
    copy of the same row (and a duplicate key in the drops map), so the run keeps one.
    """
    out, seen = [], set()
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


#: M2 grid: the attribute floor.  ``m<bm>_o<bo>_sh<bs>`` keeps every primitive and
#: spends bits per attribute group, plus the pruning baselines it must beat.
AFQ_VARIANTS = ",".join([
    "clean",
    # where does the means precision stop being free?  (other groups at 8 bits,
    # which the iso family already showed costs nothing)
    "m12_o8_sh4", "m13_o8_sh4", "m14_o8_sh4", "m15_o8_sh4",
    "m16_o8_sh4", "m17_o8_sh4", "m18_o8_sh4", "m20_o8_sh4",
    # how far can the view-dependent term go?
    # (sh1 is deliberately absent: with per-block min-max scaling qmax = 2**0-1 = 0,
    #  so the scale is a division by zero and every coefficient becomes NaN.  The
    #  published quantiser's smallest usable width is 2 bits.)
    "m16_o8_sh2", "m16_o8_sh3", "m16_o8_sh6", "m16_o8_sh8",
    # the nine non-position scalars, all together
    "m16_o4_sh4", "m16_o6_sh4", "m16_o10_sh4",
    # corner: cheapest point that still has 15-bit positions
    "m15_o6_sh2", "m15_o8_sh2",
    # prune-first baselines, unchanged
    "p90", "p80", "p70", "p60", "p50", "p40", "p30", "p20",
    # hybrids at the high-rate corner (prune is the only way to beat 6x)
    "p70_q4_g16", "p50_q4_g16",
])


#: M3 grid: (a) push the prune baseline out to 20x so the comparison covers the
#: whole QFP range instead of stopping where the pruner ran out of variants, and
#: (b) compare the two ways of shrinking the view-dependent term at matched bytes:
#: fewer bands (``d<k>_``) versus narrower coefficients (``sh<bits>``).
M3_VARIANTS = ",".join([
    "clean",
    # prune baseline, extended to 20x (keep 5%): the paper's action space, now
    # sampled across the same byte range as the quantiser
    "p90", "p70", "p50", "p30", "p20", "p10", "p05",
    # anchors carried over from M2 (near-lossless shelf)
    "m16_o8_sh8", "m16_o8_sh6", "m16_o8_sh4", "m16_o8_sh3", "m16_o8_sh2",
    # cheaper non-position scalars
    "m16_o6_sh3", "m16_o6_sh2", "m18_o6_sh3",
    # band truncation at matched-ish bytes: 8-bit coefficients, fewer bands
    "d2_m16_o8_sh8", "d1_m16_o8_sh8", "d0_m16_o8_sh8",
    "d2_m16_o8_sh4", "d1_m16_o8_sh4",
])


#: J4 (2026-11-18): the container ladder as a *rate axis*, so that coverage can be plotted
#: against rate the way an RD curve plots PSNR against rate. Two families: the colour budget at
#: fixed geometry, and one geometry field at a fixed colour budget. Every row is a spec the
#: shipped container can actually produce; the harness packs per-view residuals for each, which
#: is what the audit needs.
J4_VARIANTS = ",".join((
    "clean",
    "gp6-6-6_c8_sh6",   # 96 bit colour
    "gp6-6-6_c8_sh4",   # 64 bit
    "gp6-6-6_c8_sh3",   # 48 bit (the shipped near-lossless point)
    "gp6-6-6_c8_sh2",   # 32 bit
    "gp4-6-6_c8_sh3",   # quaternions 6 -> 4
    "gp6-4-6_c8_sh3",   # scales 6 -> 4
    "gp6-6-4_c8_sh3",   # opacity 6 -> 4
    "gp6-6-6_c7_sh3",   # positions 8 -> 7
))

#: The registered grids, keyed by the value of ``--variant-set``.  Building the argparse choices
#: from this dict is what keeps a newly registered grid from being rejected by the CLI: the M15
#: and M16 grids were both added to the registry and then refused with
#: ``invalid choice: 'm15'`` / ``'m16'`` because the choices list was a separate literal.
VARIANT_SETS = {
    "custom": DEFAULT_VARIANTS,
    "m1": DEFAULT_VARIANTS,
    "m2": AFQ_VARIANTS,
    "m3": M3_VARIANTS,
    "j4": J4_VARIANTS,
    "m7": M7_VARIANTS,
    "m8": M8_VARIANTS,
    "m9": M9_VARIANTS,
    "m10": M10_VARIANTS,
    "m11": M11_VARIANTS,
    "m12": M12_VARIANTS,
    "m15": M15_VARIANTS,
    "m16": M16_VARIANTS,
    "sota": SOTA_VARIANTS,
}


# ---------------------------------------------------------------------------
# quantisers: scene-level exact min-max grid, one grid per attribute component
# ---------------------------------------------------------------------------


def _grid(t, bits: int):
    """Per-component uniform grid on the exact ``[min, max]`` of ``t``."""
    import torch
    n_lev = (1 << int(bits)) - 1
    mn = t.amin(dim=0, keepdim=True)
    mx = t.amax(dim=0, keepdim=True)
    step = (mx - mn).clamp_min(1e-12) / float(n_lev)
    return mn, step, n_lev


def quantize_grid(t, bits: int):
    """Round ``t`` to a ``bits``-bit uniform grid, one grid per trailing component."""
    import torch
    if int(bits) >= FP32_BITS:
        return t
    mn, step, n_lev = _grid(t, bits)
    return mn + torch.round((t - mn) / step).clamp_(0.0, float(n_lev)) * step


_ST3_LIM = 1.0 / math.sqrt(2.0)


def quantise_st3_torch(q, bits: int):
    """Smallest-three quaternion coding, torch port of ``geom_pack.quantise_st3``.

    The decoder needs three payload components plus the index of the largest one
    (``2 + 3*bits`` bits); the fourth component is ``sqrt(1 - |abc|^2)`` and the
    largest component's sign is folded into the index.  ``tests/test_m15_pack.py``
    pins this implementation against the numpy one, because the render path and the
    byte meter have to code the *same* quaternions: otherwise the measured bytes and
    the measured quality would describe two different files.
    """
    import torch
    b = int(bits)
    q = q / q.norm(dim=-1, keepdim=True).clamp_min(1e-12)
    n = int(q.shape[0])
    rows = torch.arange(n, device=q.device)
    which = q.abs().argmax(dim=-1)
    sign = torch.sign(q[rows, which])
    sign = torch.where(sign == 0, torch.ones_like(sign), sign)
    q = q * sign[:, None]
    mask = torch.arange(4, device=q.device)[None, :] != which[:, None]
    abc = q[mask].reshape(n, 3)
    n_lev = float((1 << b) - 1)
    step = 2.0 * _ST3_LIM / n_lev
    aq = ((abc + _ST3_LIM) / step).round().clamp_(0.0, n_lev) * step - _ST3_LIM
    out = torch.zeros_like(q)
    out[mask] = aq.reshape(-1)
    out[rows, which] = (1.0 - (aq * aq).sum(1)).clamp_min(0.0).sqrt()
    return out / out.norm(dim=-1, keepdim=True).clamp_min(1e-12)



def morton_order(means, nbits: int = 21):
    """Permutation that visits primitives in Morton order of their positions.

    The order is a pure function of the *decoded* positions, so a decoder can rebuild
    it without side information; that is what makes cluster coding free of an index
    stream.  Positions are first normalised to the scene's bounding box, then the
    three 21-bit codes are interleaved (x lowest bit first).
    """
    import torch
    n = int(means.shape[0])
    mn = means.amin(dim=0, keepdim=True)
    mx = means.amax(dim=0, keepdim=True)
    ext = (mx - mn).clamp_min(1e-12)
    top = float((1 << nbits) - 1)
    q = ((means - mn) / ext * top).round().clamp_(0.0, top).to(torch.int64)
    key = torch.zeros(n, dtype=torch.int64, device=means.device)
    for b in range(nbits - 1, -1, -1):
        for d in range(3):
            key = (key << 1) | ((q[:, d] >> b) & 1)
    return torch.argsort(key)


def quantize_cluster(means, bits: int, block: int = CLUSTER_SIZE):
    """Quantise positions against a per-cluster origin and step.

    Primitives are cut into Morton-ordered blocks of ``block``.  Each block stores its
    own ``min`` and per-component step (``CLUSTER_HEADER_BYTES``) and every offset is
    rounded to ``bits`` levels, so the error scales with the extent of a *local* block
    instead of the whole scene.  Header cost per primitive is
    ``CLUSTER_HEADER_PER_PRIM``, which ``bytes_per_prim`` charges.
    """
    import torch
    n = int(means.shape[0])
    if int(bits) >= FP32_BITS or n == 0:
        return means
    order = morton_order(means)
    x = means.index_select(0, order)
    nblk = (n + block - 1) // block
    pad = nblk * block - n
    if pad:
        x = torch.cat([x, x[-1:].expand(pad, 3)], dim=0)
    x = x.reshape(nblk, block, 3)
    o = x.amin(dim=1, keepdim=True)
    mx = x.amax(dim=1, keepdim=True)
    n_lev = float((1 << int(bits)) - 1)
    step = ((mx - o) / n_lev).clamp_min(1e-12)
    u = ((x - o) / step).round().clamp_(0.0, n_lev)
    y = (o + u * step).reshape(-1, 3)[:n]
    out = torch.empty_like(means)
    out.index_copy_(0, order, y)
    return out


def _logit(p, torch):
    p = p.clamp(1e-6, 1 - 1e-6)
    return torch.log(p / (1.0 - p))


def _sh_flat(sp):
    """The whole view-dependent block as one ``(N, 3K)`` matrix."""
    import torch
    n = int(sp.n)
    return torch.cat([sp.sh0.reshape(n, -1), sp.shN.reshape(n, -1)], dim=1)


def _set_sh_flat(sp, flat):
    import torch
    n = int(sp.n)
    sp.sh0 = flat[:, :3].reshape(n, 1, 3).contiguous()
    rest = flat[:, 3:]
    if rest.shape[1]:
        sp.shN = rest.reshape(sp.shN.shape).contiguous()


def _vq_assign(x, codebook, block: int = None):
    """Nearest-centre index for every row of ``x``; chunked to bound the workspace."""
    import torch
    n = int(x.shape[0])
    k = int(codebook.shape[0])
    if not block:
        block = max(4096, (1 << 26) // max(1, k))
    out = torch.empty(n, dtype=torch.int64, device=x.device)
    ct = (codebook * codebook).sum(1)
    for s0 in range(0, n, block):
        xb = x[s0:s0 + block]
        d2 = (xb * xb).sum(1)[:, None] - 2.0 * (xb @ codebook.t()) + ct[None, :]
        out[s0:s0 + block] = d2.argmin(dim=1)
    return out


def _kmeans(x, k: int, iters: int = 15, seed: int = 0, subsample: int = 500_000):
    """Lloyd iterations on a fixed subsample; deterministic given ``seed``."""
    import torch
    g = torch.Generator(device="cpu").manual_seed(int(seed))
    n = int(x.shape[0])
    if n > subsample:
        idx = torch.randperm(n, generator=g)[:subsample]
        xs = x[torch.as_tensor(idx, device=x.device)]
    else:
        xs = x
    m = int(xs.shape[0])
    if k <= m:
        init = torch.randperm(m, generator=g)[:k]
    else:
        init = torch.randint(0, m, (k,), generator=g)
    C = xs[torch.as_tensor(init, device=x.device)].clone()
    for _ in range(int(iters)):
        a = _vq_assign(xs, C)
        tot = torch.zeros_like(C)
        cnt = torch.zeros(k, device=x.device)
        tot.index_add_(0, a, xs)
        cnt.index_add_(0, a, torch.ones(m, device=x.device))
        live = cnt > 0
        C[live] = tot[live] / cnt[live, None]
    return C


def quantise_codebook(C, bits: int = 8):
    """Round every centroid onto one global 8-bit grid (the cost the model charges)."""
    import torch
    n_lev = float((1 << int(bits)) - 1)
    mn = C.amin()
    step = ((C.amax() - mn) / n_lev).clamp_min(1e-12)
    return mn + torch.round((C - mn) / step).clamp_(0.0, n_lev) * step


def build_codebook(sp, vq_bits: int, deg_out: int, seed: int = 0, iters: int = 15):
    """Train and 8-bit-quantise the SH dictionary for one asset."""
    cols = sh_cols(int(deg_out))
    x = _sh_flat(sp)[:, :cols].contiguous()
    C = _kmeans(x, 1 << int(vq_bits), iters=iters, seed=seed)
    return quantise_codebook(C, 8)


def quantize_vq(sp, codebook, deg_out: int):
    """Replace the SH block with dictionary entries; bands above ``deg_out`` are zeroed."""
    import torch
    cols = sh_cols(int(deg_out))
    flat = _sh_flat(sp)
    codes = _vq_assign(flat[:, :cols].contiguous(), codebook)
    out = flat.clone()
    out[:, :cols] = codebook.index_select(0, codes)
    if cols < int(out.shape[1]):
        out[:, cols:] = 0.0
    _set_sh_flat(sp, out)
    return codes


def build_codebook_pair(sp, b1: int, b2: int, deg_out: int, seed: int = 0, iters: int = 15):
    """Two-stage dictionary: the residual codebook is trained on stage-one errors."""
    import torch
    cols = sh_cols(int(deg_out))
    x = _sh_flat(sp)[:, :cols].contiguous()
    C1 = quantise_codebook(_kmeans(x, 1 << int(b1), iters=iters, seed=seed), 8)
    a1 = _vq_assign(x, C1)
    R = x - C1.index_select(0, a1)
    C2 = quantise_codebook(_kmeans(R, 1 << int(b2), iters=iters, seed=seed + 1), 8)
    return (C1, C2)


def quantize_rvq(sp, pair, deg_out: int):
    """Replace the SH block with ``centre1 + centre2``; bands above ``deg_out`` zeroed."""
    import torch
    C1, C2 = pair
    cols = sh_cols(int(deg_out))
    flat = _sh_flat(sp)
    x = flat[:, :cols].contiguous()
    a1 = _vq_assign(x, C1)
    r = x - C1.index_select(0, a1)
    a2 = _vq_assign(r, C2)
    out = flat.clone()
    out[:, :cols] = C1.index_select(0, a1) + C2.index_select(0, a2)
    if cols < int(out.shape[1]):
        out[:, cols:] = 0.0
    _set_sh_flat(sp, out)
    return a1, a2


def _q_block(x, bits: int):
    """Published block quantiser on one primitive block (per-primitive max scale)."""
    import torch
    qmax = float((1 << (int(bits) - 1)) - 1)
    a = x.abs().amax(dim=1, keepdim=True).clamp_min(1e-12)
    st = a / qmax
    return torch.round(x / st).clamp(-qmax - 1.0, qmax) * st


def msc_select(sp, spec: QSpec, state, deg_out: int):
    """Pick a mode per primitive: ``argmin_m D_m + lam * c_m``.

    ``lam`` is normalised so that ``alpha = 1`` prices one byte at the asset's mean
    scalar-quantisation error, which keeps the three alphas comparable across assets.
    Returns ``(modes, rec_dict_full, rec_scalar_full, frac)``.
    """
    import torch
    cols = sh_cols(int(deg_out))
    m = spec.sh_msc
    b_d, b_s, alpha = int(m["b_dict"]), int(m["b_scalar"]), float(m["alpha"])
    flat = _sh_flat(sp)[:, :cols].contiguous()
    C = state.codebook(b_d, deg_out)
    a = _vq_assign(flat, C)
    rec_d = C.index_select(0, a)
    Dd = ((flat - rec_d) ** 2).sum(1)
    q0 = _q_block(flat[:, :3], b_s)
    q1 = _q_block(flat[:, 3:], b_s)
    rec_s = torch.cat([q0, q1], dim=1)
    Ds = ((flat - rec_s) ** 2).sum(1)
    Dz = (flat ** 2).sum(1)
    c_dict, c_scalar, c_zero = msc_bytes(deg_out, b_d, b_s, int(sp.n))
    lam = alpha * float(Ds.mean()) / max(c_scalar, 1e-12)
    cost = torch.stack([Dz + lam * c_zero, Dd + lam * c_dict, Ds + lam * c_scalar], dim=1)
    modes = cost.argmin(dim=1)
    n = float(max(1, int(sp.n)))
    frac = (float((modes == MSC_ZERO).sum()) / n,
            float((modes == MSC_DICT).sum()) / n,
            float((modes == MSC_SCALAR).sum()) / n)
    return modes, rec_d, rec_s, frac


def quantize_msc(sp, spec: QSpec, state, deg_out: int):
    """Write the selected reconstruction into the SH block; bands above are zeroed."""
    import torch
    cols = sh_cols(int(deg_out))
    modes, rec_d, rec_s, frac = msc_select(sp, spec, state, deg_out)
    flat = _sh_flat(sp)
    out = flat.clone()
    out[:, :cols] = 0.0
    sel_d = modes == MSC_DICT
    sel_s = modes == MSC_SCALAR
    if bool(sel_d.any()):
        out[sel_d, :cols] = rec_d[sel_d]
    if bool(sel_s.any()):
        out[sel_s, :cols] = rec_s[sel_s]
    if cols < int(out.shape[1]):
        out[:, cols:] = 0.0
    _set_sh_flat(sp, out)
    return modes, frac


def build_codebook_pq(sp, m: int, b: int, deg_out: int, seed: int = 0, iters: int = 15):
    """One codebook per interleaved sub-vector of the SH block."""
    import torch  # noqa: F401  (kept for symmetry with the other builders)
    cols = sh_cols(int(deg_out))
    if cols % m:
        raise ValueError(f"{cols} coefficients do not split into {m} groups")
    flat = _sh_flat(sp)[:, :cols].contiguous()
    books = []
    for g in range(m):
        sub = flat[:, g::m].contiguous()
        books.append(quantise_codebook(_kmeans(sub, 1 << b, seed=seed + g, iters=iters), 8))
    return books


def quantize_pq(sp, books, m: int, deg_out: int):
    """Replace each sub-vector by its nearest centre."""
    cols = sh_cols(int(deg_out))
    flat = _sh_flat(sp)
    out = flat.clone()
    for g, C in enumerate(books):
        sub = flat[:, g::m].contiguous()
        idx = _vq_assign(sub, C)
        out[:, g::m] = C.index_select(0, idx)
    if cols < int(out.shape[1]):
        out[:, cols:] = 0.0
    _set_sh_flat(sp, out)
    return sp


def base_degree(sp) -> int:
    """SH degree a ``Splats`` object currently holds."""
    return int(getattr(sp, "sh_degree", 3))


def apply_quant(sp, spec: QSpec, state=None):
    """Return a quantised clone of ``sp`` for ``spec`` (never mutates the input)."""
    import torch
    out = sp.clone()
    if spec.sh_pq is not None:
        if state is None:
            raise RuntimeError("product quantisation needs the scene state (codebooks)")
        m_pq, b_pq = int(spec.sh_pq[0]), int(spec.sh_pq[1])
        deg_out = spec.out_degree(int(base_degree(sp)))
        quantize_pq(out, state.codebook_pq(m_pq, b_pq, deg_out), m_pq, deg_out)
    elif spec.sh_msc is not None:
        if state is None:
            raise RuntimeError("mode-selected SH needs the scene state (codebook)")
        deg_out = spec.out_degree(int(base_degree(sp)))
        _, frac = quantize_msc(out, spec, state, deg_out)
        spec.msc_frac = frac
    elif spec.sh_rvq_bits is not None:
        if state is None:
            raise RuntimeError("residual-quantised SH needs the scene state (codebooks)")
        deg_out = spec.out_degree(int(base_degree(sp)))
        b1, b2 = int(spec.sh_rvq_bits[0]), int(spec.sh_rvq_bits[1])
        quantize_rvq(out, state.codebook_pair(b1, b2, deg_out), deg_out)
    elif spec.sh_vq_bits is not None:
        if state is None:
            raise RuntimeError("vector-quantised SH needs the scene state (codebook)")
        deg_out = spec.out_degree(int(base_degree(sp)))
        quantize_vq(out, state.codebook(spec.sh_vq_bits, deg_out), deg_out)
    elif spec.sh_bits < FP32_BITS:
        import dump_artifacts as D
        out = D._quantize_splats(out, torch, bits=int(spec.sh_bits))
    geo = {k: int(v) for k, v in spec.geo.items() if int(v) < FP32_BITS}
    if spec.means_cluster_bits is not None:
        out.means = quantize_cluster(out.means, int(spec.means_cluster_bits))
    if spec.quat_st3 is not None:
        # packed geometry: the quaternion group never goes through the uniform grid
        out.quats = quantise_st3_torch(out.quats, int(spec.quat_st3))
        geo.pop("quats", None)
    if geo:
        if "means" in geo:
            out.means = quantize_grid(out.means, geo["means"])
        if "scales" in geo:
            out.scales = torch.exp(quantize_grid(torch.log(out.scales.clamp_min(1e-12)),
                                                 geo["scales"]))
        if "quats" in geo:
            q = quantize_grid(out.quats, geo["quats"])
            out.quats = q / q.norm(dim=-1, keepdim=True).clamp_min(1e-12)
        if "opacities" in geo:
            lg = _logit(out.opacities, torch)
            out.opacities = torch.sigmoid(quantize_grid(lg, geo["opacities"]))
    return out


# ---------------------------------------------------------------------------
# realise one variant
# ---------------------------------------------------------------------------


@dataclass
class SceneState:
    base: object
    fisher: np.ndarray = None
    cache: dict = field(default_factory=dict)

    def codebook_pair(self, b1: int, b2: int, deg_out: int):
        """Two-stage SH dictionary, trained once per asset and reused."""
        key = ("rvq", int(b1), int(b2), int(deg_out))
        if key not in self.cache:
            self.cache[key] = build_codebook_pair(self.base, b1, b2, deg_out)
        return self.cache[key]

    def codebook_pq(self, m: int, b: int, deg_out: int):
        """Product-quantisation codebooks for this asset, trained once and reused."""
        key = ("pq", int(m), int(b), int(deg_out))
        if key not in self.cache:
            self.cache[key] = build_codebook_pq(self.base, int(m), int(b), int(deg_out))
        return self.cache[key]

    def codebook(self, vq_bits: int, deg_out: int):
        """SH dictionary for this asset, trained once and reused by every variant."""
        key = ("cb", int(vq_bits), int(deg_out))
        if key not in self.cache:
            self.cache[key] = build_codebook(self.base, vq_bits, deg_out)
        return self.cache[key]


def keep_indices(fisher, keep: float):
    """Ascending indices of the ``keep`` fraction with the largest Fisher score.

    ``fisher`` arrives as a CUDA tensor from ``calib.sensitivity``; numpy cannot
    touch it in place, so the conversion happens here rather than at every call.
    """
    if hasattr(fisher, "detach"):
        fisher = fisher.detach().float().cpu().numpy()
    fisher = np.asarray(fisher, dtype=np.float64).reshape(-1)
    n = int(fisher.shape[0])
    k = max(1, int(round(keep * n)))
    return np.sort(np.argsort(-fisher)[:k])


def realize(spec: QSpec, st: SceneState, device):
    """Build the variant ``Splats`` plus realised byte diagnostics."""
    import torch
    base = st.base
    sp = base
    extra = {}
    if spec.keep < 1.0:
        if st.fisher is None:
            raise RuntimeError("prune variant needs Fisher scores")
        idx = torch.as_tensor(keep_indices(st.fisher, spec.keep), device=base.means.device)
        sp = base.subset(idx)
    if spec.sh_bits < FP32_BITS or spec.geo or spec.sh_vq_bits is not None \
            or spec.means_cluster_bits is not None or spec.quat_st3 is not None:
        sp = apply_quant(sp, spec, st)

    return sp, extra


def _render_variant(sp, c2w_v, K_v, W, H, chunk: int = 4, sh_degree: int = None):
    import torch
    from calib.gsrender import render
    deg = sp.sh_degree if sh_degree is None else min(int(sh_degree), int(sp.sh_degree))
    cols, alps = [], []
    for s in range(0, c2w_v.shape[0], chunk):
        sl = slice(s, s + chunk)
        out = render(sp, c2w_v[sl], K_v[sl], W, H, sh_degree=deg)
        cols.append(out["colors"].float().cpu())
        alps.append(out["alphas"].float().cpu()[..., 0])
        del out
    return torch.cat(cols, 0), torch.cat(alps, 0)


# ---------------------------------------------------------------------------
# real (GPU) run
# ---------------------------------------------------------------------------


def run_real(args) -> dict:
    C = _C()
    C.add_code_root()
    import torch
    from calib.archive_only import load_archive_only_scene
    from calib.colmap_io import load_images, normalize_exposure
    from calib.gsrender import load_splats
    import dump_artifacts as D

    torch.manual_seed(args.seed)
    specs = [parse_spec(v) for v in _variants(args)]
    scenes = [s.strip() for s in args.scenes.split(",") if s.strip()]
    os.makedirs(args.out, exist_ok=True)
    pack_args = type("A", (), dict(downsample=args.downsample, factor=args.factor,
                                   alpha=args.alpha, cal_frac=args.cal_frac,
                                   no_compress=args.no_compress,
                                   budget_mb=args.budget_mb,
                                   fidelity=bool(args.fidelity),
                                   lpips_net=args.lpips_net))()
    manifest = dict(dry_run=False, archive=args.archive, factor=args.factor,
                    alpha=args.alpha, fidelity=bool(args.fidelity),
                    lpips_net=args.lpips_net if args.fidelity else None,
                    bytes_model="11*b_geo/8 + 3K*b_sh/8 + 2",
                    variants=[s.name for s in specs], scenes=[])
    # Merge on load: one scene per process is the resilient way to run this (a
    # segfault in scene four must not erase scenes one to three), so a rerun must
    # keep the rows of the scenes it is not touching.
    _mprev = os.path.join(args.out, "m1_manifest.json")
    if os.path.exists(_mprev):
        try:
            with open(_mprev, "r", encoding="utf-8") as fh:
                _old = json.load(fh)
            manifest["scenes"] = [r for r in _old.get("scenes", [])
                                  if r.get("scene") not in scenes]
            C.log(f"merged {len(manifest['scenes'])} existing scene row(s) from manifest")
        except Exception as exc:                                # noqa: BLE001
            C.log(f"warn: could not merge existing manifest ({exc})")

    for scene in scenes:
        t_scene = time.time()
        sc = load_archive_only_scene(args.archive, scene, factor=args.factor,
                                     cal_frac=args.cal_frac)
        W, H = int(sc["width"]), int(sc["height"])
        _gt = load_images(sc["image_paths"], args.factor, (W, H))
        gt_np = (normalize_exposure(_gt) if args.gt_convention == "normalized"
                 else _gt.astype(np.float32) / 255.0)
        gt = torch.from_numpy(gt_np).float().to(args.device)
        c2w_all = torch.from_numpy(sc["camtoworlds"]).to(args.device)
        K_all = torch.from_numpy(sc["Ks"]).to(args.device)
        views = sorted(set(int(i) for i in sc["cal_idx"]) | set(int(i) for i in sc["dep_idx"]))
        if args.max_views and len(views) > args.max_views:
            views = views[: args.max_views]
        cal = [int(i) for i in sc["cal_idx"] if int(i) in set(views)]
        vt = torch.as_tensor(views, device=args.device)
        c2w_v, K_v = c2w_all[vt], K_all[vt]
        gt_v = gt[torch.as_tensor(views)].permute(0, 3, 1, 2).contiguous()
        gt_gray = gt_v.mean(1).cpu().numpy().astype(np.float32)
        gt_hwc = gt_v.permute(0, 2, 3, 1).cpu()

        ply = args.ply_pattern.format(archive=args.archive, scene=scene)
        base = load_splats(ply, device=args.device)
        deg = base.sh_degree
        st = SceneState(base=base)
        C.log(f"[{C.stamp()}] === {scene}: {base.n} primitives, SH degree {deg} "
              f"({sh_cols(deg)} coefs, fp32 {fp32_bytes_per_prim(deg):.0f} B/prim), "
              f"{len(views)} views, {W}x{H}")

        if any(s.keep < 1.0 for s in specs):
            t0 = time.time()
            import calib.sensitivity as sens
            st.fisher = sens.sensitivity_scores(base, c2w_all, K_all, gt, cal, W, H,
                                                n_views=args.n_fisher_views,
                                                device=args.device)
            C.log(f"  Fisher over {min(args.n_fisher_views, len(cal))} cal views "
                  f"({time.time() - t0:.1f}s)")

        grays, resids, stats = [], [], {}
        for spec in specs:
            t0 = time.time()
            sp, extra = realize(spec, st, args.device)
            deg_out = spec.out_degree(deg)
            cols, alps = _render_variant(sp, c2w_v, K_v, W, H, sh_degree=deg_out)
            res = (cols - gt_hwc).abs().mean(-1).numpy()
            grays.append(cols.mean(-1).numpy())
            resids.append(res)
            rv_mean = res.reshape(len(views), -1).mean(1)
            rv_med = np.median(res.reshape(len(views), -1), axis=1)
            av = alps.numpy().reshape(len(views), -1).mean(1)
            stats[spec.name] = dict(
                n_primitives=int(sp.n),
                psnr=C.psnr_np(cols.numpy(), gt_hwc.numpy()),
                mean_alpha=float(av.mean()),
                resid_median=float(np.median(rv_med)),
                resid_mean=float(rv_mean.mean()),
                psnr_views=[C.psnr_np(cols[i].numpy(), gt_hwc[i].numpy())
                            for i in range(len(views))],
                resid_mean_views=[float(x) for x in rv_mean],
                resid_median_views=[float(x) for x in rv_med],
                alpha_views=[float(x) for x in av],
            )
            if args.fidelity:
                fid = D._fidelity_stats(cols, gt_v, args)
                stats[spec.name].update(fid)
            n_st = int(sp.n)
            bpp = spec.bytes_per_prim(deg, n_stored=n_st)
            stats[spec.name].update(
                bytes_per_prim=float(bpp),
                codebook_bytes=float(spec.codebook_bytes(deg)),
                keep=float(spec.keep),
                ratio_vs_fp32=float(spec.rate_vs_fp32(deg, n_stored=n_st)),
                sh_degree_out=int(deg_out),
                family=spec.family, **extra)
            C.log(f"  {scene:11s} {spec.name:12s} n={sp.n:>9,d} "
                  f"B/pr={bpp:6.1f} ({spec.rate_vs_fp32(deg, n_stored=int(sp.n)):4.2f}x) "
                  f"PSNR={stats[spec.name]['psnr']:6.2f} "
                  f"resid={stats[spec.name]['resid_mean']:.4f} "
                  f"ssim={stats[spec.name].get('ssim')} ({time.time() - t0:.1f}s)")
            del cols, alps, res
            if spec.name != "clean":
                del sp
            if str(args.device).startswith("cuda"):
                torch.cuda.empty_cache()

        n_keep = min(int(args.prim_sample), base.n)
        stride = max(1, base.n // max(1, n_keep))
        meta = dict(dry_run=False, gt_convention="archive", a4=True, m1=True,
                    bytes_model="11*b_geo/8 + 3K*b_sh/8 + 2",
                    prim_sample_stride=int(stride),
                    prim_sample_n=int(len(base.means.detach().cpu().numpy()[::stride])),
                    scene_ntotal_primitives=int(base.n), sh_degree=int(deg))
        row, path = D.pack_and_save(args.out, scene, [s.name for s in specs],
                                    np.stack(grays, 0), np.stack(resids, 0), gt_gray,
                                    np.asarray(views, np.int32),
                                    c2w_v.detach().cpu().numpy(),
                                    K_v.detach().cpu().numpy(), stats, meta,
                                    base.means.detach().cpu().numpy()[::stride],
                                    base.opacities.detach().cpu().numpy()[::stride],
                                    pack_args)
        row.update(sh_degree=int(deg), fp32_bytes_per_prim=float(fp32_bytes_per_prim(deg)),
                   seconds=round(time.time() - t_scene, 1))
        # pack_and_save keeps a fixed whitelist of per-variant fields (it is shared
        # with the A4 round), so the rate bookkeeping and the optional fidelity
        # numbers have to be added back here or the analysis would silently see
        # rate=None for every variant.
        for name in row.get("variants", {}):
            st = stats.get(name) or {}
            for k in ("bytes_per_prim", "codebook_bytes", "keep", "ratio_vs_fp32",
                      "family",
                      "sh_degree_out", "ssim", "lpips", "ssim_views", "lpips_views"):
                if k in st:
                    row["variants"][name][k] = st[k]
        manifest["scenes"].append(row)
        # Written after every scene: a crash in scene four must not throw away the
        # byte accounting of scenes one to three, and the analyser reads this file.
        C.json_dump(os.path.join(args.out, "m1_manifest.json"), manifest)
        C.log(f"[{C.stamp()}] {scene}: {len(specs)} variants -> {path} "
              f"({time.time() - t_scene:.0f}s)")
        del base, st, grays, resids
        if str(args.device).startswith("cuda"):
            torch.cuda.empty_cache()

    C.json_dump(os.path.join(args.out, "m1_manifest.json"), manifest)
    C.log(f"[{C.stamp()}] WROTE {os.path.join(args.out, 'm1_manifest.json')}")
    return manifest


# ---------------------------------------------------------------------------
# self-test (CPU, synthetic)
# ---------------------------------------------------------------------------


def _synthetic_splats(n: int = 2000, deg: int = 3, seed: int = 0, device="cpu"):
    import torch
    from calib.gsrender import Splats
    g = torch.Generator(device="cpu").manual_seed(seed)
    K = (deg + 1) ** 2
    return Splats(
        means=torch.randn(n, 3, generator=g) * 2.0,
        scales=torch.exp(torch.randn(n, 3, generator=g) * 0.3 - 3.0),
        quats=(lambda q: q / q.norm(dim=-1, keepdim=True))(
            torch.randn(n, 4, generator=g)),
        opacities=torch.rand(n, generator=g) * 0.6 + 0.35,
        sh0=torch.randn(n, 1, 3, generator=g) * 0.5,
        shN=torch.randn(n, K - 1, 3, generator=g) * 0.05,
    )


def selftest(args) -> int:
    C = _C()
    C.add_code_root()
    import torch
    fails = []

    def _raises(fn):
        try:
            fn()
            return False
        except ValueError:
            return True

    def check(name, cond, detail=""):
        C.log(f"  [{'ok' if cond else 'FAIL'}] {name} {detail}")
        if not cond:
            fails.append(name)

    C.log("== byte model ==")
    deg = 3
    cols = sh_cols(deg)
    check("K=16 SH coefs", cols == 48, f"{cols}")
    check("fp32 == 236 B", abs(fp32_bytes_per_prim(deg) - 236.0) < 1e-9,
          f"{fp32_bytes_per_prim(deg)}")
    check("q4_g16 == 48 B", abs(bytes_per_prim(deg, 4, {a: 16 for a in GEO_SCALARS}) - 48.0) < 1e-9)
    check("q2_g8 == 25 B", abs(bytes_per_prim(deg, 2, {a: 8 for a in GEO_SCALARS}) - 25.0) < 1e-9)
    check("q2_g6 == 22.25 B", abs(bytes_per_prim(deg, 2, {a: 6 for a in GEO_SCALARS}) - 22.25) < 1e-9)
    check("fp32 SH has no scale overhead",
          abs(bytes_per_prim(deg, 32, {a: 16 for a in GEO_SCALARS}) - 214.0) < 1e-9)
    check("monotone in sh bits",
          all(bytes_per_prim(deg, b, {a: 16 for a in GEO_SCALARS}) <
              bytes_per_prim(deg, b + 1, {a: 16 for a in GEO_SCALARS})
              for b in (2, 3, 4, 6, 8, 12)))

    C.log("== spec parsing ==")
    names = _variants(argparse.Namespace(variants=DEFAULT_VARIANTS))
    specs = [parse_spec(n) for n in names]
    check("variant count", len(specs) == 35, f"{len(specs)}")
    by = {s.name: s for s in specs}
    check("p30 keeps 0.3", abs(by["p30"].keep - 0.3) < 1e-9)
    check("q4_g12 sh/geo", by["q4_g12"].sh_bits == 4 and by["q4_g12"].geo["means"] == 12)
    check("iso_opac6 maps to opacities", by["iso_opac6"].geo == {"opacities": 6})
    check("geo16 all groups", set(by["geo16"].geo) == set(GEO_SCALARS))
    check("p50_q4_g12 parse", by["p50_q4_g12"].keep == 0.5
          and by["p50_q4_g12"].sh_bits == 4
          and by["p50_q4_g12"].geo["quats"] == 12)
    check("families", [by[k].family for k in ("clean", "p30", "q4_g12", "p50_q4_g12", "iso_quats8", "geo10")]
          == ["clean", "prune", "qfp", "joint", "iso", "qfp"])
    check("ratios strictly decreasing at 16-bit geo",
          all(by[f"sh{b}_g16"].bytes_per_prim(deg) > by[f"sh{b2}_g16"].bytes_per_prim(deg)
              for b, b2 in ((16, 12), (12, 8), (8, 6), (6, 4))))
    check("prune ratio divides by keep",
          abs(by["p50"].rate_vs_fp32(deg) - 2.0) < 1e-9,
          f"{by['p50'].rate_vs_fp32(deg):.3f}x")
    check("q4_g16 sits at 4.92x", abs(by["sh4_g16"].rate_vs_fp32(deg) - 236.0 / 48.0) < 1e-9,
          f"{by['sh4_g16'].rate_vs_fp32(deg):.3f}x")
    check("joint reaches past 18x", by["p30_q4_g12"].rate_vs_fp32(deg) > 18.0,
          f"{by['p30_q4_g12'].rate_vs_fp32(deg):.2f}x")
    try:
        parse_spec("garbage")
        check("rejects garbage", False)
    except ValueError:
        check("rejects garbage", True)

    # band truncation is a second lever: fewer stored coefficients at the same
    # width must cost fewer bytes, and the stored degree must never exceed the
    # scene's own degree.
    C.log("== band truncation ==")
    d2 = parse_spec("d2_m16_o8_sh8")
    check("d-prefix keeps the full name", d2.name == "d2_m16_o8_sh8", d2.name)
    check("d2 stores degree 2", d2.out_degree(3) == 2, str(d2.out_degree(3)))
    check("d-prefix is clamped to the scene degree", parse_spec("d3_m16_o8_sh8").out_degree(2) == 2,
          str(parse_spec("d3_m16_o8_sh8").out_degree(2)))
    check("fewer bands cost fewer bytes",
          bytes_per_prim(2, 8, d2.geo) < bytes_per_prim(3, 8, d2.geo),
          f"{bytes_per_prim(2, 8, d2.geo):.1f} vs {bytes_per_prim(3, 8, d2.geo):.1f}")
    check("degree 0 keeps only DC (3 coefficients)", sh_cols(0) == 3)
    check("d2 at 8 bits sits near 5.5x",
          abs(d2.rate_vs_fp32(3) - 236.0 / 43.0) < 1e-9, f"{d2.rate_vs_fp32(3):.2f}x")
    check("band truncation counts as a quantising variant", d2.family == "qfp", d2.family)
    check("prune extends to 20x", abs(parse_spec("p05").rate_vs_fp32(3) - 20.0) < 1e-9,
          f"{parse_spec('p05').rate_vs_fp32(3):.2f}x")

    C.log("== quantisers ==")
    sp = _synthetic_splats(2000, deg)
    ref = _synthetic_splats(2000, deg)
    same = apply_quant(sp, parse_spec("clean"))
    check("clean is a no-op", all(torch.equal(getattr(sp, k), getattr(same, k))
                                 for k in ("means", "scales", "quats", "opacities", "sh0", "shN")))
    d = apply_quant(sp, parse_spec("q2_g8"))
    check("input not mutated by quantisation",
          all(torch.equal(getattr(sp, k), getattr(ref, k))
              for k in ("means", "scales", "quats", "opacities", "sh0", "shN")),
          "base asset must stay fp32 after a variant is built")
    check("quantised variant differs from base",
          not torch.equal(d.means, sp.means) and not torch.equal(d.shN, sp.shN))

    # per-group distortion must fall as bits rise, and 12-bit geometry must be small
    err = {}
    for attr, bits_list in (("means", (6, 8, 10, 12, 16)),
                            ("scales", (6, 8, 10, 12)),
                            ("quats", (6, 8, 10, 12)),
                            ("opacities", (4, 6, 8, 10))):
        alias = "opac" if attr == "opacities" else attr
        vals = []
        for b in bits_list:
            q = apply_quant(sp, parse_spec(f"iso_{alias}{b}"))
            d = float((getattr(q, attr) - getattr(sp, attr)).abs().mean())
            vals.append(d)
            err[(attr, b)] = d
        check(f"{attr} error monotone in bits",
              all(vals[i] > vals[i + 1] for i in range(len(vals) - 1)),
              " ".join(f"{b}:{v:.2e}" for b, v in zip(bits_list, vals)))

    q = apply_quant(sp, parse_spec("q4_g12"))
    check("quats stay unit norm",
          float((q.quats.norm(dim=-1) - 1).abs().max()) < 1e-4,
          f"{float((q.quats.norm(dim=-1) - 1).abs().max()):.2e}")
    check("means 12-bit grid error below half a step",
          err[("means", 12)] <= 0.5 * float(sp.means.max() - sp.means.min()) / (2 ** 12 - 1) + 1e-9,
          f"{err[('means', 12)]:.3e}")

    import dump_artifacts as D
    sh_err = {}
    for b in (8, 6, 4, 2):
        qq = D._quantize_splats(sp.clone(), torch, bits=b)
        sh_err[b] = float((qq.shN - sp.shN).abs().max())
    check("SH perturbation grows as bits drop",
          sh_err[8] < sh_err[6] < sh_err[4] < sh_err[2],
          " ".join(f"{b}:{v:.2e}" for b, v in sh_err.items()))
    check("SH 4-bit perturbation stays relative (<= 1/8 of block max)",
          sh_err[4] <= 0.13 * float(sp.shN.abs().amax(dim=(1, 2)).max()),
          f"{sh_err[4]:.3e}")

    C.log("== cluster-relative positions ==")
    c12 = parse_spec("c12_o8_sh3")
    check("c-prefix keeps the full name", c12.name == "c12_o8_sh3", c12.name)
    check("c12 sets the cluster bit budget", c12.means_cluster_bits == 12,
          str(c12.means_cluster_bits))
    check("c12 does not fall back to a global means grid", "means" not in c12.geo, str(c12.geo))
    check("cluster codes count as quantising", c12.family == "qfp", c12.family)
    check("cluster header is charged per primitive",
          abs(c12.bytes_per_prim(deg) - (3 * 12 / 8 + CLUSTER_HEADER_PER_PRIM + 8 + 20.0)) < 1e-9,
          f"{c12.bytes_per_prim(deg):.3f} B")
    check("m and c are mutually exclusive",
          parse_spec("c12_o8_sh3").geo.get("means") is None)
    check("c-bits are range checked",
          _raises(lambda: parse_spec("c2_o8_sh3")) and _raises(lambda: parse_spec("c40_o8_sh3")),
          "6..24")
    check("cluster is cheaper than a 16-bit global grid",
          c12.bytes_per_prim(deg) < parse_spec("m16_o8_sh3").bytes_per_prim(deg),
          f"{c12.bytes_per_prim(deg):.2f} vs {parse_spec('m16_o8_sh3').bytes_per_prim(deg):.2f}")

    # the point of the codec: at equal bits, a local block must beat the scene grid
    # on error, because the error scale is the block extent, not the scene extent.
    far = sp.means * 20.0            # keep the geometry, blow up the extent
    g12 = float((quantize_grid(far, 12) - far).abs().mean())
    c12e = float((quantize_cluster(far, 12) - far).abs().mean())
    check("cluster beats the scene grid at equal bits", c12e < g12,
          f"cluster {c12e:.3e} vs grid {g12:.3e}")
    check("cluster error shrinks with bits",
          float((quantize_cluster(sp.means, 8) - sp.means).abs().mean()) >
          float((quantize_cluster(sp.means, 12) - sp.means).abs().mean()) >
          float((quantize_cluster(sp.means, 16) - sp.means).abs().mean()),
          "")
    check("cluster keeps every primitive in place-order",
          quantize_cluster(sp.means, 12).shape == sp.means.shape)
    check("cluster quantiser is deterministic",
          torch.equal(quantize_cluster(sp.means, 12), quantize_cluster(sp.means, 12)))
    check("morton order is a permutation",
          int(morton_order(sp.means).sort()[0].sub(torch.arange(sp.means.shape[0],
                                                               device=sp.means.device)).abs().max()) == 0)

    C.log("== vector-quantised SH (M9) ==")
    ref_flat = _sh_flat(sp)
    st_vq = SceneState(base=sp)
    cb6 = st_vq.codebook(6, 3)
    check("codebook has 2**b centres of 3K coefficients", tuple(cb6.shape) == (64, 48),
          str(tuple(cb6.shape)))
    check("codebook training is deterministic",
          torch.equal(cb6, SceneState(base=sp).codebook(6, 3)))
    qv = apply_quant(sp, parse_spec("vq6_c8_o8"), st_vq)
    rec = _sh_flat(qv)
    dmin = (rec[:, None, :] - cb6[None, :, :]).abs().amax(dim=2).amin(dim=1)
    check("every stored SH block is one dictionary entry", float(dmin.max()) < 1e-5,
          f"max deviation {float(dmin.max()):.2e}")

    def _vq_err(bits):
        st = SceneState(base=sp)
        q = apply_quant(sp, parse_spec(f"vq{bits}_c8_o8"), st)
        return float((_sh_flat(q) - ref_flat).abs().mean())

    e4, e6, e8 = _vq_err(4), _vq_err(6), _vq_err(8)
    check("VQ error shrinks with the codebook", e4 > e6 > e8, f"{e4:.2e} {e6:.2e} {e8:.2e}")
    b_vq = parse_spec("vq12_c8_o8").bytes_per_prim(3, n_stored=1_000_000)
    want = (8.0 + 3 * 8 / 8 + CLUSTER_HEADER_PER_PRIM + 12 / 8 + 4096 * 48 / 1e6
            + 64.0 / 1e6)           # grid headers, 8 B per coded component
    check("codebook is charged to the asset",
          abs(b_vq - want) < 1e-9, f"{b_vq:.4f} B vs {want:.4f}")
    check("dictionary beats scalar SH on paper",
          b_vq < parse_spec("c8_o8_sh3").bytes_per_prim(3, n_stored=1_000_000),
          f"{b_vq:.2f} vs {parse_spec('c8_o8_sh3').bytes_per_prim(3, n_stored=1_000_000):.2f}")
    check("vq and scalar SH are exclusive", _raises(lambda: parse_spec("vq12_sh4_c8_o8")))
    check("codebook width is range checked",
          _raises(lambda: parse_spec("vq2_c8_o8")) and _raises(lambda: parse_spec("vq20_c8_o8")),
          "4..16")
    check("canvas keeps its bands when the dictionary truncates",
          abs(float(_sh_flat(apply_quant(sp, parse_spec("d2_vq8_c8_o8"),
                                         SceneState(base=sp)))[:, 27:].abs().max())) == 0.0)

    C.log("== residual vector quantisation (M10) ==")
    st_r = SceneState(base=sp)
    pair = st_r.codebook_pair(6, 2, 3)
    check("two codebooks of the registered widths", [tuple(c.shape) for c in pair]
          == [(64, 48), (4, 48)], str([tuple(c.shape) for c in pair]))
    check("residual codebook training is deterministic",
          torch.equal(pair[1], SceneState(base=sp).codebook_pair(6, 2, 3)[1]))
    qr = apply_quant(sp, parse_spec("rvq6-2_c8_o8"), st_r)
    rec_r = _sh_flat(qr)[:, :48]

    # The residual stage is only worth its index bits if the reconstruction really is
    # ``centre1 + centre2``: every row must land on such a sum.
    # A two-stage reconstruction lies within the residual codebook's reach of *some*
    # first-stage centre; it is not necessarily nearest to one, because the second
    # stage can pull a row into another centre's cell.
    near1 = (rec_r[:, None, :] - pair[0][None, :, :]).abs().amax(dim=2).amin(dim=1)
    reach = float(pair[1].abs().amax()) + 1e-5
    check("every stored block is one centre plus a residual entry",
          float(near1.max()) <= reach,
          f"max distance to a first-stage centre {float(near1.max()):.3f} <= {reach:.3f}")

    def _err(spec):
        st = SceneState(base=sp)
        q = apply_quant(sp, parse_spec(spec), st)
        return float((_sh_flat(q) - ref_flat).abs().mean())

    # Same total index width, spent as 8 or as 6+2: the split must not be worse than
    # a single codebook of the same width, and both must beat a narrower one.
    e_single8, e_rvq62, e_single6 = _err("vq8_c8_o8"), _err("rvq6-2_c8_o8"), _err("vq6_c8_o8")
    check("two stages at 8 total bits beat a 6-bit single stage",
          e_rvq62 < e_single6, f"{e_rvq62:.3e} vs {e_single6:.3e}")
    check("residual stage is a real refinement (not a no-op)",
          e_rvq62 < e_single8 * 1.5, f"rvq 6+2 {e_rvq62:.3e} vs single 8 {e_single8:.3e}")

    b_rvq = parse_spec("rvq8-4_c8_o8").bytes_per_prim(3, n_stored=1_000_000)
    want_r = (8.0 + 3 * 8 / 8 + CLUSTER_HEADER_PER_PRIM + (8 + 4) / 8
              + (256 + 16) * 48 / 1e6 + 64.0 / 1e6)
    check("both codebooks are charged", abs(b_rvq - want_r) < 1e-9,
          f"{b_rvq:.4f} B vs {want_r:.4f}")
    check("rvq excludes vq and scalar SH",
          _raises(lambda: parse_spec("rvq8-4_vq12_c8_o8"))
          and _raises(lambda: parse_spec("rvq8-4_c8_o8_sh4")))
    check("rvq widths are range checked",
          _raises(lambda: parse_spec("rvq1-4_c8_o8"))
          and _raises(lambda: parse_spec("rvq8-20_c8_o8")))
    check("bands above the truncation are zeroed under rvq",
          abs(float(_sh_flat(apply_quant(sp, parse_spec("d2_rvq8-4_c8_o8"),
                                        SceneState(base=sp)))[:, 27:].abs().max())) == 0.0)

    # ---- M11: per-primitive mode selection -------------------------------------
    C.log("== mode selection (msc) ==")
    spec_m = parse_spec("msc12-4-a1_c8_o8")
    check("msc parsed", spec_m.sh_msc == {"b_dict": 12, "b_scalar": 4, "alpha": 1}
          and spec_m.means_cluster_bits == 8, str(spec_m.sh_msc))
    _n = 4_000_000
    _cols4 = sh_cols(3) * FP32_BITS / 8.0
    def _nonsh(spec_, deg_):
        """Total bytes minus whatever the SH block costs at fp32."""
        return spec_.bytes_per_prim(deg_, _n) - _cols4
    _peak = parse_spec("c8_o8_sh32").bytes_per_prim(3, _n)
    check("msc charges the 2-bit flag",
          abs((spec_m.bytes_per_prim(3, _n) - (_peak - _cols4))
              - msc_bytes_per_prim(3, 12, 4, (0.0, 1.0, 0.0), _n)) < 1e-9,
          f"{spec_m.bytes_per_prim(3, _n):.4f}")
    check("msc excludes vq/rvq/scalar sh",
          _raises(lambda: parse_spec("msc12-4-a1_vq12_c8_o8"))
          and _raises(lambda: parse_spec("msc12-4-a1_c8_o8_sh4")))
    st_m = SceneState(base=sp)
    deg_m = int(sp.sh_degree)
    cols_m = sh_cols(deg_m)
    flat_m = _sh_flat(sp)[:, :cols_m]
    mixes = {}
    for a in (1, 4):
        spx = parse_spec(f"msc12-4-a{a}_c8_o8")
        _, _, _, frac = msc_select(sp, spx, st_m, deg_m)
        mixes[a] = frac
        check(f"msc a{a} mix sums to one", abs(sum(frac) - 1.0) < 1e-6, f"{frac}")
        spq = apply_quant(sp, spx, st_m)
        check(f"msc a{a} records its realised mix",
              spx.msc_frac is not None and abs(sum(spx.msc_frac) - 1.0) < 1e-6,
              str(spx.msc_frac))
        _n2 = int(sp.n)
        _c2 = sh_cols(deg_m) * FP32_BITS / 8.0
        _peak2 = parse_spec("c8_o8_sh32").bytes_per_prim(deg_m, _n2)
        check(f"msc a{a} charges the realised mix",
              abs((spx.bytes_per_prim(deg_m, _n2) - (_peak2 - _c2))
                  - msc_bytes_per_prim(deg_m, 12, 4, spx.msc_frac, _n2)) < 1e-9,
              f"{spx.bytes_per_prim(deg_m, _n2):.4f} B")
        rec = _sh_flat(spq)[:, :cols_m]
        err = float(((flat_m - rec) ** 2).sum(1).mean())
        check(f"msc a{a} beats zeroing everything", err < float((flat_m ** 2).sum(1).mean()),
              f"{err:.4e}")
    check("a dearer byte zeroes more primitives",
          mixes[4][0] >= mixes[1][0], f"{mixes[1]} vs {mixes[4]}")
    check("bands above the truncation are zeroed under msc",
          abs(float(_sh_flat(apply_quant(sp, parse_spec("d2_msc12-4-a1_c8_o8"),
                                         st_m))[:, 27:].abs().max())) == 0.0)

    C.log("== end-to-end analysis smoke ==")
    dump_dir = _write_synth_dump(os.path.join(_here_artifacts(), "_m1_selftest"))
    import m1_analyse
    res = m1_analyse.analyse_dump(dump_dir, rates=(2.0, 3.0, 5.0), n_splits=40, verbose=True)
    crit = res["summary"]["criteria"]
    check("D1 present", "D1_coverage_dominance" in crit, str(list(crit)))
    check("synthetic dump yields sensible rates", all(
        r["rows"] for r in res["scenes"]), "")

    C.log("=" * 60)
    if fails:
        C.log(f"FAILED {len(fails)}: {fails}")
        return 1
    C.log("ALL PASS")
    return 0


def _here_artifacts() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")


def _write_synth_dump(out_dir: str, flip: bool = False) -> str:
    """A tiny npz in the A4/M1 layout so the analyser can be exercised on CPU.

    The variant *names* are the real QFP names.  ``flip=False`` builds a world
    where precision-first wins (pruning degrades with how much it removes, while
    quantisation costs little); ``flip=True`` builds the opposite world, where
    pruning is nearly free and quantisation is expensive, so the analyser's
    verdicts can be tested in both directions without any GPU work.
    """
    C = _C()
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(0)
    n_views, H, W = 4, 32, 32
    names = [v for v in DEFAULT_VARIANTS.split(",") if v]
    specs = [parse_spec(n) for n in names]
    sev = {}
    for s in specs:
        # magnitudes are calibrated so that coverage (the 10 % tail of a
        # uniform[0, 0.2] residual) moves by ~1 pp per 0.002 of added residual,
        # which is what makes a "near-lossless shelf" reachable at all.
        prune_sev = 0.0008 if flip else 0.026
        quant_sev = 0.020 if flip else 0.0008
        if s.family == "clean":
            sev[s.name] = 0.0
        elif s.family == "prune":
            sev[s.name] = prune_sev * (1.0 - s.keep) ** 0.7
        elif s.family == "joint":
            sev[s.name] = prune_sev * (1.0 - s.keep) ** 0.7 + 0.0008
        elif s.family == "iso":
            sev[s.name] = quant_sev
        else:                                   # qfp
            b = s.sh_bits
            sev[s.name] = quant_sev + 0.0004 * max(0.0, 8 - b) / 8.0
    m = len(names)
    base = rng.random((n_views, H, W), dtype=np.float32) * 0.2
    resid = np.zeros((m, n_views, H, W), np.float16)
    for i, s in enumerate(specs):
        resid[i] = (base + sev[s.name] * rng.random((n_views, H, W), dtype=np.float32)).astype(np.float16)
    gt = (rng.random((n_views, H, W), dtype=np.float32) * 0.2).astype(np.float16)
    c2w = np.tile(np.eye(4, dtype=np.float32), (n_views, 1, 1))
    K = np.tile(np.array([[30.0, 0, W / 2], [0, 30.0, H / 2], [0, 0, 1]], np.float32), (n_views, 1, 1))
    stats = {}
    for s in specs:
        stats[s.name] = dict(n_primitives=2000,
                             psnr=30.0 - 6.0 * sev[s.name],
                             mean_alpha=0.5, resid_median=0.01, resid_mean=0.01,
                             psnr_views=[30.0 - 6.0 * sev[s.name]] * n_views,
                             resid_mean_views=[0.01] * n_views,
                             resid_median_views=[0.01] * n_views,
                             alpha_views=[0.5] * n_views,
                             bytes_per_prim=float(s.bytes_per_prim(3)),
                             keep=float(s.keep),
                             ratio_vs_fp32=float(s.rate_vs_fp32(3)),
                             family=s.family,
                             ssim=None if s.family != "clean" else 0.9,
                             lpips=None)
    pack_args = type("A", (), dict(downsample=1, factor=4, alpha=0.1, cal_frac=0.5,
                                   no_compress=True, budget_mb=900))()
    meta = dict(dry_run=True, alpha=0.1, cal_frac=0.5, sh_degree=3)
    import dump_artifacts as D
    D.pack_and_save(out_dir, "synth", names, np.stack([resid[i].astype(np.float32) for i in range(m)]),
                    np.stack([resid[i].astype(np.float32) for i in range(m)]),
                    gt, np.arange(n_views), c2w, K, stats, meta,
                    np.zeros((10, 3), np.float32), np.zeros((10,), np.float32), pack_args)
    C.json_dump(os.path.join(out_dir, "m1_manifest.json"),
                dict(scenes=[dict(scene="synth", variants=stats, sh_degree=3,
                                  fp32_bytes_per_prim=236.0)]))
    return out_dir


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="M1/QFP precision-first rate-distortion")
    ap.add_argument("--archive", default="/workspace/data/out3dgs")
    ap.add_argument("--scenes", default="bicycle,flowers,stump,treehill")
    ap.add_argument("--out", default="/workspace/res/m1")
    ap.add_argument("--ply-pattern",
                    default="{archive}/output/{scene}/point_cloud/iteration_40000/point_cloud.ply")
    ap.add_argument("--variants", default=DEFAULT_VARIANTS)
    ap.add_argument("--variant-set", default="custom",
                    choices=sorted(VARIANT_SETS),
                    help="registered grid to realise: m1 = QFP grid, m2 = attribute "
                         "ladder, m3 = extended prune + band/bit comparison "
                         "(a --variants that differs from all of them still wins)")
    ap.add_argument("--factor", type=int, default=4)
    ap.add_argument("--cal-frac", type=float, default=0.5)
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--n-fisher-views", type=int, default=4)
    ap.add_argument("--gt-convention", default="archive", choices=["archive", "normalized"])
    ap.add_argument("--downsample", type=int, default=1)
    ap.add_argument("--prim-sample", type=int, default=200000)
    ap.add_argument("--budget-mb", type=float, default=900)
    ap.add_argument("--no-compress", action="store_true")
    ap.add_argument("--max-views", type=int, default=0)
    ap.add_argument("--fidelity", action="store_true", help="also compute SSIM/LPIPS")
    ap.add_argument("--lpips-net", default="alex", choices=["alex", "vgg"])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.selftest:
        return selftest(args)
    run_real(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
