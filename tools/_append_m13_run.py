import io

SRC = r"D:\3dsg_1\tools\_m13_section.md"
DST = r"D:\3dsg_1\experiments\METHOD_PLAN.md"

text = io.open(SRC, encoding="utf-8").read()
cur = io.open(DST, encoding="utf-8").read()
if "## M13 规格与判定" in cur:
    print("already present")
else:
    if not cur.endswith("\n"):
        cur += "\n"
    io.open(DST, "w", encoding="utf-8", newline="\n").write(cur + text)
    print("appended", len(text), "chars")
