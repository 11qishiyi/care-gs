import io
p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''        with torch.no_grad():
            params["means"] = _s.means.clone()
            params["scales"] = torch.log(_s.scales.clamp_min(1e-8))
            params["quats"] = _s.quats.clone()
            params["opacities"] = torch.logit(_s.opacities.clamp(1e-6, 1 - 1e-6))
            params["sh0"] = _s.sh0.clone()
            params["shN"] = _s.shN.clone()''',
'''        with torch.no_grad():
            # keep them as Parameters, otherwise retain_grad() inside the strategy fails
            params["means"] = torch.nn.Parameter(_s.means.clone())
            params["scales"] = torch.nn.Parameter(torch.log(_s.scales.clamp_min(1e-8)))
            params["quats"] = torch.nn.Parameter(_s.quats.clone())
            params["opacities"] = torch.nn.Parameter(
                torch.logit(_s.opacities.clamp(1e-6, 1 - 1e-6)))
            params["sh0"] = torch.nn.Parameter(_s.sh0.clone())
            params["shN"] = torch.nn.Parameter(_s.shN.clone())''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("params kept as nn.Parameter")
