import io

P = r"D:\3dsg_1\submission\cviu\main.tex"
s = io.open(P, encoding="utf-8").read()

old_sent = ("per se. Table~\\ref{tab:bytes} traces the whole frontier: the loss is $-0.39$ points at a $3\\times$\n"
            "budget and $0.00$ at $7\\times$, and it does not improve further out to $24\\times$, so the budget\n"
            "that matters is the one below about $7\\times$ and the paper's own operating point sits inside it.")
new_sent = ("per se. Table~\\ref{tab:bytes} reads the same frontier backwards, from a coverage tolerance to\n"
            "the bytes it needs, because the forward reading saturates: once a zero-loss point exists at\n"
            "$2.8\\times$, every larger budget reports the same point. Staying within a quarter of a point\n"
            "costs $2.10$--$2.80\\times$ on all eight checkpoints, and within one point never more than\n"
            "$2.77\\times$ --- so the three-fold budget that the paper's own edits occupy is already inside\n"
            "the zero-loss shelf, and the interesting question is not how much the first few times cost but\n"
            "what a pipeline does once it must ship ten times smaller.")
assert old_sent in s, "sentence not found"
s = s.replace(old_sent, new_sent, 1)

old_tbl = "\\resizebox{\\textwidth}{!}{\\input{tab_frontier}}"
new_tbl = "\\resizebox{\\textwidth}{!}{\\input{tab_frontier_inv}}"
assert old_tbl in s
s = s.replace(old_tbl, new_tbl, 1)

old_cap = ("\\caption{The same edits at equal bytes. Each cell is the least damaging \\emph{measured} variant\n"
           "that fits the column's budget, written as coverage change (points) / measured size")
new_cap = ("\\caption{The same frontier read backwards: for a coverage tolerance (points) the cell is the\n"
           "cheapest \\emph{measured} variant that stays within it, written as measured size~($\\times$)")
assert old_cap in s, "caption not found"
s = s.replace(old_cap, new_cap, 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("swapped the table to the inverse reading and rewrote the sentence")
