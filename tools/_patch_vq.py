"""Add vector-quantised SH (a per-asset view-dependent dictionary) to qfp_rd.py.

Idempotent: re-running is a no-op once the markers are present.
"""
import io
import re
import sys

P = r"D:\3dsg_1\experiments\qfp_rd.py"
s = io.open(P, encoding="utf-8").read()
orig = s

# ---------------------------------------------------------------- constants
CONST_ANCHOR = ('CLUSTER_HEADER_PER_PRIM = CLUSTER_HEADER_BYTES / float(CLUSTER_SIZE)\n')
CONST_ADD = CONST_ANCHOR + '''#: vector-quantised SH: every primitive stores an index into a per-asset codebook
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
'''
if "SH_VQ_CENTROID_BYTES" not in s:
    assert CONST_ANCHOR in s
    s = s.replace(CONST_ANCHOR, CONST_ADD, 1)

# ---------------------------------------------------------------- bytes model
OLD_SIG = '''def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None) -> float:'''
NEW_SIG = '''def bytes_per_prim(sh_degree: int, sh_bits: int, geo: dict,
                   means_cbits: int = None, sh_vq_bits: int = None,
                   n_stored: int = None) -> float:'''
if OLD_SIG in s:
    s = s.replace(OLD_SIG, NEW_SIG, 1)

OLD_BODY = '''    cols = sh_cols(sh_degree)
    if sh_bits >= FP32_BITS:
        b_sh = cols * 4.0
    else:
        b_sh = cols * sh_bits / 8.0 + SH_SCALE_BYTES'''
NEW_BODY = '''    cols = sh_cols(sh_degree)
    if sh_vq_bits is not None:
        b_sh = int(sh_vq_bits) / 8.0
        b_sh += vq_codebook_bytes(sh_vq_bits, cols) / float(n_stored or VQ_NOMINAL_PRIMS)
    elif sh_bits >= FP32_BITS:
        b_sh = cols * 4.0
    else:
        b_sh = cols * sh_bits / 8.0 + SH_SCALE_BYTES'''
if OLD_BODY in s:
    s = s.replace(OLD_BODY, NEW_BODY, 1)

# ---------------------------------------------------------------- QSpec
OLD_F = '''    means_cluster_bits: int = None
'''
NEW_F = '''    means_cluster_bits: int = None
    #: width of the codebook index, i.e. SH is stored as one dictionary entry per
    #: primitive instead of ``sh_cols`` independent coefficients.  Mutually exclusive
    #: with ``sh_bits``; the codebook itself is charged per asset.
    sh_vq_bits: int = None
'''
if "sh_vq_bits: int = None" not in s:
    assert OLD_F in s
    s = s.replace(OLD_F, NEW_F, 1)

OLD_FAM = '''        is_quant = (self.sh_bits < FP32_BITS or self.sh_degree_out is not None'''
NEW_FAM = '''        is_quant = (self.sh_bits < FP32_BITS or self.sh_vq_bits is not None
                    or self.sh_degree_out is not None'''
if "self.sh_vq_bits is not None\n                    or self.sh_degree_out" not in s:
    assert OLD_FAM in s
    s = s.replace(OLD_FAM, NEW_FAM, 1)

OLD_BPP = '''    def bytes_per_prim(self, sh_degree: int) -> float:
        """Bytes for one *kept* primitive, at the degree the variant stores."""
        return bytes_per_prim(self.out_degree(sh_degree), self.sh_bits, self.geo,
                              means_cbits=self.means_cluster_bits)

    def rate_vs_fp32(self, sh_degree: int) -> float:
        """Total-file compression ratio: a prune variant keeps only ``keep`` of them."""
        return fp32_bytes_per_prim(sh_degree) / (self.bytes_per_prim(sh_degree) * self.keep)'''
NEW_BPP = '''    def bytes_per_prim(self, sh_degree: int, n_stored: int = None) -> float:
        """Bytes for one *kept* primitive, at the degree the variant stores."""
        return bytes_per_prim(self.out_degree(sh_degree), self.sh_bits, self.geo,
                              means_cbits=self.means_cluster_bits,
                              sh_vq_bits=self.sh_vq_bits, n_stored=n_stored)

    def codebook_bytes(self, sh_degree: int, n_stored: int = None) -> float:
        """Share of the file that the SH dictionary takes (0 for scalar variants)."""
        if self.sh_vq_bits is None:
            return 0.0
        return vq_codebook_bytes(self.sh_vq_bits, sh_cols(self.out_degree(sh_degree)))

    def rate_vs_fp32(self, sh_degree: int, n_stored: int = None) -> float:
        """Total-file compression ratio: a prune variant keeps only ``keep`` of them."""
        bpp = self.bytes_per_prim(sh_degree, n_stored=n_stored)
        return fp32_bytes_per_prim(sh_degree) / (bpp * self.keep)'''
if OLD_BPP in s:
    s = s.replace(OLD_BPP, NEW_BPP, 1)

