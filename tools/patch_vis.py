# -*- coding: utf-8 -*-
import io
p = r"D:\3dsg_1\research\code\calib\gsrender.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace(
"""        radii, means2d, depths, conics, comp = gsplat.fully_fused_projection(
            means=splats.means,
            quats=splats.quats,
            scales=splats.scales,
            viewmats=vm,
            Ks=K,
            width=width,
            height=height,
            near_plane=near,
            packed=False,
        )""",
"""        radii, means2d, depths, conics, comp = gsplat.fully_fused_projection(
            means=splats.means,
            covars=None,
            quats=splats.quats,
            scales=splats.scales,
            viewmats=vm,
            Ks=K,
            width=width,
            height=height,
            near_plane=near,
            packed=False,
        )""")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched gsrender visibility")

p2 = r"D:\3dsg_1\research\code\scripts\run_scene.py"
s = io.open(p2, encoding="utf-8").read()
s = s.replace(
"""        radii, means2d, depths, conics, comp = gsplat.fully_fused_projection(
            means=splats.means, quats=splats.quats, scales=splats.scales,
            viewmats=vm_s, Ks=K_s, width=W, height=H, packed=False)""",
"""        radii, means2d, depths, conics, comp = gsplat.fully_fused_projection(
            means=splats.means, covars=None, quats=splats.quats, scales=splats.scales,
            viewmats=vm_s, Ks=K_s, width=W, height=H, packed=False)""")
io.open(p2, "w", encoding="utf-8").write(s)
ast.parse(s); print("patched run_scene importance")
