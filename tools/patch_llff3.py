import io
p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("f\"{W}x{H}, train={len(scene['train_idx'])} test={len(scene['test_idx'])}\", flush=True)",
              "f\"{W}x{H}, train={len(scene['train_idx'])} \"\n"
              "          f\"cal={len(scene.get('cal_idx', []))} dep={len(scene.get('dep_idx', []))}\", flush=True)")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed print")
