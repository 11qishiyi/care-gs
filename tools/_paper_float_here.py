import io

P = r"D:\3dsg_1\submission\cviu\main.tex"
s = io.open(P, encoding="utf-8").read()
pairs = [
    ("\\label{tab:bytes}\n\\resizebox",
     "\\label{tab:bytes}\n\\resizebox"),
]
# retag the two new tables so they sit next to their text instead of drifting to the float queue
n = 0
for lab in ("\\label{tab:bytes}\n", "\\label{tab:bytes_vs}\n"):
    idx = s.index(lab)
    head = s.rfind("\\begin{table}[t]", 0, idx)
    if head == -1:
        continue
    s = s[:head] + "\\begin{table}[!htbp]" + s[head + len("\\begin{table}[t]"):]
    n += 1
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("retagged", n, "table(s)")
