import io, re
full = io.open(r"D:\3dsg_1\_ags_tmp\aura.txt", encoding="utf-8").read()
pats = {
 "edit/modify after export": r"\b(edit|modif|re-?certif|recalibrat|invalidat)\w*",
 "downstream task": r"downstream task|downstream application",
 "consumer action": r"consumer (may|can|drops|prunes)",
 "LoD levels R": r"four levels|𝑅 non-trivial|R =",
}
for name, pat in pats.items():
    ms = list(re.finditer(pat, full, flags=re.I))
    print(f"--- {name}: {len(ms)} hits ---")
    for m in ms[:4]:
        a=max(0,m.start()-140); b=min(len(full), m.end()+200)
        print("  ", re.sub(r'\s+',' ', full[a:b]).strip()[:330]); print()
