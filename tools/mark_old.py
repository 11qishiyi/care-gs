import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()

# abstract point 3: describe the direction without the old-protocol pair
s = s.replace("""   退化幅度从 −5.8~−15.5pp 放大到 **−11.4~−20.6pp**，无标签自检偏差从 −4~−9pp 收到 **±0.03**。""",
"""   退化幅度几乎翻倍，无标签自检偏差从 −4~−9pp 收到 **±0.03**（该节数值基于单次划分的旧协议，见 §2）。""")

# §3.1c alpha table: mark it as old protocol
s = s.replace("### 3.1c 结论在 α = 0.05 / 0.10 / 0.20 上一致，且退化随 α 单调增大",
              "### 3.1c 结论在 α = 0.05 / 0.10 / 0.20 上一致，且退化随 α 单调增大\n\n（本节数值基于单次划分的旧协议，只用来看趋势；绝对值不可与 §3.1 比较。）")
s = s.replace("### 3.1d 结论与渲染分辨率无关",
              "### 3.1d 结论与渲染分辨率无关\n\n（同上：单次划分旧协议，只看趋势。）")
io.open(p, "w", encoding="utf-8").write(s)
print("abstract and 3.1c/3.1d marked")
