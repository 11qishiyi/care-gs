"""M38 -- joint vector quantisation of the four geometry attribute groups.

The scalar path codes each attribute independently, and M29 showed those codes are already at their
first-order entropy, so no coder can take bytes out of them.  The only remaining lever is to spend *fewer
symbols per primitive*: one index into a shared codebook instead of four independent codes.

    x = (log σx, log σy, log σz, qw, qx, qy, qz, logit α)

is an 8-D tuple per primitive.  They are strongly dependent (large Gaussians are more opaque, orientation is
tied to shape), which is exactly what a joint codebook can exploit and independent scalar codes cannot.

Cost model, counted inside the container (no hidden bytes):

    bits/primitive = ceil(log2 k)          (one index)
    + k * 8 * 2 B / n                      (float16 centroids, amortised over n primitives)

At k = 65536 and n = 6.13 M that is 16 bit + 0.017 B ≈ 2.02 B per primitive, against the scalar path's
5.50 B (2.25 scales + 2.50 rotation + 0.75 opacity) -- a 63 % cut on those streams if the distortion holds.
"""
from __future__ import annotations

import numpy as np

#: order matters: the matrix layout is part of the file format
DIMS = ("log_sx", "log_sy", "log_sz", "qw", "qx", "qy", "qz", "logit_a")
WIDTH = len(DIMS)


def canon_quat(q: np.ndarray) -> np.ndarray:
    """Unit quaternions with a canonical sign.

    ``q`` and ``-q`` are the same rotation, so a codebook built without fixing the sign would spend two
    entries on every orientation and, worse, put two centroids at opposite points of the sphere where a
    nearest-neighbour lookup cannot tell them apart.  The largest-magnitude component is made positive.
    """
    q = np.asarray(q, dtype=np.float32).reshape(-1, 4)
    q = q / np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-12)
    k = np.argmax(np.abs(q), axis=1)
    sign = np.sign(q[np.arange(q.shape[0]), k])
    sign[sign == 0] = 1.0
    return (q * sign[:, None]).astype(np.float32)


def attr_matrix(geo: dict) -> np.ndarray:
    """The 8-D matrix the codebook is fitted on, from the encoder's own attribute dict."""
    s = np.asarray(geo["scales"], dtype=np.float32).reshape(-1, 3)
    q = canon_quat(geo["quats"])
    a = np.asarray(geo["opacities"], dtype=np.float32).reshape(-1, 1)
    return np.concatenate([s, q, a], axis=1)


def fit(x: np.ndarray, k: int, iters: int = 15, sample: int = 100_000, seed: int = 0,
        chunk: int = 8192, device: str | None = None, log=print) -> np.ndarray:
    """Mini-batch k-means with Lloyd updates on a subsample; returns ``(k, 8)`` float32 centroids.

    The subsample is what makes k = 65536 affordable: a full pass over 6.13 M points against 65 536
    centroids is 3.2 TFLOP, which is a fine final assignment but a poor use of fifteen iterations.
    """
    import torch

    torch.manual_seed(int(seed))
    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    xs = torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32))
    if xs.shape[0] > sample:
        pick = torch.randperm(xs.shape[0])[:sample]
        xs = xs[pick]
    xd = xs.to(dev)
    cb = xd[torch.randperm(xd.shape[0], device=dev)[:k]].clone()
    for it in range(int(iters)):
        sums = torch.zeros_like(cb)
        cnt = torch.zeros(k, dtype=torch.float32, device=dev)
        for i in range(0, xd.shape[0], chunk):
            part = xd[i:i + chunk]
            a = torch.cdist(part, cb).argmin(dim=1)
            sums.index_add_(0, a, part)
            cnt.index_add_(0, a, torch.ones_like(a, dtype=torch.float32))
        live = cnt > 0
        cb = torch.where(live.unsqueeze(1), sums / cnt.clamp_min(1.0).unsqueeze(1), cb)
        if not bool(live.all()):
            #: dead centroids are re-seeded from the data: a k-means with empty cells wastes index space
            dead = int((~live).sum())
            cb[~live] = xd[torch.randint(0, xd.shape[0], (dead,), device=dev)]
        if log and (it % 5 == 0 or it == iters - 1):
            log(f"  kmeans k={k} iter {it}: live {int(live.sum())}/{k}")
    return cb.detach().cpu().numpy().astype(np.float32)


