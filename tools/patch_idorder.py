import io
p = r"D:\3dsg_1\research\code\calib\archive_scene.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''    cams = _load_cams(os.path.join(cam_base, "cameras.json"))
    cams.sort(key=lambda c: c["img_name"])          # 3DGS sorts cameras by name''',
'''    cams = _load_cams(os.path.join(cam_base, "cameras.json"))
    # NOTE: cameras.json is written in the *training order* (id order), which is a
    # COLMAP insertion order and NOT sorted by image name.  Sorting by name breaks
    # the ``test j -> camera 8j`` mapping (verified: PSNR drops 20.4 -> 12.2 dB).
    cams.sort(key=lambda c: c["id"])''')
s = s.replace('''        out.append(dict(img_name=c["img_name"], width=int(c["width"]), height=int(c["height"]),
                        c2w=c2w, K=K))''',
'''        out.append(dict(id=int(c.get("id", len(out))), img_name=c["img_name"],
                        width=int(c["width"]), height=int(c["height"]), c2w=c2w, K=K))''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched archive_scene id-order")

for q in [r"D:\3dsg_1\research\code\scripts\verify_archive.py", r"D:\3dsg_1\research\code\scripts\cmp_render.py"]:
    t = io.open(q, encoding="utf-8").read()
    io.open(q, "w", encoding="utf-8").write(t)
print("done")
