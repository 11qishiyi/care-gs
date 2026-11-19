import sys, torch
sys.path.insert(0, r"D:\3dsg_1\experiments")
import common as C
C.add_code_root()
import qfp_rd as Q
from calib.gsrender import Splats

torch.manual_seed(0)
n = 512
grid = torch.stack(torch.meshgrid(torch.arange(8), torch.arange(8), torch.arange(8),
                                  indexing="ij"), dim=-1).reshape(-1, 3).float()
idx = torch.arange(n, dtype=torch.float32)
base = (0.5 + 0.1 * torch.sin(idx * 0.35))[:, None].expand(n, 3)
shN = (base[:, None, :] * torch.linspace(0.5, 0.05, 15)[None, :, None]).expand(n, 15, 3)
sp = Splats(means=grid * 0.1, scales=torch.full((n, 3), 1e-3),
            quats=torch.tensor([1.0, 0.0, 0.0, 0.0]).expand(n, 4),
            opacities=torch.full((n,), 0.5),
            sh0=base[:, None, :].expand(n, 1, 3).contiguous(), shN=shN.contiguous())

flat = Q._sh_flat(sp)
perm = Q.morton_order(sp.means)
x = flat.index_select(0, perm)
block = 64
nb = (n + block - 1) // block
xb = x.reshape(nb, block, x.shape[1])
r = torch.empty_like(xb)
r[:, 0, :] = xb[:, 0, :]
r[:, 1:, :] = xb[:, 1:, :] - xb[:, :-1, :]
qmax = float((1 << (2 - 1)) - 1)
s = (r.abs().amax(dim=2, keepdim=True) / qmax).clamp_min(1e-12)
q = (r / s).round().clamp(-qmax - 1, qmax)
print("qmax", qmax, "scale head", s[0, 0, :3].tolist())
print("q unique", torch.unique(q[0]).tolist())
print("residual head", r[0, :6, 0].tolist())
xh = torch.cumsum(q * s, dim=1)
print("xhat head", xh[0, :6, 0].tolist())
print("x head   ", xb[0, :6, 0].tolist())
print("max err", float((xh - xb).abs().max()))
