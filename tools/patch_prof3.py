import io
p = r"D:\3dsg_1\research\code\scripts\profile_stages.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("tiles_per_gauss, gauss_ids = gsplat.isect_tiles(",
              "tiles_per_gauss, isect_ids, gauss_ids = gsplat.isect_tiles(")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed unpack")
