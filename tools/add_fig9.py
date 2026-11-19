import io
p = r"D:\3dsg_1\research\code\scripts\make_figures.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''if __name__ == "__main__":
    fig_edit_families()''',
'''def fig_task_vs_cert():
    """Downstream task damage vs certificate damage -- the paper's second headline."""
    rows = []
    for rel in ("research/results_v60/vt_flowers.json", "research/results_v60/vt_rest.json"):
        rows += load(rel)
    fig, ax = plt.subplots(figsize=(5.2, 2.7))
    x = np.arange(len(rows)); w = 0.36
    cert = [abs(100 * r["voxel_prune30_drop_mean"]) for r in rows]
    task = [abs(100 * (r["task_prune30_hit"] - r["task_clean_hit"])) for r in rows]
    ax.bar(x - w / 2, cert, w, label="certificate coverage (3D voxel)", color="#999999",
           edgecolor="white")
    ax.bar(x + w / 2, task, w, label="downstream task (re-localisation)", color="#C44E52",
           edgecolor="white")
    for xi, t in zip(x, task):
        ax.text(xi + w / 2, t + 0.6, f"{t:.0f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([r["scene"] for r in rows])
    ax.set_ylabel("drop after pruning 30% (pp)")
    ax.set_title("The certificate understates the damage", loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    p = os.path.join(OUT, "fig9_task_vs_cert.png")
    fig.savefig(p); plt.close(fig)
    print("wrote", p)


if __name__ == "__main__":
    fig_task_vs_cert()
    fig_edit_families()''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fig9 added")
