import io

for p in ("experiments/m20_probe.py", "experiments/m20_measure.py"):
    s = io.open(p, encoding="utf-8").read()
    s = s.replace("    import calib.gsrender as GR\n", "    from m20_model import load_model\n")
    s = s.replace('GR.load_splats(path, device="cpu")', "load_model(path)")
    s = s.replace('GR.load_splats(os.path.join(args.models, f"{scene}.ply"), device="cpu")',
                  'load_model(os.path.join(args.models, f"{scene}.ply"))')
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print(p, "->", "load_model" in s, "GR." in s)
