import io
p = r"D:\3dsg_1\research\code\scripts\verify_archive.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('PLY = "/workspace/data/out3dgs/output"', 'PLY = "/workspace/data/out3dgs/output"\nCAM_ROOT = "/workspace/data/out3dgs"')
s = s.replace('cam_root=PLY)', 'cam_root=CAM_ROOT)')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("ok")
