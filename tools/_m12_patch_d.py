import io
P = r"D:\3dsg_1\experiments\m12_report.py"
s = io.open(P, encoding="utf-8").read()
old = '''    shelf = evaluate(_synth(0.2, pq_drop=-0.4))'''
new = '''    shelf = evaluate(_synth(0.1, pq_drop=-0.4, vq_drop=-0.5))'''
assert old in s
s = s.replace(old, new, 1)
old2 = '''    ok1 = shelf["criteria"]["Q1"]["verdict"], shelf["criteria"]["Q2"]["verdict"]
    check("Q2 can pass while Q1 fails", (not ok1[0]) and ok1[1] is False or
          (ok1[1] is False), str(ok1))'''
new2 = '''    check("Q2 can pass while Q1 fails (a shelf without a bytes-for-bytes win)",
          (not shelf["criteria"]["Q1"]["verdict"]) and shelf["criteria"]["Q2"]["verdict"],
          f"Q1={shelf['criteria']['Q1']['verdict']} Q2={shelf['criteria']['Q2']['verdict']}")'''
assert old2 in s
s = s.replace(old2, new2, 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
