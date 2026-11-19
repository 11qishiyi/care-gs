import io
p = r"D:\3dsg_1\research\code\calib\gsrender.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("    chunk: int = 8,", "    chunk: int = 2,")
s = s.replace("""        out_c.append(colors)
        out_a.append(alphas)""", """        out_c.append(colors.cpu())
        out_a.append(alphas.cpu())
        del colors, alphas""")
s = s.replace('''    res = {"colors": torch.cat(out_c, 0), "alphas": torch.cat(out_a, 0)}''',
              '''    res = {"colors": torch.cat(out_c, 0).to(device), "alphas": torch.cat(out_a, 0).to(device)}''')
s = s.replace('''        if "ED" in render_mode:
            out_d.append(colors[..., 3:4])
            out_c[-1] = colors[..., :3]''',
              '''        if "ED" in render_mode:
            out_d.append(out_c[-1][..., 3:4])
            out_c[-1] = out_c[-1][..., :3]''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("patched render chunking")
