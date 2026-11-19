import io
p = r"D:\3dsg_1\research\code\calib\llff.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""    c2w = np.concatenate([poses[:, :, :4],
                          np.tile(np.array([0, 0, 0, 1.0]).reshape(1, 4, 1), (n, 1, 1))], 1)""",
"""    bottom = np.tile(np.array([0.0, 0.0, 0.0, 1.0]).reshape(1, 1, 4), (n, 1, 1))
    c2w = np.concatenate([poses[:, :, :4], bottom], axis=1)          # (n,4,4)""")
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed c2w concat")
