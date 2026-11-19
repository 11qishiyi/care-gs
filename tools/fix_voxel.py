import io
p = r"D:\3dsg_1\research\code\calib\voxel_cert.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''@torch.no_grad()
def render_rgbd(splats, c2w, K, W, H):
    """Render RGB and expected depth for the given cameras."""
    from calib.gsrender import Splats  # noqa: F401
    import gsplat
    vm = torch.linalg.inv_ex(c2w).inverse
    out = gsplat.rasterization(
        means=splats.means, quats=splats.quats, scales=splats.scales,
        opacities=splats.opacities,
        colors=torch.cat([splats.sh0, splats.shN], dim=1),
        viewmats=vm, Ks=K, width=W, height=H,
        sh_degree=splats.sh_degree, packed=False, render_mode="RGB+ED")
    rgb = out[0][..., :3]           # (C,H,W,3)
    depth = out[0][..., 3]          # (C,H,W) expected depth (0 where empty)
    return rgb, depth''',
'''@torch.no_grad()
def render_rgbd(splats, c2w, K, W, H, chunk: int = 4):
    """Render RGB and expected depth for the given cameras (chunked to bound memory)."""
    import gsplat
    coeffs = torch.cat([splats.sh0, splats.shN], dim=1)
    rgbs, deps = [], []
    for s in range(0, c2w.shape[0], chunk):
        c2w_c, K_c = c2w[s:s + chunk], K[s:s + chunk]
        vm = torch.linalg.inv_ex(c2w_c).inverse
        out = gsplat.rasterization(
            means=splats.means, quats=splats.quats, scales=splats.scales,
            opacities=splats.opacities, colors=coeffs,
            viewmats=vm, Ks=K_c, width=W, height=H,
            sh_degree=splats.sh_degree, packed=False, render_mode="RGB+ED")
        rgbs.append(out[0][..., :3])
        deps.append(out[0][..., 3])
    return torch.cat(rgbs, 0), torch.cat(deps, 0)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("render_rgbd chunked")
