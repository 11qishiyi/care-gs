import io
p = r"D:\3dsg_1\research\code\scripts\train_gs.py"
s = io.open(p, encoding="utf-8").read()
i = s.find("using {len(scene['train_idx'])} calibration views")
print("train_idx 取自:", s[max(0,i-320):i+60].strip().splitlines()[-6:])
