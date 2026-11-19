import io
p = r"D:\3dsg_1\research\code\scripts\profile_stages.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''from calib.colmap_io import load_images, normalize_exposure  # noqa: E402
from calib.scene3dgs import load_scene_from_3dgs  # noqa: E402''',
'''from calib.archive_scene import _load_cams  # noqa: E402''')
s = s.replace('''    sc = load_scene_from_3dgs(os.path.join(args.out3dgs, name, "cameras.json"), args.scene,
                              factor=1, split="chrono", cal_frac=0.15, train_frac=0.65)
    W0, H0 = sc["width"], sc["height"]
    c2w_all = torch.from_numpy(sc["camtoworlds"]).to(args.device)
    K_all = torch.from_numpy(sc["Ks"]).to(args.device)''',
'''    cams = _load_cams(os.path.join(args.out3dgs, name, "cameras.json"))
    W0, H0 = cams[0]["width"], cams[0]["height"]
    c2w_all = torch.from_numpy(np.stack([c["c2w"] for c in cams])).float().to(args.device)
    K_all = torch.from_numpy(np.stack([c["K"] for c in cams])).float().to(args.device)
    n_cams = len(cams)
    dep_idx = list(range(n_cams // 2, n_cams))''')
s = s.replace("        vi = int(sc[\"dep_idx\"][0])", "        vi = dep_idx[0]")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched to use cameras.json directly")
