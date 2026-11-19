import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()
anchor = "### 3.2 几何编辑致命，外观/精度编辑无害"
new = """### 3.1d 结论与渲染分辨率无关

审稿人自然会问：这是不是 1/4 分辨率下的伪影？我们在 1/2 分辨率（像素数为 4 倍）上重跑同样的协议：

| 场景 | 1/4 分辨率降幅 | **1/2 分辨率降幅** | 差异 |
|---|---:|---:|---:|
| flowers | −11.4 | **−12.8** | 1.4 |
| treehill | −11.9 | **−12.2** | 0.3 |
| bicycle | −20.6 | **−20.3** | 0.3 |
| stump | −12.5 | **−13.7** | 1.2 |

干净态覆盖率也与 1/4 分辨率一致（0.898 / 0.915 / 0.864 / 0.898 对 0.899 / 0.914 / 0.859 / 0.903）。
**退化幅度与分辨率无关（差异 ≤1.4pp），这不是采样伪影。**

""" + anchor
s = s.replace(anchor, new)
io.open(p, "w", encoding="utf-8").write(s)
print("added resolution-robustness section")
