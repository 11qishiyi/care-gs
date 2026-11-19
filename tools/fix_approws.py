import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("""| 附录 A | 效应随优化程度增长（密度、微调、步数三组对照） | 见附录 |
| 附录 B | 两个方法学陷阱（划分方式、训练视角泄漏） | — |
| 附录 C | 鲁棒性（α 三档、分辨率、3D 体素区域） | — |""",
"""| 附录 A | 效应随优化程度增长（密度、微调、步数三组对照） | 三组对照 |
| 附录 B | 两个方法学陷阱：划分方式破坏交换性、训练视角泄漏 | — |
| 附录 C | 鲁棒性：α 三档、分辨率两档、3D 体素区域 | — |""")
io.open(p, "w", encoding="utf-8").write(d)
print("appendix rows now start with | 附录")
