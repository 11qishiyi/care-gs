import io
p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace("from calib.llff import load_llff_scene",
              "from calib.llff import load_llff_scene\nfrom calib.archive_only import load_archive_only_scene")
s = s.replace('ap.add_argument("--init_ply", default="",',
              'ap.add_argument("--archive_scene", default="",\n'
              '                    help="load a scene from the 3DGS output archive instead of COLMAP")\n'
              '    ap.add_argument("--archive_root", default="/workspace/data/out3dgs")\n'
              '    ap.add_argument("--init_ply", default="",')

old_scene = '''    if os.path.isfile(os.path.join(args.data, "poses_bounds.npy")):'''
new_scene = '''    if args.archive_scene:
        scene = load_archive_only_scene(args.archive_root, args.archive_scene,
                                        factor=args.factor, cal_frac=0.5)
        scene["sparse_dir"] = os.path.join(args.archive_root, "output", args.archive_scene)
    elif os.path.isfile(os.path.join(args.data, "poses_bounds.npy")):'''
assert old_scene in s
s = s.replace(old_scene, new_scene)

# points: use input.ply from the archive when there is no sparse/0
s = s.replace('''    p3 = os.path.join(scene["sparse_dir"], "points3D.bin")
    if os.path.isfile(p3):''',
'''    p3 = os.path.join(scene["sparse_dir"], "points3D.bin")
    in_ply = os.path.join(scene.get("sparse_dir", ""), "input.ply")
    if not os.path.isfile(p3) and os.path.isfile(in_ply):
        from calib.gsrender import load_splats as _ls
        _sp = _ls(in_ply, device="cpu")
        xyz = _sp.means.numpy()
        rgb = (np.clip(_sp.sh0[:, 0, :].numpy() * 255, 0, 255)).astype(np.uint8)
    elif os.path.isfile(p3):''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("train_gs: archive scene mode added")
