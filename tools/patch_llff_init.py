# -*- coding: utf-8 -*-
"""LLFF support: return near/far bounds and initialise points by ray sampling."""
import io

# 1) llff.py: expose the bounds
p = r"D:\3dsg_1\research\code\calib\llff.py"
s = io.open(p, encoding="utf-8").read()
if "bounds" not in s:
    s = s.replace("""    return dict(camtoworlds=c2w.astype(np.float32),""",
                  """    near = float(pb[:, 15].mean())
    far = float(pb[:, 16].mean())
    return dict(bounds=(near, far),
                camtoworlds=c2w.astype(np.float32),""")
    io.open(p, "w", encoding="utf-8").write(s)
    import ast; ast.parse(s)
print("llff.py: bounds exposed")

# 2) train_gs.py: ray-sampling initialisation when there is no sparse point cloud
p2 = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p2, encoding="utf-8").read()
old = """    else:                                          # LLFF: no sparse points
        rng = np.random.default_rng(0)
        cs = scene["camtoworlds"][:, :3, 3]
        ctr = cs.mean(0)
        rad = float(np.linalg.norm(cs - ctr, axis=1).max())
        xyz = ctr + rng.normal(0, 0.5 * rad, (40000, 3))
        rgb = rng.integers(60, 200, (40000, 3), dtype=np.uint8)"""
new = """    else:
        # No sparse points (LLFF).  Forward-facing scenes need points *along the
        # camera rays*, not a Gaussian blob at the centroid: sample random pixels
        # and random depths between the scene's near/far bounds.
        rng = np.random.default_rng(0)
        n_pts = 60000
        near, far = scene.get("bounds", (0.5, 4.0))
        cs = scene["camtoworlds"][:, :3, 3]
        ctr = cs.mean(0)
        rad = float(np.linalg.norm(cs - ctr, axis=1).max())
        cam_ids = rng.integers(0, len(scene["train_idx"]), n_pts)
        c2w_s = scene["camtoworlds"]
        Ks_s = scene["Ks"]
        pts = np.zeros((n_pts, 3), np.float64)
        for i in range(n_pts):
            ci = int(scene["train_idx"][cam_ids[i]])
            c2w_i, K_i = c2w_s[ci], Ks_s[ci]
            u = rng.uniform(0, scene["width"]) - K_i[0, 2]
            v = rng.uniform(0, scene["height"]) - K_i[1, 2]
            d_cam = np.array([u / K_i[0, 0], v / K_i[1, 1], 1.0])
            d_cam /= np.linalg.norm(d_cam)
            t = rng.uniform(near, far) * max(rad, 1e-3)
            pts[i] = c2w_i[:3, :3] @ (t * d_cam) + c2w_i[:3, 3]
        xyz = pts
        rgb = rng.integers(60, 200, (n_pts, 3), dtype=np.uint8)"""
assert old in s
s = s.replace(old, new)
io.open(p2, "w", encoding="utf-8").write(s)
import ast; ast.parse(s)
print("train_gs.py: ray-sampling init for LLFF")
