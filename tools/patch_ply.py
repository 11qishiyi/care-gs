import io
p = r"D:\3dsg_1\research\code\scripts\certificate_audit.py"
s = io.open(p, encoding="utf-8").read()
old = '''        ply = os.path.join(args.archive, "output", scene,
                           "point_cloud/iteration_40000/point_cloud.ply")'''
new = '''        if args.ply:
            ply = args.ply
        else:
            ply = os.path.join(args.archive, "output", scene,
                               "point_cloud/iteration_40000/point_cloud.ply")'''
assert old in s
s = s.replace(old, new)
s = s.replace('ap.add_argument("--scene_dir", default="")',
              'ap.add_argument("--scene_dir", default="")\n'
              '    ap.add_argument("--ply", default="")')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("added --ply override")
