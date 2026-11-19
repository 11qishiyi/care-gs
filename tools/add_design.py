import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
# record the concrete design of the follow-up experiment so it is actionable
s = s.replace("""要分离它，必须让微调集与部署集严格不相交、且证书标定集等于微调集，然后重跑。""",
"""要分离它，需要一个严格的对照：把每场景的留出视角切成互不相交的 T 与 V，
**只用 T 微调**，证书用 **cal=T、deploy=V**（两者严格不相交，且标定集就是微调集）。
若此时仍观测到 −18~−21pp，则"贴合标定分布"被排除；若效应消失，则是该解释成立。
当前所有紧凑模型实验都没有按这个设计跑，因此这条对照是本工作最直接的下一步。""")
io.open(p, "w", encoding="utf-8").write(s)
print("follow-up design written into the paper")
