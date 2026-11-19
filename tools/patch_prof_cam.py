import io
p = r"D:\3dsg_1\research\code\scripts\profile_render.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''    c2w = torch.eye(4, device=args.device)
    c2w[:3, 3] = ctr + torch.tensor([0.0, 0.0, 2.5 * rad], device=args.device)
    c2w = c2w[None]''',
'''    c2w = torch.eye(4, device=args.device)
    # rotate 180 deg about x so the camera's +z points from the eye toward the scene
    R = torch.tensor([[1.0, 0, 0], [0, -1.0, 0], [0, 0, -1.0]], device=args.device)
    c2w[:3, :3] = R
    c2w[:3, 3] = ctr + torch.tensor([0.0, 0.0, 2.5 * rad], device=args.device)
    c2w = c2w[None]''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("camera fixed")
