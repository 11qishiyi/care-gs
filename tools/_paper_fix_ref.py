import io

P = r"D:\3dsg_1\submission\cviu\main.tex"
s = io.open(P, encoding="utf-8").read()
a = ("falls only $3.66$--$3.90\\times$\n"
     "(Table~\\ref{tab:bytes}, column \\emph{prune 30\\%}), while 8-bit quantisation of the same")
b = ("falls only $3.66$--$3.90\\times$\n"
     "(Table~\\ref{tab:bytes_vs}, column \\emph{prune 30\\%}), while 8-bit quantisation of the same")
assert a in s, "anchor not found"
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
print("fixed cross-reference to the head-to-head table")
