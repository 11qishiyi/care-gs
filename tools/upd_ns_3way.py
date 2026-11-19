import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""2. **修训练器的致密化控制**（若要让自训模型也进入"已收敛"状态）：""",
"""2. **把三分对照扩到自训模型**：目前紧凑模型都由发布检查点剪枝而来。
若能让自训模型也进入"已收敛"状态（见下条），就能在完全独立的样本上复现同一结论。
3. **修训练器的致密化控制**：""")
s = s.replace("""3. **补编辑类型**""", """4. **补编辑类型**""")
s = s.replace("""4. **把区域换成 3D 体素**""", """5. **把区域换成 3D 体素**""")
s = s.replace("""5. ~~做成工具~~ **已完成**""", """6. ~~做成工具~~ **已完成**""")
io.open(p, "w", encoding="utf-8").write(s)
print("next steps updated")
