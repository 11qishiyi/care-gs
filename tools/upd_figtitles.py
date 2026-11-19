import io
p = r"D:\3dsg_1\research\code\scripts\make_figures.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('ax.set_title("Only geometry edits break the certificate", loc="left", fontsize=10)',
              'ax.set_title("Geometry edits hurt 10-19 pp; appearance 0.2-2; precision 0",\n'
              '                 loc="left", fontsize=10)')
s = s.replace('ax.set_title("The pruning criterion matters more than the budget", loc="left", fontsize=9)',
              'ax.set_title("Sensitivity pruning keeps most of the certificate", loc="left", fontsize=9)')
io.open(p, "w", encoding="utf-8").write(s)
print("figure titles updated to match the revised claims")
