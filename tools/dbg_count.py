import io, re
paper = io.open(r"D:\3dsg_1\PAPER_certificate_invalid.md", encoding="utf-8").read()
idx = io.open(r"D:\3dsg_1\DELIVERABLES.md", encoding="utf-8").read()
n_sec = len(re.findall(r"^### [0-9]", paper, flags=re.M)) + len(re.findall(r"^## 附录", paper, flags=re.M))
listed = len(re.findall(r"^\| [3A]", idx, flags=re.M))
print("paper sections:", n_sec, " index rows starting with 3/A:", listed)
