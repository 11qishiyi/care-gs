import io
p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''        scene["sparse_dir"] = os.path.join(args.archive_root, "output", args.archive_scene)''',
'''        scene["sparse_dir"] = os.path.join(args.archive_root, "output", args.archive_scene)
        # archive-only scenes carry no training split; for fine-tuning we optimise on the
        # calibration views and keep the deployment views untouched (no leakage)
        if len(scene.get("train_idx", [])) == 0:
            scene["train_idx"] = scene["cal_idx"]
            print(f"[finetune] using {len(scene['train_idx'])} calibration views for training",
                  flush=True)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("train_idx fallback added")
