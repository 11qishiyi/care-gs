import sys, torch
sys.path.insert(0, r"D:\3dsg_1\experiments")
import common as C
C.add_code_root()
import qfp_rd as Q, dpcm, dump_artifacts as D
from calib.gsrender import Splats

torch.manual_seed(0)
grid = torch.stack(torch.meshgrid(torch.arange(8), torch.arange(8), torch.arange(8),
                                  indexing="ij"), dim=-1).reshape(-1, 3).float()
n = int(grid.shape[0])
base = (0.90 + 0.05 * torch.sin(grid[:, :1] * 0.15) + 0.04 * torch.cos(grid[:, 1:2] * 0.12))
shN = (base[:, None, :] * torch.linspace(0.5, 0.05, 15)[None, :, None]).expand(n, 15, 3)
sp = Splats(means=grid * 0.1, scales=torch.full((n, 3), 1e-3),
            quats=torch.tensor([1.0, 0.0, 0.0, 0.0]).expand(n, 4),
            opacities=torch.full((n,), 0.5),
            sh0=base[:, None, :].expand(n, 1, 3).contiguous(), shN=shN.contiguous())

ref = Q._sh_flat(sp)
for b in (2, 3, 4):
    d = Q._sh_flat(dpcm.quantize_dpcm(sp, b))
    s = Q._sh_flat(D._quantize_splats(sp.clone(), torch, bits=b))
    ed = float((ref - d).abs().mean())
    es = float((ref - s).abs().mean())
    drift = Q._sh_flat(dpcm.quantize_dpcm(sp, b))
    print(f"bits={b} dpcm={ed:.6f} scalar={es:.6f} ratio={ed/es:.3f}")
print("block=64, prims per block drift check at b=2:",
      float((ref - Q._sh_flat(dpcm.quantize_dpcm(sp, 2))).abs().max()))
for blk in (4, 8, 16, 64):
    d = Q._sh_flat(dpcm.quantize_dpcm(sp, 2, block=blk))
    print(f"block={blk:3d} dpcm={float((ref-d).abs().mean()):.6f}")
