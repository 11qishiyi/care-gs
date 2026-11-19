"""Build tools/push_m36.ps1: the M35 bundle plus the M36 rate term, its tests, and the round script."""
import io
import re

src = io.open("tools/push_m35.ps1", encoding="utf-8").read()

new_names = [
    r"experiments\m36_rate.py", r"experiments\run_m36.sh",
    r"experiments\prune_ply.py", r"research\code\scripts\train_gs.py",
]

lines = src.splitlines()
idx = None
for i, line in enumerate(lines):
    if r"'experiments\run_m35.sh'" in line:
        idx = i
        break
assert idx is not None, "run_m35.sh line missing from push_m35.ps1"

have = {m.group(1) for m in re.finditer(r"'([^']+)'", lines[idx])}
for line in lines:
    have |= {m.group(1) for m in re.finditer(r"'([^']+)'", line)}
add = [n for n in new_names if n not in have]
lines[idx] = lines[idx].rstrip().rstrip(",") + ",\n  " + ", ".join("'%s'" % n for n in add) + ","

out = "\n".join(lines) + "\n"
out = out.replace("-BundleName m35", "-BundleName m36")
out = out.replace("Push everything the M35 round needs", "Push everything the M36 round needs")
io.open("tools/push_m36.ps1", "w", encoding="utf-8", newline="\n").write(out)
print("wrote tools/push_m36.ps1, added", add)
