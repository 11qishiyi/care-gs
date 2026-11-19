import io
P = r"D:\3dsg_1\experiments\m11_report.py"
s = io.open(P, encoding="utf-8").read()
old = '''            {"variant": "msc12-4-a1_c8_o8", "rate": rate * 1.04,
             "drop_pp": base_drop + gain_pp, "d_psnr": 0.05 if dpsnr_ok else -1.0},'''
new = '''            {"variant": "msc12-4-a1_c8_o8", "rate": rate * 1.04,
             "drop_pp": base_drop + gain_pp, "d_psnr": 0.05 if dpsnr_ok else -1.0},
            {"variant": "msc12-4-a2_c8_o8", "rate": 19.0,
             "drop_pp": -0.5 if dpsnr_ok else -1.2, "d_psnr": 0.1 if dpsnr_ok else -1.0},'''
assert old in s
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("ok")
