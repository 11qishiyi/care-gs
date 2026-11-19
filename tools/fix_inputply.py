import io
p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''    if not os.path.isfile(p3) and os.path.isfile(in_ply):
        from calib.gsrender import load_splats as _ls
        _sp = _ls(in_ply, device="cpu")
        xyz = _sp.means.numpy()
        rgb = (np.clip(_sp.sh0[:, 0, :].numpy() * 255, 0, 255)).astype(np.uint8)''',
'''    if not os.path.isfile(p3) and os.path.isfile(in_ply):
        # the archive's input.ply is a plain point cloud (xyz + colour), not a
        # splat file, so read it field by field
        from plyfile import PlyData
        _pl = PlyData.read(in_ply)["vertex"].data
        names = _pl.dtype.names
        xyz = np.stack([np.asarray(_pl["x"]), np.asarray(_pl["y"]),
                        np.asarray(_pl["z"])], axis=1).astype(np.float32)
        if all(c in names for c in ("red", "green", "blue")):
            rgb = np.stack([np.asarray(_pl["red"]), np.asarray(_pl["green"]),
                            np.asarray(_pl["blue"])], axis=1).astype(np.uint8)
        else:
            rgb = np.full((xyz.shape[0], 3), 128, dtype=np.uint8)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("input.ply reader fixed")