# ---------------------------------------------------------------- parse_spec
OLD_LAD = '''        geo, sh_bits, seen = {}, FP32_BITS, set()
        cbits = None'''
NEW_LAD = '''        geo, sh_bits, seen = {}, FP32_BITS, set()
        cbits = None
        vq_bits = None'''
if "vq_bits = None\n" not in s:
    assert OLD_LAD in s
    s = s.replace(OLD_LAD, NEW_LAD, 1)

OLD_TOK = '''            elif tok.startswith("sh") and tok[2:].isdigit():
                sh_bits = int(tok[2:])
                seen.add("sh")'''
NEW_TOK = '''            elif tok.startswith("sh") and tok[2:].isdigit():
                sh_bits = int(tok[2:])
                seen.add("sh")
            elif tok.startswith("vq") and tok[2:].isdigit():
                vq_bits = int(tok[2:])
                if not 4 <= vq_bits <= 16:
                    raise ValueError(f"codebook index width out of range in {name}")
                seen.add("sh")'''
if 'tok.startswith("vq")' not in s:
    assert OLD_TOK in s
    s = s.replace(OLD_TOK, NEW_TOK, 1)

OLD_RET = '''        for b in list(geo.values()) + [sh_bits] + ([cbits] if cbits else []):
            if not 1 <= b <= 32:
                raise ValueError(f"bad bits in {name}")
        if cbits is not None and not 6 <= cbits <= 24:
            raise ValueError(f"cluster position bits out of range in {name}")
        return mk(keep=_keep, sh_bits=sh_bits, geo=geo, means_cluster_bits=cbits)'''
NEW_RET = '''        if vq_bits is not None and sh_bits < FP32_BITS:
            raise ValueError(f"vq and sh are exclusive in {name}")
        for b in list(geo.values()) + [sh_bits] + ([cbits] if cbits else []):
            if not 1 <= b <= 32:
                raise ValueError(f"bad bits in {name}")
        if cbits is not None and not 6 <= cbits <= 24:
            raise ValueError(f"cluster position bits out of range in {name}")
        return mk(keep=_keep, sh_bits=sh_bits, geo=geo, means_cluster_bits=cbits,
                  sh_vq_bits=vq_bits)'''
if OLD_RET in s:
    s = s.replace(OLD_RET, NEW_RET, 1)

# ---------------------------------------------------------------- quantisers
Q_ANCHOR = '''def _logit(p, torch):
    p = p.clamp(1e-6, 1 - 1e-6)
    return torch.log(p / (1.0 - p))
'''
Q_ADD = Q_ANCHOR + '''

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
'''
if "def quantize_vq(" not in s:
    assert Q_ANCHOR in s
    s = s.replace(Q_ANCHOR, Q_ADD, 1)

# ---------------------------------------------------------------- apply_quant
OLD_AQ = '''def apply_quant(sp, spec: QSpec):
    """Return a quantised clone of ``sp`` for ``spec`` (never mutates the input)."""
    import torch
    out = sp.clone()
    if spec.sh_bits < FP32_BITS:'''
NEW_AQ = '''def apply_quant(sp, spec: QSpec, state=None):
    """Return a quantised clone of ``sp`` for ``spec`` (never mutates the input)."""
    import torch
    out = sp.clone()
    if spec.sh_vq_bits is not None:
        if state is None:
            raise RuntimeError("vector-quantised SH needs the scene state (codebook)")
        deg_out = spec.out_degree(int(base_degree(sp)))
        quantize_vq(out, state.codebook(spec.sh_vq_bits, deg_out), deg_out)
    elif spec.sh_bits < FP32_BITS:'''
if OLD_AQ in s:
    s = s.replace(OLD_AQ, NEW_AQ, 1)

HELP = '''

def base_degree(sp) -> int:
    """SH degree a ``Splats`` object currently holds."""
    return int(getattr(sp, "sh_degree", 3))
'''
if "def base_degree(" not in s:
    s = s.replace("\n\ndef apply_quant(", HELP + "\n\ndef apply_quant(", 1)

# ---------------------------------------------------------------- SceneState
OLD_SS = '''@dataclass
class SceneState:
    base: object
    fisher: np.ndarray = None
    cache: dict = field(default_factory=dict)
'''
NEW_SS = '''@dataclass
class SceneState:
    base: object
    fisher: np.ndarray = None
    cache: dict = field(default_factory=dict)

    def codebook(self, vq_bits: int, deg_out: int):
        """SH dictionary for this asset, trained once and reused by every variant."""
        key = ("cb", int(vq_bits), int(deg_out))
        if key not in self.cache:
            self.cache[key] = build_codebook(self.base, vq_bits, deg_out)
        return self.cache[key]
'''
if "def codebook(self, vq_bits" not in s:
    assert OLD_SS in s
    s = s.replace(OLD_SS, NEW_SS, 1)

