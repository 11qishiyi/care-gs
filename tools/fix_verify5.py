import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('check("abstract drop min (pp, abs)", abs(min(drops)), 11.4, tol=0.2)',
              'mag = [abs(d) for d in drops]\ncheck("abstract drop min (pp, abs)", min(mag), 11.4, tol=0.2)')
s = s.replace('check("abstract drop max (pp, abs)", abs(max(drops)), 20.6, tol=0.2)',
              'check("abstract drop max (pp, abs)", max(mag), 20.6, tol=0.2)')
io.open(p, "w", encoding="utf-8").write(s)
print("using magnitude")
