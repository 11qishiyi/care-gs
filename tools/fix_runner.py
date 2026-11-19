import io
p = r"D:\3dsg_1\research\code\scripts\voxel_and_task.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("from calib.voxel_cert import render_rgbd, voxel_errors, conformal_q",
              "from calib.voxel_cert import render_rgbd, voxel_tables, conformal_q")
s = s.replace('''            # per-view voxel tables so we can split views, not voxels
            vt = []
            for i in range(len(views)):
                vt.append(voxel_errors(m, c2w, K, gt, [views[i]], W, H, args.voxel, args.device))
            tabs[name] = vt''',
'''            # per-view voxel tables so we can split views, not voxels
            tabs[name] = voxel_tables(m, c2w, K, gt, views, W, H, args.voxel, args.device)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("runner updated")
