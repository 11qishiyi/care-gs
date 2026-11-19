# -*- coding: utf-8 -*-
"""Fix the scene-scale used for densification on forward-facing (LLFF) scenes.

scene_scale was computed from the spread of camera *centres*.  For forward-facing
captures the cameras sit on a tiny arc while the scene extends metres away, so the
scale is orders of magnitude too small and the densification strategy prunes every
primitive as "too large".  Use the extent of the initialised point cloud instead.
"""
import io
p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()

old = """    cam_centers = c2w_all[:, :3, 3]
    scene_scale = float(torch.linalg.norm(cam_centers - cam_centers.mean(0), dim=1).max())"""
new = """    cam_centers = c2w_all[:, :3, 3]
    cam_spread = float(torch.linalg.norm(cam_centers - cam_centers.mean(0), dim=1).max())
    # the densification thresholds are normalised by this scale; for forward-facing
    # captures the camera spread is tiny compared with the scene, so take the max of
    # the camera spread and the initial point-cloud radius.
    pc_radius = float((params["means"] - params["means"].mean(0)).norm(dim=1).quantile(0.99))
    scene_scale = max(cam_spread, pc_radius)"""
assert old in s
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched scene_scale -> max(camera spread, point-cloud radius)")
