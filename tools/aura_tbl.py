import io, re
full = io.open(r"D:\3dsg_1\_ags_tmp\aura.txt", encoding="utf-8").read()
i = full.find("Scene dataset carriers")
print(re.sub(r'\s+',' ', full[i:i+700]))
print()
print("--- 视角数 ---")
for m in re.finditer(r"(train|held-out)\s*(views|lbl)", full, flags=re.I):
    a=max(0,m.start()-100); b=min(len(full), m.end()+160)
    print("  ", re.sub(r'\s+',' ', full[a:b]).strip()[:260])
