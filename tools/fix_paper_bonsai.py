import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("| bonsai | 211k | 0.903 | 0.896 | −0.7 |", "| bonsai | 211k | 0.903 | 0.896 | −0.8 |")
s = s.replace("在 5 个轻量自训模型（≤241k 基元）上该效应**不存在**（−0.7~+3.2pp，见 §3.1a）",
              "在 5 个轻量自训模型（≤241k 基元）上该效应**不存在**（−0.8~+3.2pp，见 §3.1a）")
s = s.replace("在 5 个轻量自训模型（117k–241k 基元、10–16 dB）上**观察不到**该效应（−0.7~+3.2pp，§3.1a）",
              "在 5 个轻量自训模型（117k–241k 基元、10–16 dB）上**观察不到**该效应（−0.8~+3.2pp，§3.1a）")
io.open(p, "w", encoding="utf-8").write(s)
print("paper: bonsai value synced")
