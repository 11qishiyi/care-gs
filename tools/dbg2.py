import io, re
paper = io.open(r"D:\3dsg_1\PAPER_certificate_invalid.md", encoding="utf-8").read()
idx = io.open(r"D:\3dsg_1\DELIVERABLES.md", encoding="utf-8").read()
n = len(re.findall(r"^### [0-9]", paper, flags=re.M)) + len(re.findall(r"^## 附录", paper, flags=re.M))
listed = len(re.findall(r"^\| (?:3\.|附录)", idx, flags=re.M))
print("n_sections", n, "listed", listed)
print("index rows:")
for ln in idx.splitlines():
    if re.match(r"^\| (?:3\.|附录)", ln):
        print("  ", ln[:40])
