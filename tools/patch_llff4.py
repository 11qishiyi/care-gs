import io
p = r"D:\3dsg_1\research\code\calib\llff.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("camtoworlds=c2w[:, :3, :4].astype(np.float32),", "camtoworlds=c2w.astype(np.float32),")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("return full 4x4 c2w")
