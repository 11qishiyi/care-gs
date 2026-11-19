import sys
sys.path.insert(0, r"D:\3dsg_1\experiments")
sys.path.insert(0, r"D:\3dsg_1\research\code")
import common as C
C.add_code_root()
import torch
import qfp_rd as Q
import m4_bytes as M
from calib.gsrender import Splats

N = 4000
shN = torch.randn(N, 15, 3) * 0.05
shN[: N // 2] = 0.0
sp = Splats(means=torch.randn(N, 3), scales=torch.randn(N, 3) * 0.1 - 3,
            quats=torch.nn.functional.normalize(torch.randn(N, 4), dim=1),
            opacities=torch.rand(N), sh0=torch.randn(N, 1, 3) * 0.1, shN=shN)
for name in ["msc12-4-a1_c8_o8", "msc12-6-a4_c8_o8"]:
    spx = Q.parse_spec(name)
    r = M.measure_scene(sp, [name], level=1, log=lambda *a: None, skip_flat=True)
    rows = r["rows"] if isinstance(r, dict) and "rows" in r else r
    row = rows[0] if isinstance(rows, list) else list(rows.values())[0]
    n = row["stored"]
    print(name, "mix", tuple(round(x, 3) for x in spx.msc_frac))
    for k, v in row["streams"].items():
        print("   ", k, round(v / n, 3), "B/prim")
    print("   model", round(row["model_bytes_per_prim"], 3),
          "packed", round(row["packed_bytes_per_prim"], 3))
