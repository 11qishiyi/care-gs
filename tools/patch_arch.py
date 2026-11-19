import io
p = r"D:\3dsg_1\research\code\calib\archive_scene.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace(
'''def load_archive_scene(archive_root: str, scene: str, factor: int = 4,
                       llffhold: int = 8, which: str = "test"):''',
'''def load_archive_scene(archive_root: str, scene: str, factor: int = 4,
                       llffhold: int = 8, which: str = "test",
                       cam_root: str | None = None):''')
s = s.replace(
'''    base = os.path.join(archive_root, "output", scene)
    cams = _load_cams(os.path.join(base, "cameras.json"))''',
'''    base = os.path.join(archive_root, "output", scene)
    cam_base = os.path.join(cam_root or archive_root, "output", scene)
    cams = _load_cams(os.path.join(cam_base, "cameras.json"))''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched archive_scene")

p2 = r"D:\3dsg_1\research\code\scripts\verify_archive.py"
s = io.open(p2, encoding="utf-8").read()
s = s.replace('sc = load_archive_scene(ARCH, scene, factor=factor)',
              'sc = load_archive_scene(ARCH, scene, factor=factor, cam_root=PLY)')
io.open(p2, "w", encoding="utf-8").write(s)
ast.parse(s); print("patched verify_archive")
