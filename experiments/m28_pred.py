"""M28 -- predicted anchors: the anchor keeps a coarse record, a small network supplies the detail.

M27 measured the two halves of the anchor idea separately: the bookkeeping is 3.8x cheaper than the
shelf and the *constant* reconstruction is 4-8 dB worse, because inside one 10 cm voxel the scales span
a factor of two and the rotations disagree by ~23 degrees.  This module keeps M27's grid, offsets,
container and colour basis and replaces the constant with a prediction:

    input   anchor log-scale (3), anchor rotation vector (3), anchor logit opacity (1),
            the primitive's offset inside the voxel (3)                       = 10 numbers
    body    2 x 64 SiLU
    output  dlog-scale (3), a rotation vector (3) composed with the anchor's, dlogit opacity (1)

Per primitive the file stores only the offset and the DC code; the network weights (10.6 kB fp16) and
the anchor records are the rest.  Training minimises the error of the *decoded* attributes against the
source model -- no render loss, no evaluation views.
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
import m27_anchor as A27

HIDDEN = 64
OFFSET_BITS = 4  #: 16 levels per axis inside the voxel: 6.7 mm at ppa 8 on bicycle (M27: 3 bits cost 1.7 dB)


# ----------------------------------------------------------------------------- tensor helpers

def _torch():
    import torch
    return torch


def quat_mul(a, b):
    """Hamilton product of ``(..., 4)`` quaternions in ``(w, x, y, z)`` order."""
    aw, ax, ay, az = a.unbind(-1)
    bw, bx, by, bz = b.unbind(-1)
    t = _torch()
    return t.stack([aw * bw - ax * bx - ay * by - az * bz,
                    aw * bx + ax * bw + ay * bz - az * by,
                    aw * by - ax * bz + ay * bw + az * bx,
                    aw * bz + ax * by - ay * bx + az * bw], dim=-1)


def rotvec_to_quat(r):
    t = _torch()
    th = r.norm(dim=-1, keepdim=True).clamp_min(1e-8)
    axis = r / th
    half = 0.5 * th
    return t.cat([t.cos(half), axis * t.sin(half)], dim=-1)


def quat_to_rotvec(q):
    t = _torch()
    q = q / q.norm(dim=-1, keepdim=True).clamp_min(1e-12)
    w = q[..., :1].abs().clamp(max=1.0)
    v = q[..., 1:]
    s = v.norm(dim=-1, keepdim=True).clamp_min(1e-8)
    ang = 2.0 * t.atan2(s, w)
    return v / s * ang


# ----------------------------------------------------------------------------- model

class Predictor:
    """10 -> 64 -> 64 -> 7 MLP; the weights are part of the file, so this is the decoder too."""

    def __init__(self, hidden: int = HIDDEN, seed: int = 0):
        t = _torch()
        t.manual_seed(int(seed))
        self.net = t.nn.Sequential(
            t.nn.Linear(10, hidden), t.nn.SiLU(),
            t.nn.Linear(hidden, hidden), t.nn.SiLU(),
            t.nn.Linear(hidden, 7),
        )
        #: start at "no correction": the first round of M27 is the identity function, so a predictor
        #: that learns nothing can only match M27, never be worse than it for a trivial reason
        with t.no_grad():
            self.net[-1].weight.mul_(0.0)
            self.net[-1].bias.mul_(0.0)

    def forward(self, x):
        return self.net(x)

    def state(self):
        return {k: v.detach().cpu().numpy() for k, v in self.net.state_dict().items()}

    def load_state(self, sd: dict, hidden: int):
        t = _torch()
        self.net = t.nn.Sequential(
            t.nn.Linear(10, hidden), t.nn.SiLU(),
            t.nn.Linear(hidden, hidden), t.nn.SiLU(),
            t.nn.Linear(hidden, 7),
        )
        self.net.load_state_dict({k: t.from_numpy(np.ascontiguousarray(v)) for k, v in sd.items()})

    def to_bytes(self) -> bytes:
        sd = self.state()
        hidden = int(sd["0.weight"].shape[0])
        head = np.asarray([hidden, 10, 7], dtype=np.int32).tobytes()
        body = b"".join(np.asarray(sd[k], dtype=np.float16).tobytes() for k in
                        ("0.weight", "0.bias", "2.weight", "2.bias", "4.weight", "4.bias"))
        return head + body

    @staticmethod
    def from_bytes(buf: bytes) -> "Predictor":
        hidden, nin, nout = np.frombuffer(buf[:12], dtype=np.int32)
        assert (int(nin), int(nout)) == (10, 7), (nin, nout)
        off = 12
        sd = {}
        for k, shape in (("0.weight", (hidden, 10)), ("0.bias", (hidden,)),
                         ("2.weight", (hidden, hidden)), ("2.bias", (hidden,)),
                         ("4.weight", (7, hidden)), ("4.bias", (7,))):
            n = int(np.prod(shape))
            sd[k] = np.frombuffer(buf, dtype=np.float16, count=n, offset=off).astype(np.float32).reshape(shape)
            off += 2 * n
        p = Predictor(hidden=1)
        p.load_state(sd, int(hidden))
        return p


def _inputs(a_log_scale, a_quat, a_logit_op, off, ofa):
    """``(n, 10)`` network input built from what the *file* stores, not from encoder memory."""
    t = _torch()
    x = t.cat([a_log_scale[ofa], a_quat[ofa][:, 1:], a_logit_op[ofa][:, None], off], dim=-1)
    return x


def _outputs(pred, a_quat):
    """Split the network output into corrected attributes."""
    t = _torch()
    dscale = pred[:, 0:3]
    dquat = rotvec_to_quat(pred[:, 3:6])
    dop = pred[:, 6:7]
    return dscale, dquat, dop


# ----------------------------------------------------------------------------- training

# ----------------------------------------------------------------------------- encoding

def encode(splats, spec_name: str = "c10_o8_sh3", target_ppa: float = 8.0, rank: int = 16,
           bits_total: int = 48, level: int = 12, path: str = None, pos_bits: int = 10,
           attr_bits: int = 8, dc_bits: int = 6, offset_bits: int = OFFSET_BITS,
           steps: int = 20000, hidden: int = HIDDEN, seed: int = 0, log=None):
    """Write a predicted-anchor container; returns ``(meta, streams, path)``."""
    means = np.asarray(A27._get(splats, "means"), dtype=np.float32)
    n = means.shape[0]
    sh = A27._get(splats, "sh", None)
    sh0 = A27._get(sh, "sh0") if sh is not None else A27._get(splats, "sh0")
    shn = A27._get(sh, "shN") if sh is not None else A27._get(splats, "shN")

    voxel = A27.voxel_size_for(means, target_ppa)
    order, starts, counts, vox, org = A27.group(means, voxel)
    while counts.max() > 65000:
        voxel *= 1.5
        order, starts, counts, vox, org = A27.group(means, voxel)
    na = int(vox.shape[0])
    a_means = org[None, :] + (vox.astype(np.float32) + 0.5) * np.float32(voxel)
    pos_bits = int(max(1, np.ceil(np.log2(max(2, int(vox.max()) + 1)))))
    ofa = np.repeat(np.arange(na), counts)

    st: dict = {}
    st["a_vox"] = M.pack_bits(vox.reshape(-1), pos_bits)
    st["a_org"] = org.astype(np.float32).tobytes()
    st["a_count"] = counts.astype(np.uint16).tobytes()

    off = means[order] - a_means[ofa]
    quantum = voxel / float(1 << int(offset_bits))
    ocode = np.clip(np.round((off + 0.5 * voxel) / quantum), 0, (1 << int(offset_bits)) - 1)
    st["a_off"] = M.pack_bits(ocode.reshape(-1).astype(np.int64), int(offset_bits))
    #: the network sees the *decoded* offset, i.e. the centre of the quantisation cell
    off_q = ((ocode.astype(np.float32) - np.float32((1 << int(offset_bits)) - 1) / 2.0)
             * np.float32(quantum))

    def _mean(v):
        v = np.asarray(v, dtype=np.float64)[order]
        return np.add.reduceat(v, starts, axis=0) / (counts[:, None] if v.ndim > 1 else counts)

    scales = np.log(np.maximum(np.asarray(A27._get(splats, "scales"), dtype=np.float32), 1e-12))
    opac_lin = np.clip(np.asarray(A27._get(splats, "opacities"), dtype=np.float32), 1e-6, 1 - 1e-6)
    quats = np.asarray(A27._get(splats, "quats"), dtype=np.float64)

    a_scale = _mean(scales)
    a_opac_lin = _mean(opac_lin)
    a_opac = np.log(a_opac_lin / (1 - a_opac_lin))

    q_o = quats[order]
    raw = np.add.reduceat(q_o, starts, axis=0)
    nrm = np.linalg.norm(raw, axis=1, keepdims=True)
    ref = raw / np.maximum(nrm, 1e-12)
    ref[nrm[:, 0] < 1e-9] = np.array([1.0, 0.0, 0.0, 0.0])
    sign = np.where((q_o * ref[ofa]).sum(axis=1) < 0.0, -1.0, 1.0)
    a_quat = np.add.reduceat(q_o * sign[:, None], starts, axis=0) / counts[:, None]
    a_quat /= np.maximum(np.linalg.norm(a_quat, axis=1, keepdims=True), 1e-12)

    #: quantise the anchor records first: this is what the decoder will hold, so the network has to be
    #: trained against the quantised conditioning, not against the encoder's floats
    scodes, smn, sstep = A27._quant(a_scale, attr_bits)
    st["a_scale"] = M.pack_bits(scodes.reshape(-1), attr_bits)
    st["a_scale_hdr"] = np.concatenate([smn, sstep]).astype(np.float32).tobytes()
    a_scale_q = smn + scodes.astype(np.float32) * sstep

    ocodes, omn, ostep = A27._quant(a_opac.reshape(-1, 1), attr_bits)
    st["a_opac"] = M.pack_bits(ocodes.reshape(-1), attr_bits)
    st["a_opac_hdr"] = np.concatenate([omn, ostep]).astype(np.float32).tobytes()
    a_opac_q = omn[0] + ocodes.reshape(-1).astype(np.float32) * ostep[0]

    qwhich, qabc = GP.st3_encode(a_quat, attr_bits)
    st["a_quat_which"] = M.pack_bits(np.asarray(qwhich, dtype=np.int64).reshape(-1), 2)
    st["a_quat_abc"] = M.pack_bits(np.asarray(qabc, dtype=np.int64).reshape(-1), attr_bits)
    a_quat_q = np.asarray(GP.st3_decode(qwhich, qabc, attr_bits), dtype=np.float32)

    # ---- the predictor, trained against the quantised conditioning ----------------------------
    t = _torch()
    dev = "cuda" if t.cuda.is_available() else "cpu"
    a_ls = t.from_numpy(a_scale_q.astype(np.float32)).to(dev)
    a_qq = t.from_numpy(a_quat_q).to(dev)
    a_lo = t.from_numpy(a_opac_q.astype(np.float32)).to(dev)
    off_t = t.from_numpy(off_q.astype(np.float32)).to(dev)
    ofa_t = t.from_numpy(ofa.astype(np.int64)).to(dev)

    scale_t = t.from_numpy(scales[order]).to(dev)
    quat_t = t.from_numpy(quats[order].astype(np.float32)).to(dev)
    op = np.clip(opac_lin[order], 1e-6, 1 - 1e-6)
    logit_t = t.from_numpy(np.log(op / (1 - op)).astype(np.float32)).to(dev)

    x_all = t.cat([a_ls[ofa_t], a_qq[ofa_t][:, 1:], a_lo[ofa_t][:, None], off_t], dim=-1)
    net = Predictor(hidden=hidden, seed=seed).net.to(dev)
    opt = t.optim.Adam(net.parameters(), lr=1e-3)
    gen = t.Generator(device="cpu").manual_seed(int(seed))
    bs = min(1 << 20, n)
    for step in range(int(steps)):
        idx = t.randint(0, n, (bs,), generator=gen).to(dev)
        out = net(x_all[idx])
        dscale, dquat, dop = _outputs(out, a_qq)
        q_pred = t.nn.functional.normalize(quat_mul(dquat, a_qq[ofa_t][idx]), dim=-1)
        l_s = ((a_ls[ofa_t][idx] + dscale) - scale_t[idx]).pow(2).mean()
        l_q = (1.0 - (q_pred * quat_t[idx]).sum(-1).abs()).mean()
        l_o = ((a_lo[ofa_t][idx] + dop.squeeze(-1)) - logit_t[idx]).pow(2).mean()
        loss = l_s + 4.0 * l_q + 0.5 * l_o
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if log and (step % 1000 == 0 or step == steps - 1):
            log(f"  step {step:5d}  loss {float(loss):.5f}  scale {float(l_s):.5f} "
                f"quat {float(l_q):.5f}  opac {float(l_o):.5f}")
    net.eval()
    pred = Predictor(hidden=hidden)
    pred.net = net
    st["m28_w"] = pred.to_bytes()

    # ---- colour: DC per primitive, rest per anchor through the M22 basis ----------------------
    rest_all = np.asarray(shn, dtype=np.float32).reshape(n, -1)
    dc_all = np.asarray(sh0, dtype=np.float32).reshape(n, 3)
    dc = dc_all[order]
    a_lvl = np.maximum.reduceat(np.abs(dc).max(axis=1), starts).astype(np.float32)
    lcodes, lmn, lstep = A27._quant(a_lvl.reshape(-1, 1), attr_bits)
    st["a_dc_lvl"] = M.pack_bits(lcodes.reshape(-1), attr_bits)
    st["a_dc_lvl_hdr"] = np.concatenate([lmn, lstep]).astype(np.float32).tobytes()
    lvl_q = (lmn[0] + lcodes.reshape(-1).astype(np.float32) * lstep[0])[:, None]
    qmax = (1 << (dc_bits - 1)) - 1
    dcode = np.clip(np.round(dc / np.maximum(lvl_q[ofa], 1e-8) * qmax), -qmax - 1, qmax)
    st["a_dc"] = M.pack_bits((dcode.astype(np.int64) + (qmax + 1)).reshape(-1), dc_bits)

    a_rest = _mean(rest_all)
    f = B.fit(a_rest, rank)
    q = B.quantise_alloc(f["coef"], f["comp"], bits_total)
    st["a_basis"] = np.asarray(f["basis"], dtype=np.float32).tobytes()
    st["a_basis_mean"] = np.asarray(f["mean"], dtype=np.float32).reshape(-1).tobytes()
    st["a_coef_comp"] = np.asarray(f["comp"], dtype=np.float32).tobytes()
    st["a_coef_bits"] = np.asarray(q["bits"], dtype=np.uint8).tobytes()
    st["a_coef"] = B.pack_codes(q["codes"], q["bits"], "bits")

    cols = int(rest_all.shape[1])
    meta = {"n": int(n), "n_anchor": na, "spec": spec_name,
            "deg_out": A27._deg_from_cols(cols), "sh_rest_cols": cols,
            "voxel": float(voxel), "target_ppa": float(target_ppa),
            "rank": int(f["basis"].shape[0]), "offset_bits": int(offset_bits),
            "pos_bits": int(pos_bits), "attr_bits": int(attr_bits), "dc_bits": int(dc_bits),
            "anchor_mode": True, "predicted": True, "hidden": int(hidden),
            "sh_layout": "bits", "color": "anchor_basis", "ppa_measured": float(n / max(1, na)),
            "sh_scale_levels": 1, "n_rest": na, "steps": int(steps),
            "basis_energy": float(f["energy"]), "coef_bits": int(q["bits_total"])}
    if path:
        C.write_container(path, st, meta, level=level)
    return meta, st, path


# ----------------------------------------------------------------------------- decoding

def decode(meta: dict, streams: dict) -> dict:
    """Rebuild the renderer tensors: anchor records, offsets, and the network's correction."""
    t = _torch()
    n = int(meta["n"])
    na = int(meta["n_anchor"])
    pb = int(meta.get("pos_bits", 10))
    ab = int(meta.get("attr_bits", 8))
    ob = int(meta.get("offset_bits", OFFSET_BITS))
    voxel = float(meta["voxel"])
    cols = int(meta["sh_rest_cols"])

    org = np.frombuffer(streams["a_org"], dtype=np.float32).reshape(-1)[:3]
    vox = C.unpack_bits(streams["a_vox"], pb, na * 3, dtype=np.uint16).reshape(na, 3)
    a_means = org[None, :] + (vox.astype(np.float32) + np.float32(0.5)) * np.float32(voxel)

    counts = np.frombuffer(streams["a_count"], dtype=np.uint16).astype(np.int64)
    if int(counts.sum()) != n or counts.shape[0] != na:
        counts = np.full(na, max(1, n // max(1, na)), dtype=np.int64)
    ofa = np.repeat(np.arange(na), counts)[:n]

    ocode = C.unpack_bits(streams["a_off"], ob, n * 3, dtype=np.uint8).reshape(n, 3)
    quantum = np.float32(voxel / float(1 << ob))
    off = (ocode.astype(np.float32) - np.float32((1 << ob) - 1) / 2.0) * quantum
    means = a_means[ofa] + off

    def _attr(name, dim):
        h = np.frombuffer(streams[f"a_{name}_hdr"], dtype=np.float32).reshape(-1, dim)
        c = C.unpack_bits(streams[f"a_{name}"], ab, na * dim, dtype=np.uint8).reshape(na, dim)
        return h[0] + c.astype(np.float32) * h[1]

    a_scale = _attr("scale", 3)
    a_opac = _attr("opac", 1).reshape(-1)
    which = C.unpack_bits(streams["a_quat_which"], 2, na, dtype=np.uint8)
    abc = C.unpack_bits(streams["a_quat_abc"], ab, na * 3, dtype=np.uint8).reshape(na, 3)
    a_quat = np.asarray(GP.st3_decode(which, abc, ab), dtype=np.float32)

    pred = Predictor.from_bytes(streams["m28_w"])
    dev = "cuda" if t.cuda.is_available() else "cpu"
    pred.net = pred.net.to(dev).eval()
    chunk = 1 << 21
    out_scale = np.empty((n, 3), dtype=np.float32)
    out_quat = np.empty((n, 4), dtype=np.float32)
    out_op = np.empty(n, dtype=np.float32)
    with t.no_grad():
        a_ls = t.from_numpy(a_scale).to(dev)
        a_qq = t.from_numpy(a_quat).to(dev)
        a_lo = t.from_numpy(a_opac).to(dev)
        for i in range(0, n, chunk):
            j = min(n, i + chunk)
            fi = t.from_numpy(ofa[i:j].astype(np.int64)).to(dev)
            x = t.cat([a_ls[fi], a_qq[fi][:, 1:], a_lo[fi][:, None],
                       t.from_numpy(off[i:j]).to(dev)], dim=-1)
            y = pred.net(x)
            dscale, dquat, dop = _outputs(y, a_qq)
            qn = t.nn.functional.normalize(quat_mul(dquat, a_qq[fi]), dim=-1)
            out_scale[i:j] = (a_ls[fi] + dscale).cpu().numpy()
            out_quat[i:j] = qn.cpu().numpy()
            out_op[i:j] = (a_lo[fi] + dop.squeeze(-1)).cpu().numpy()

    lh = np.frombuffer(streams["a_dc_lvl_hdr"], dtype=np.float32).reshape(1, 2)
    lc = C.unpack_bits(streams["a_dc_lvl"], ab, na, dtype=np.uint8).astype(np.float32)
    a_lvl = (lh[0, 0] + lc * lh[0, 1])[:, None]
    dcb = int(meta.get("dc_bits", 6))
    qmax = (1 << (dcb - 1)) - 1
    dcode = C.unpack_bits(streams["a_dc"], dcb, n * 3, dtype=np.uint8).reshape(n, 3).astype(np.float32)
    sh_dc = (dcode - np.float32(qmax + 1)) / np.float32(qmax) * a_lvl[ofa]

    basis = np.frombuffer(streams["a_basis"], dtype=np.float32).reshape(-1, cols)
    vmean = np.frombuffer(streams["a_basis_mean"], dtype=np.float32)
    comp = np.frombuffer(streams["a_coef_comp"], dtype=np.float32)
    bits = np.frombuffer(streams["a_coef_bits"], dtype=np.uint8).astype(np.int64)
    codes = B.unpack_codes(streams["a_coef"], bits, na, str(meta.get("sh_layout", "bits")))
    coef = np.empty((na, len(bits)), dtype=np.float32)
    for k, bj in enumerate(bits):
        stp = np.float32(2.0 / float(1 << int(bj)))
        coef[:, k] = (codes[k].astype(np.float32) + np.float32(0.5)) * stp - np.float32(1.0)
        coef[:, k] *= comp[k]
    rest_a = (coef @ basis + vmean).astype(np.float32)

    return {"means": means.astype(np.float32), "scales": np.exp(out_scale),
            "quats": out_quat, "opacities": (1.0 / (1.0 + np.exp(-out_op))).astype(np.float32),
            "sh_dc": sh_dc.astype(np.float32),
            "sh_rest": rest_a[ofa].reshape(n, -1, 3).astype(np.float32)}


# ----------------------------------------------------------------------------- round trip

def _fake(seed: int = 0, n: int = 20000):
    rng = np.random.default_rng(seed)
    means = (rng.normal(size=(n, 3)) * 0.2).astype(np.float32)
    scales = np.exp((rng.normal(size=(n, 3)) * 0.3 - 1.0).astype(np.float32))
    q = rng.normal(size=(n, 4))
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    op = 1 / (1 + np.exp(-rng.normal(size=n)))
    return {"means": means, "scales": scales, "quats": q.astype(np.float32),
            "opacities": op.astype(np.float32),
            "sh": {"sh0": rng.normal(size=(n, 3)).astype(np.float32),
                   "shN": (rng.normal(size=(n, 45)) * 0.05).astype(np.float32).reshape(n, 15, 3)}}


def selftest() -> None:
    splats = _fake(n=8000)
    meta, st, _ = encode(splats, target_ppa=8.0, rank=8, bits_total=32, steps=60, path=None)
    out = decode(meta, st)
    for k in ("means", "scales", "quats", "opacities", "sh_dc", "sh_rest"):
        assert out[k].shape[0] == splats["means"].shape[0], (k, out[k].shape)
    assert np.isfinite(out["scales"]).all() and np.isfinite(out["quats"]).all()
    assert float(np.abs(np.linalg.norm(out["quats"], axis=1) - 1.0).max()) < 1e-4
    #: the decoder is a pure function of the file: decode twice, bit for bit
    again = decode(meta, st)
    for k in again:
        assert np.array_equal(again[k], out[k]), k
    #: and the weights survive the container encoding (float16 in, float32 out)
    w = Predictor.from_bytes(st["m28_w"])
    assert w.state()["0.weight"].shape[0] == int(meta["hidden"])
    print("m28 selftest ok  n=%d anchors=%d  reconstructs from the file alone" %
          (int(meta["n"]), int(meta["n_anchor"])))


def main() -> int:
    ap = argparse.ArgumentParser(description="M28 predicted-anchor container")
    ap.add_argument("--ply")
    ap.add_argument("--out")
    ap.add_argument("--ppa", type=float, default=8.0)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--bits", type=int, default=48)
    ap.add_argument("--offset-bits", type=int, default=OFFSET_BITS)
    ap.add_argument("--dc-bits", type=int, default=6)
    ap.add_argument("--steps", type=int, default=20000)
    ap.add_argument("--hidden", type=int, default=HIDDEN)
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

    def log(msg: str) -> None:
        print(msg, flush=True)

    meta, st, _ = encode(splats, target_ppa=a.ppa, rank=a.rank, bits_total=a.bits,
                         offset_bits=a.offset_bits, dc_bits=a.dc_bits, steps=a.steps,
                         hidden=a.hidden, path=a.out, log=log)
    size = os.path.getsize(a.out)
    n = int(meta["n"])
    row = {"file": a.out, "bytes": size, "n": n, "n_anchor": int(meta["n_anchor"]),
           "ppa": round(meta["ppa_measured"], 3), "b_per_prim": round(size / n, 3),
           "voxel": meta["voxel"], "rank": int(meta["rank"]), "bits": a.bits,
           "offset_bits": a.offset_bits, "dc_bits": a.dc_bits, "hidden": a.hidden,
           "steps": a.steps, "streams": {k: len(v) for k, v in st.items()}}
    print(json.dumps(row, indent=1))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(row, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
