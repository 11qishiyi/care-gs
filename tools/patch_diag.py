import io
p = r"D:\3dsg_1\research\code\scripts\diag_shift.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("        lum = rgb.mean(1).reshape(len(idx), -1)\n        gx = (lum[:, :, 1:] - lum[:, :, :-1]).abs().mean(1)",
              "        lum = rgb.mean(1)\n        gx = (lum[:, :, 1:] - lum[:, :, :-1]).abs().mean(dim=(1, 2))")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed")
