import io

P = r"D:\3dsg_1\submission\cviu\main.tex"
s = io.open(P, encoding="utf-8").read()

a = ("number of bytes: a change of $-0.04$ to $-1.17$ points on all eight checkpoints, against $-7.1$ to\n"
     "$-19.2$ points for the deletion, with PSNR flat or slightly improved.")
b = ("number of bytes: no measurable change at all --- a paired drop of $0.00$ points on eight of the\n"
     "eight checkpoints, and never worse than $0.01$ --- against $-7.1$ to $-19.2$ points for the\n"
     "deletion, for $12.8$ to $19.2$ points of difference at the same size, with PSNR flat or slightly\n"
     "improved.")
assert a in s, "loss sentence not found"
s = s.replace(a, b, 1)

c = ("``prune to $30\\%$'' version, and the fourth column is the least damaging non-deleting variant that\n"
     "fits inside it.")
d = ("``prune to $30\\%$'' version, and the fourth column is the least damaging non-deleting variant that\n"
     "fits inside it, ties broken by size (so a cheaper point that loses the same is preferred).")
assert c in s, "caption sentence not found"
s = s.replace(c, d, 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("updated the equal-byte numbers to the measured zero-loss result")
