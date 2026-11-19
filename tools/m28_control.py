"""Can the M28 predictor learn at all?  Feed it a world where the answer *is* a function of the offset.

This is the control the M28 round needed: with a 7-number anchor record and a 4-bit offset, the measured
loss on bicycle never moved (scale 2.11, opacity 13.2, quaternion |dot| 0.92 -- the same as M27's
constant).  Before that is read as "the conditioning carries no information", the training code has to
be shown capable of learning a function that is there.
"""

from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, "D:/3dsg_1/experiments")

import m28_pred as P  # noqa: E402


def build(n=200000, seed=0):
    rng = np.random.default_rng(seed)
    off = rng.uniform(-0.5, 0.5, size=(n, 3)).astype(np.float32)
    a_scale = rng.normal(size=(3,)).astype(np.float32)
    a_quat = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    a_op = np.float32(0.0)
    #: the world: scale grows with x, opacity with y, rotation about z with x
    scale = a_scale[None, :] + np.stack([off[:, 0], off[:, 0], off[:, 0]], axis=1) * 2.0
    logit = a_op + off[:, 1] * 3.0
    return off, a_scale, a_quat, a_op, scale.astype(np.float32), logit.astype(np.float32)


def main() -> int:
    import torch
    t = torch
    off, a_scale, a_quat, a_op, scale, logit = build()
    n = off.shape[0]
    dev = "cuda" if t.cuda.is_available() else "cpu"

    xs = t.from_numpy(np.tile(np.concatenate([a_scale, a_quat[1:], [a_op]]), (n, 1))).to(dev)
    x = t.cat([xs, t.from_numpy(off).to(dev)], dim=-1)
    y_scale = t.from_numpy(scale).to(dev)
    y_logit = t.from_numpy(logit).to(dev)

    net = P.Predictor(seed=0).net.to(dev)
    opt = t.optim.Adam(net.parameters(), lr=1e-3)
    bs = 65536
    for step in range(3001):
        idx = t.randint(0, n, (bs,), device=dev)
        out = net(x[idx])
        dscale = out[:, 0:3]
        dop = out[:, 6:7]
        loss = ((dscale - y_scale[idx]).pow(2).mean()
                + 0.5 * (dop - y_logit[idx][:, None]).pow(2).mean())
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % 500 == 0:
            print(f"step {step:5d} loss {float(loss):.5f}")
    print("final loss", float(loss))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