# ---------------------------------------------------------------- realize
OLD_RZ = '''    if spec.sh_bits < FP32_BITS or spec.geo:
        sp = apply_quant(sp, spec)
    return sp, extra'''
NEW_RZ = '''    if spec.sh_bits < FP32_BITS or spec.geo or spec.sh_vq_bits is not None \\
            or spec.means_cluster_bits is not None:
        sp = apply_quant(sp, spec, st)
    return sp, extra'''
if OLD_RZ in s:
    s = s.replace(OLD_RZ, NEW_RZ, 1)

# ---------------------------------------------------------------- run_real accounting
OLD_ACC = '''            bpp = spec.bytes_per_prim(deg)
            stats[spec.name].update(
                bytes_per_prim=float(bpp),
                keep=float(spec.keep),
                ratio_vs_fp32=float(spec.rate_vs_fp32(deg)),'''
NEW_ACC = '''            n_st = int(sp.n)
            bpp = spec.bytes_per_prim(deg, n_stored=n_st)
            stats[spec.name].update(
                bytes_per_prim=float(bpp),
                codebook_bytes=float(spec.codebook_bytes(deg)),
                keep=float(spec.keep),
                ratio_vs_fp32=float(spec.rate_vs_fp32(deg, n_stored=n_st)),'''
if OLD_ACC in s:
    s = s.replace(OLD_ACC, NEW_ACC, 1)

OLD_LOG = '''                  f"B/pr={bpp:6.1f} ({spec.rate_vs_fp32(deg):4.2f}x) "'''
NEW_LOG = '''                  f"B/pr={bpp:6.1f} ({spec.rate_vs_fp32(deg, n_stored=int(sp.n)):4.2f}x) "'''
if OLD_LOG in s:
    s = s.replace(OLD_LOG, NEW_LOG, 1)

OLD_WL = '''            for k in ("bytes_per_prim", "keep", "ratio_vs_fp32", "family",'''
NEW_WL = '''            for k in ("bytes_per_prim", "codebook_bytes", "keep", "ratio_vs_fp32",
                      "family",'''
if OLD_WL in s:
    s = s.replace(OLD_WL, NEW_WL, 1)

# ---------------------------------------------------------------- variant grid
M9 = '''

#: M9 grid: the view-dependent block is now a dictionary lookup.  M7 left the 7-13x
#: region constrained by SH bit width (3->2 bits costs 1.86 pp), and M8 showed that
#: spending the same bytes on fewer bands is a wash; the remaining redundancy is
#: *across* primitives (most blocks are near zero, similar materials share a curve),
#: which is exactly what a vector quantiser can take.
M9_VARIANTS = ",".join([
    "clean",
    # scalar anchors from M7/M8: the frontier the dictionary has to beat
    "c10_o8_sh3", "c12_o8_sh2",
    # dictionary width sweep at cluster-10 positions
    "vq8_c8_o8", "vq10_c8_o8", "vq12_c8_o8", "vq14_c8_o8",
    # positions matter less once the dictionary does the work
    "vq10_c10_o8", "vq12_c10_o8", "vq12_c12_o8",
    # band truncation on top of the dictionary
    "d2_vq12_c8_o8",
    # hybrid at the top of the range
    "p30_vq12_c8_o8",
])

'''
if "M9_VARIANTS" not in s:
    anchor = "\n\ndef _variants(args) -> list:"
    s = s.replace(anchor, M9 + "\ndef _variants(args) -> list:", 1)

OLD_VAR = '''        if getattr(args, "variants", None) not in (None, DEFAULT_VARIANTS,
                                                  AFQ_VARIANTS, M3_VARIANTS,
                                                  M7_VARIANTS, M8_VARIANTS):
            return [v.strip() for v in args.variants.split(",") if v.strip()]
        grid = {"m1": DEFAULT_VARIANTS, "m2": AFQ_VARIANTS, "m3": M3_VARIANTS,
                "m7": M7_VARIANTS, "m8": M8_VARIANTS}[preset]'''
NEW_VAR = '''        if getattr(args, "variants", None) not in (None, DEFAULT_VARIANTS,
                                                  AFQ_VARIANTS, M3_VARIANTS,
                                                  M7_VARIANTS, M8_VARIANTS,
                                                  M9_VARIANTS):
            return [v.strip() for v in args.variants.split(",") if v.strip()]
        grid = {"m1": DEFAULT_VARIANTS, "m2": AFQ_VARIANTS, "m3": M3_VARIANTS,
                "m7": M7_VARIANTS, "m8": M8_VARIANTS, "m9": M9_VARIANTS}[preset]'''
if OLD_VAR in s:
    s = s.replace(OLD_VAR, NEW_VAR, 1)

OLD_CH = 'choices=["custom", "m1", "m2", "m3", "m7", "m8"]'
NEW_CH = 'choices=["custom", "m1", "m2", "m3", "m7", "m8", "m9"]'
if OLD_CH in s:
    s = s.replace(OLD_CH, NEW_CH, 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("changed" if s != orig else "unchanged", len(s), "chars")
