import io

p = "experiments/m20_probe.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('        sp = plyio.load_inria_ply(path)', '        sp = GR.load_splats(path, device="cpu")')
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("probe loader:", 'GR.load_splats' in s)

p = "experiments/m20_measure.py"
t = io.open(p, encoding="utf-8").read()
t = t.replace('        sp = load_inria_ply(os.path.join(args.models, f"{scene}.ply"))',
              '        sp = GR.load_splats(os.path.join(args.models, f"{scene}.ply"), device="cpu")')
io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print("measure loader:", 'GR.load_splats' in t)
