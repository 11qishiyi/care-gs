import io
p = r"D:\3dsg_1\research\code\scripts\risk_alloc.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("from calib.colmap_io import load_images_normalized_placeholder  # noqa: F401  (unused guard)\n", "")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed import")
