import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("2. **重标定保住了覆盖率，却把区间放宽 26–83%**：证书仍有效但精度差近一倍。",
              "2. **重标定保住了覆盖率，却把区间放宽 26–71%**：证书仍有效但精度明显变差。")
io.open(p, "w", encoding="utf-8").write(s)
print("abstract width range synced")
