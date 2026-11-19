import io
p = r"D:\3dsg_1\research\code\scripts\certificate_audit.py"
s = io.open(p, encoding="utf-8").read()
# quantize_sh returns the mutated object; make sure the caller uses it AND verify it bites
s = s.replace('''        if "quant8" in edits:
            q8 = quantize_sh(load_splats(ply, device=args.device), bits=8)''',
'''        if "quant8" in edits:
            q8 = quantize_sh(load_splats(ply, device=args.device), bits=8)
            _d = (q8.shN - load_splats(ply, device=args.device).shN).abs().mean()
            print(f"  [quant8] mean |dSH_N| = {float(_d):.2e}", flush=True)''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("added quant8 sanity probe")
