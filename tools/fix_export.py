import io
p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()
old = """    _g.export_splats(
        means=splats.means.cpu(), scales=splats.scales.cpu(), quats=splats.quats.cpu(),
        opacities=splats.opacities.cpu(), sh0=splats.sh0.cpu(), shN=splats.shN.cpu(),
        format="ply", save_to=ply_path,
    )"""
new = """    # INRIA PLY convention: scales are stored in LOG space and opacities as LOGITS.
    # Writing raw values here and then reading them back with exp()/sigmoid() blows
    # the scales up by ~100x (a 0.01 scale becomes exp(0.01) ~= 1.0).
    _g.export_splats(
        means=splats.means.cpu(), scales=torch.log(splats.scales).cpu(),
        quats=splats.quats.cpu(),
        opacities=torch.logit(splats.opacities.clamp(1e-6, 1 - 1e-6)).cpu(),
        sh0=splats.sh0.cpu(), shN=splats.shN.cpu(),
        format="ply", save_to=ply_path,
    )"""
if old in s:
    s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8").write(s)
    import ast; ast.parse(s); print("FIXED export: log-scale + logit-opacity")
else:
    print("pattern not found; checking current export block")
    i = s.find("export_splats")
    print(s[max(0, i-300):i+500])
