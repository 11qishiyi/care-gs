import io
p = r"D:\3dsg_1\research\code\scripts\make_figures.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''    ax.set_title("Only geometry edits break the certificate", loc="left", fontsize=10)
    ax.legend(ncol=4, frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout()''',
'''    ax.set_title("Only geometry edits break the certificate", loc="left", fontsize=10)
    ax.set_ylim(-24, 3)
    ax.legend(ncol=4, frameon=False, fontsize=8, loc="upper center",
              bbox_to_anchor=(0.5, -0.28))
    fig.tight_layout()''')
io.open(p, "w", encoding="utf-8").write(s)
print("fig1 legend moved below axes")
