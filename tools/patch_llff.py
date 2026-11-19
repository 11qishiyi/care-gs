# -*- coding: utf-8 -*-
"""Hook the LLFF loader into train_gs.py and risk_alloc.py."""
import io

p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("from calib.colmap_io import load_colmap_scene, load_images, read_points3D_bin, normalize_exposure",
              "from calib.colmap_io import load_colmap_scene, load_images, read_points3D_bin, normalize_exposure\n"
              "from calib.llff import load_llff_scene")
s = s.replace("""    scene = load_colmap_scene(args.data, factor=args.factor, split=args.split,
                              cal_frac=args.cal_frac, train_frac=args.train_frac)""",
"""    if os.path.isfile(os.path.join(args.data, "poses_bounds.npy")):
        scene = load_llff_scene(args.data, factor=args.factor,
                                cal_frac=args.cal_frac, train_frac=args.train_frac)
        scene["sparse_dir"] = os.path.join(args.data, "sparse", "0")
    else:
        scene = load_colmap_scene(args.data, factor=args.factor, split=args.split,
                                  cal_frac=args.cal_frac, train_frac=args.train_frac)""")
# LLFF has no sparse points: fall back to random initialisation inside the frustum
s = s.replace('''    xyz, rgb = read_points3D_bin(os.path.join(scene["sparse_dir"], "points3D.bin"))''',
'''    p3 = os.path.join(scene["sparse_dir"], "points3D.bin")
    if os.path.isfile(p3):
        xyz, rgb = read_points3D_bin(p3)
    else:                                          # LLFF: no sparse points
        rng = np.random.default_rng(0)
        cs = scene["camtoworlds"][:, :3, 3]
        ctr = cs.mean(0)
        rad = float(np.linalg.norm(cs - ctr, axis=1).max())
        xyz = ctr + rng.normal(0, 0.5 * rad, (40000, 3))
        rgb = rng.integers(60, 200, (40000, 3), dtype=np.uint8)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched train_gs for LLFF")

p2 = r"D:\3dsg_1\research\code\scripts\risk_alloc.py"
s = io.open(p2, encoding="utf-8").read()
s = s.replace("from calib.scene3dgs import load_scene_from_3dgs  # noqa: E402",
              "from calib.scene3dgs import load_scene_from_3dgs  # noqa: E402\n"
              "from calib.llff import load_llff_scene  # noqa: E402")
s = s.replace('''    else:
        sc = load_colmap_scene(args.scene, factor=args.factor, split="chrono",
                               cal_frac=0.15, train_frac=0.65)''',
'''    elif os.path.isfile(os.path.join(args.scene, "poses_bounds.npy")):
        sc = load_llff_scene(args.scene, factor=args.factor, cal_frac=0.2, train_frac=0.6)
    else:
        sc = load_colmap_scene(args.scene, factor=args.factor, split="chrono",
                               cal_frac=0.15, train_frac=0.65)''')
io.open(p2, "w", encoding="utf-8").write(s)
ast.parse(s); print("patched risk_alloc for LLFF")
