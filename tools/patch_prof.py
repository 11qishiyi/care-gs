# -*- coding: utf-8 -*-
"""Adapt profiler to gsplat 1.5.3 SH signature: (deg, dirs, coeffs)."""
import io
p = r"D:\3dsg_1\research\code\scripts\profile_render.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace('''        # stage 2: SH shading (per camera x gaussian)
        t_sh = bench(lambda: gsplat.spherical_harmonics(s.sh_degree, s.means, vm, coeffs))''',
'''        # stage 2: SH shading (per camera x gaussian).  1.5.3 API takes dirs.
        cam_c = (-c2w[0, :3, :3].T @ c2w[0, :3, 3])
        dirs = s.means - cam_c
        dirs = dirs / dirs.norm(dim=-1, keepdim=True).clamp_min(1e-9)
        t_sh = bench(lambda: gsplat.spherical_harmonics(s.sh_degree, dirs, coeffs))''')

s = s.replace('''        cols = gsplat.spherical_harmonics(s.sh_degree, s.means, vm, coeffs)  # (1,N,3)''',
'''        cols = (gsplat.spherical_harmonics(s.sh_degree, dirs, coeffs) + 0.5)[None]  # (1,N,3)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched profiler for gsplat 1.5.3 SH API")
