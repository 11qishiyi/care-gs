import io
p = r"D:\3dsg_1\APPENDIX_negative_results.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("而四个发布检查点是 −11.4 ~ −20.6pp。",
              "而四个发布检查点是 −10.9 ~ −18.6pp（400 次划分的配对降幅）。")
io.open(p, "w", encoding="utf-8").write(s)
print("appendix N9 synced")
