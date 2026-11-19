import io
p = r"D:\3dsg_1\DELIVERABLES.md"
d = io.open(p, encoding="utf-8").read()
d = d.replace("| 3.7 | 无标签自检在正确划分下误差 ±0.03 | 4 场景 |",
              "| 3.7 | **撤回**：无标签自检是循环论证，永远返回 0.900，实测漏报 3.6–13.2pp | 2 场景 × 400 划分 |")
d = d.replace("""3. 覆盖率不是剪枝代价的敏感指标，**区间宽度才是**。""",
"""3. 覆盖率不是剪枝代价的敏感指标，**区间宽度才是**；
4. **用标定集自检来发现陈旧证书是循环论证**——它永远返回名义值，实测漏报 3.6–13.2pp。""")
io.open(p, "w", encoding="utf-8").write(d)
print("index updated")
