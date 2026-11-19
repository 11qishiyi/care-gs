import io, re
full = io.open(r"D:\3dsg_1\_ags_tmp\aura.txt", encoding="utf-8").read()
def show(pat, n=6, width=340):
    print(f"--- {pat} ---")
    for m in list(re.finditer(pat, full, flags=re.I))[:n]:
        a = max(0, m.start()-120); b = min(len(full), m.end()+width)
        print("  ", re.sub(r'\s+',' ', full[a:b]).strip()[:430])
        print()
show(r"held-out split", 3)
show(r"calibration set|calibration views|calibration size", 3)
