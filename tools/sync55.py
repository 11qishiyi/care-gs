import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("不重标定丢覆盖率（−11~−20pp），重标定丢精度（区间 +26~83%）。",
              "不重标定丢覆盖率（−11~−19pp），重标定丢精度（区间 +26~71%）。")
io.open(p, "w", encoding="utf-8").write(s)
print("inline numbers synced")
