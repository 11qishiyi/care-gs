"""Build tools/push_m35.ps1: the M31 bundle plus everything the M33-M35 rounds added.

Written as a file rather than `python -c` because PowerShell eats the escaped quotes, which is the
same trap that has cost this project three rounds of debugging (see N41's lessons).

`push_m31.ps1` keeps its file list on line 23 (the M31 extras sit there, one long line), so the new
names are appended to *that* line rather than after a named anchor that does not exist.
"""
import io
import re

src = io.open("tools/push_m31.ps1", encoding="utf-8").read()

new_names = [
    r"experiments\run_m32.sh", r"experiments\run_m33.sh", r"experiments\run_m34.sh",
    r"experiments\run_m35.sh", r"experiments\make_m360_archive.py",
    r"experiments\probe_render.sh",
    r"tools\zip_entry.py", r"tools\m33_damage.py", r"tools\m34_check.py",
    r"tools\m34_summary.py", r"tools\m35_table.py",
]

line_no = None
lines = src.splitlines()
for i, line in enumerate(lines):
    if r"'experiments\run_m31.sh'" in line:
        line_no = i
        break
assert line_no is not None, "run_m31.sh line missing from push_m31.ps1"

have = {m.group(1) for m in re.finditer(r"'([^']+)'", lines[line_no])}
add = [n for n in new_names if n not in have]
lines[line_no] = lines[line_no].rstrip().rstrip(",") + ",\n  " + ", ".join("'%s'" % n for n in add) + ","

out = "\n".join(lines) + "\n"
out = out.replace("-BundleName m31", "-BundleName m35")
out = out.replace("Push everything the M31/M32 round needs", "Push everything the M35 round needs")
io.open("tools/push_m35.ps1", "w", encoding="utf-8", newline="\n").write(out)

print("wrote tools/push_m35.ps1, added", len(add), "names")
print("   ", ", ".join(add))
for line in out.splitlines():
    if "BundleName" in line:
        print("   ", line.strip()[:110])
