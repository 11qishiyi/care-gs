import io, re
full = io.open(r"D:\3dsg_1\_ags_tmp\aura.txt", encoding="utf-8").read()
lines = full.splitlines()
print("=== 前 60 行 ===")
for l in lines[:60]:
    if l.strip(): print(" ", l.strip()[:110])