def assign(x: np.ndarray, cb: np.ndarray, chunk: int = 8192, device: str | None = None) -> np.ndarray:
    """Nearest centroid for every row, chunked so the distance matrix stays around a gigabyte."""
    import torch

    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    c = torch.from_numpy(np.ascontiguousarray(cb, dtype=np.float32)).to(dev)
    out = np.empty(x.shape[0], dtype=np.uint32)
    step = chunk if c.shape[0] <= 16384 else max(1024, chunk // 4)
    for i in range(0, x.shape[0], step):
        part = torch.from_numpy(np.ascontiguousarray(x[i:i + step], dtype=np.float32)).to(dev)
        out[i:i + step] = torch.cdist(part, c).argmin(dim=1).to(torch.int64).cpu().numpy()
    return out


def bits_for(k: int) -> int:
    return int(np.ceil(np.log2(int(k))))


def encode_attrs(splats, k: int, iters: int = 15, seed: int = 0, log=print) -> dict:
    """Fit a codebook on this model's attributes and return the streams + the meta fields.

    The attributes are reordered by the same Morton order as the position stream: the container stores
    primitives in that order, so an attribute row that is not reordered describes a *different*
    primitive.  (The first version of this function skipped the permutation; the round-trip test caught
    it as a 0.04 disagreement in log-scale, i.e. a correctly-sized file describing the wrong model.)
    """
    import m4_bytes as M

    geo, _ = M._attribute_arrays(splats)
    order = M.morton_order(geo["means"])
    x = attr_matrix(geo)[np.asarray(order)]
    cb = fit(x, k, iters=iters, seed=seed, log=log)
    idx = assign(x, cb)
    b = bits_for(k)
    return {
        "streams": {
            "geo_vq_cb": np.asarray(cb, dtype=np.float16).tobytes(),
            "geo_vq_idx": M.pack_bits(idx.astype(np.uint32), b),
        },
        "meta": {"geo_vq_k": int(k), "geo_vq_bits": b, "geo_vq_dims": list(DIMS),
                 "geo_vq_cb_bytes": int(cb.size * 2)},
        "x": x,
        "idx": idx,
        #: the reconstruction the decoder must reproduce exactly: VQ is lossy against ``x`` by design,
        #: and a test that compares against ``x`` would be measuring the quantiser, not the file
        "recon": cb[idx],
    }


def decode_attrs(streams: dict, meta: dict) -> dict:
    """Rebuild the three attribute groups in *coded* space (log scales, unit quat, logit opacity).

    The caller applies ``exp``/``sigmoid`` exactly as it does for the scalar path, so there is one
    nonlinearity in the decoder rather than two.
    """
    import m19_codec as C

    k = int(meta["geo_vq_k"])
    b = int(meta["geo_vq_bits"])
    n = int(meta["n"])
    cb = np.frombuffer(streams["geo_vq_cb"], dtype=np.float16).astype(np.float32).reshape(k, WIDTH)
    idx = C.unpack_bits(streams["geo_vq_idx"], b, n, dtype=np.uint32 if b > 16 else np.uint16)
    attrs = cb[idx.astype(np.int64)]
    return {"scales": attrs[:, 0:3], "quats": attrs[:, 3:7], "opacities": attrs[:, 7:8]}


def build(model, k: int, spec_name: str = "gp6-6-6_c8_sh3", rank: int = 16, bits_total: int = 48,
          level: int = 12, iters: int = 15, seed: int = 0, log=print) -> dict:
    """A full container: the M35 shipping configuration, with the four attribute streams replaced by VQ.

    Everything else -- cluster positions, SH DC, the rank-16/48-bit colour basis -- is byte-identical to
    the scalar container, so a size difference between the two files is entirely the codebook.
    """
    import m24_alpha as A

    rec = A.build(model, rank=rank, bits_total=bits_total, level=level, spec_name=spec_name,
                  mode="auto", log=log)
    streams, meta = dict(rec["streams"]), dict(rec["meta"])
    vq = encode_attrs(model, k, iters=iters, seed=seed, log=log)
    for name in ("geo_scales", "geo_quat_which", "geo_quat_abc", "geo_opacities"):
        streams.pop(name, None)
    streams.update(vq["streams"])
    meta.update(vq["meta"])
    meta["geo_vq"] = True
    return {"streams": streams, "meta": meta, "x": vq["x"], "idx": vq["idx"],
            "recon": vq["recon"]}


def selftest() -> None:
    rng = np.random.default_rng(0)
    x = np.concatenate([rng.normal(size=(4000, 3)) * 0.2, canon_quat(rng.normal(size=(4000, 4))),
                        rng.normal(size=(4000, 1))], axis=1).astype(np.float32)
    cb = fit(x, 64, iters=8, sample=4000, seed=1, log=None, device="cpu")
    assert cb.shape == (64, WIDTH)
    idx = assign(x, cb, device="cpu")
    assert idx.shape == (4000,) and idx.max() < 64
    #: with 64 cells in 8-D the cells are wide, so the meaningful assertion is not "small error" but
    #: "better than sending one constant": half the variance is what a coarse codebook must still beat.
    err = float(((cb[idx] - x) ** 2).mean())
    base = float(((cb.mean(axis=0)[None, :] - x) ** 2).mean())
    assert err < 0.5 * base, (err, base)
    q = canon_quat(rng.normal(size=(100, 4)))
    #: paired indexing (``q[i, kmax[i]]``); ``q[:, kmax]`` would be a 100x100 cross-product of every row
    #: against every row's maximum column and would fail on the pairs that are not maximum at all
    kx = np.argmax(np.abs(q), axis=1)
    assert np.all(q[np.arange(q.shape[0]), kx] >= -1e-6)
    print(f"m38_vq selftest: OK (mse {err:.4f} vs single-code {base:.4f})")


if __name__ == "__main__":
    selftest()
