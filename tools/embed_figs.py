import io
p = r"D:\3dsg_1\PAPER_certificate_invalid.md"
s = io.open(p, encoding="utf-8").read()

# insert figure 1 right after the 3.2 heading
s = s.replace("""### 3.2 几何编辑致命，外观/精度编辑无害

我们测了三类编辑""",
"""### 3.2 几何编辑致命，外观/精度编辑无害

![编辑类型对证书的影响](figures/fig1_edit_families.png)

我们测了三类编辑""")

s = s.replace("""### 3.3 重标定能保住覆盖率，但要把区间放宽 26–83%""",
"""### 3.3 重标定能保住覆盖率，但要把区间放宽 26–83%

![区间宽度](figures/fig2_interval_width.png)""")

s = s.replace("""### 3.1c 结论在 α = 0.05 / 0.10 / 0.20 上一致，且退化随 α 单调增大""",
"""### 3.1c 结论在 α = 0.05 / 0.10 / 0.20 上一致，且退化随 α 单调增大

![alpha 鲁棒性](figures/fig3_alpha.png)""")

s = s.replace("""### 3.6 如果非要剪枝：选对准则能把损失减半""",
"""### 3.6 如果非要剪枝：选对准则能把损失减半

![剪枝准则对照](figures/fig4_pruning_criterion.png)""")
io.open(p, "w", encoding="utf-8").write(s)
print("4 figures embedded")
