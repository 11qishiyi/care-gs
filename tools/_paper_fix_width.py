import io

P = r"D:\3dsg_1\submission\cviu\main.tex"
s = io.open(P, encoding="utf-8").read()
a = "\\label{tab:bytes}\n\\input{tab_frontier}"
b = ("\\label{tab:bytes}\n"
     "\\resizebox{\\textwidth}{!}{\\input{tab_frontier}}")
assert a in s, "frontier input not found"
s = s.replace(a, b, 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("wrapped the frontier table so it fits the column")
