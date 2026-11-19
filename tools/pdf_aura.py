import fitz, io, re
doc = fitz.open(r"D:\3dsg_1\_ags_tmp\aura.pdf")
print("pages:", doc.page_count)
txt = []
for i, p in enumerate(doc):
    txt.append(p.get_text())
full = "\n".join(txt)
io.open(r"D:\3dsg_1\_ags_tmp\aura.txt","w",encoding="utf-8").write(full)
print("chars:", len(full))
# section headings
for line in full.splitlines():
    s = line.strip()
    if re.match(r'^(\d+(\.\d+)*)\s+[A-Z]', s) and len(s) < 90:
        print("  ", s)
