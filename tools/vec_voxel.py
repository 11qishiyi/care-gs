import io
p = r"D:\3dsg_1\research\code\calib\voxel_cert.py"
s = io.open(p, encoding="utf-8").read()
start = s.index("def voxel_errors(")
end = s.index("def conformal_q(")
new = '''def reduce_max_per_voxel(ids: torch.Tensor, errs: torch.Tensor):
    """Vectorised max-reduction of per-pixel error into voxels (no Python loop)."""
    i = ids.cpu().numpy()
    e = errs.cpu().numpy()
    order = np.argsort(i, kind="stable")
    i, e = i[order], e[order]
    if i.size == 0:
        return {}
    uniq, start = np.unique(i, return_index=True)
    maxes = np.maximum.reduceat(e, start)
    return dict(zip(uniq.tolist(), maxes.tolist()))


@torch.no_grad()
def voxel_tables(splats, c2w, K, gt, idx, W, H, voxel, device):
    """One max-per-voxel table per view (so splits can be done over views)."""
    c2w_s = c2w[torch.as_tensor(idx, device=device)]
    K_s = K[torch.as_tensor(idx, device=device)]
    rgb, depth = render_rgbd(splats, c2w_s, K_s, W, H)
    g = gt[torch.as_tensor(idx)].to(device)
    err = (rgb - g).abs().mean(dim=-1)                      # (C,H,W)
    tables = []
    for i in range(len(idx)):
        pts, valid = backproject(depth[i], K_s[i], c2w_s[i])
        ids, m = voxel_ids(pts, valid, voxel)
        tables.append(reduce_max_per_voxel(ids.reshape(-1)[m.reshape(-1)],
                                           err[i].reshape(-1)[m.reshape(-1)]))
    return tables


'''
s = s[:start] + new + s[end:]
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("voxel reduction vectorised")
