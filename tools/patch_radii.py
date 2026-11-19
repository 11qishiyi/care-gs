# -*- coding: utf-8 -*-
import io
p = r"D:\3dsg_1\research\code\calib\gsrender.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("outs.append(((radii > 0) & (depths > near)).reshape(vm.shape[0], -1))",
              "outs.append(((radii[..., 0] > 0) & (depths > near)).reshape(vm.shape[0], -1))")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched visibility radii")

p2 = r"D:\3dsg_1\research\code\scripts\run_scene.py"
s = io.open(p2, encoding="utf-8").read()
s = s.replace("        vis = (radii > 0) & (depths > 0.01)                  # (c,N)",
              "        vis = (radii[..., 0] > 0) & (depths > 0.01)          # (c,N)")
io.open(p2, "w", encoding="utf-8").write(s)
ast.parse(s); print("patched importance radii")
