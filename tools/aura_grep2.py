import io, re
full = io.open(r"D:\3dsg_1\_ags_tmp\aura.txt", encoding="utf-8").read()
def show(pat, n=4, width=420):
    print(f"--- {pat} ---")
    for m in list(re.finditer(pat, full, flags=re.I))[:n]:
        a = max(0, m.start()-150); b = min(len(full), m.end()+width)
        print("  ", re.sub(r'\s+',' ', full[a:b]).strip()[:520]); print()
show(r"Limitations|Future work|we do not", 4)
show(r"level-of-detail ladder|LoD ladder|family-wise", 3)
