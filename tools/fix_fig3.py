import io
p = r"D:\3dsg_1\research\code\scripts\make_figures.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("    ax.set_xlabel(r\"$\\alpha$  (looser guarantee $\\rightarrow$)\")",
              "    ax.set_xlabel(r\"$\\alpha$  (larger = looser guarantee)\")")
s = s.replace("    ax.invert_xaxis()\n", "")
io.open(p, "w", encoding="utf-8").write(s)
print("fig3 axis direction fixed")
