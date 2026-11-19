"""render() joined with a literal backslash-n; the markdown needs real newlines."""
import io

P = r"D:\3dsg_1\experiments\m10_report.py"
s = io.open(P, encoding="utf-8").read()
old = '    return "\\\\n".join(out) + "\\\\n"'
new = '    return "\\n".join(out) + "\\n"'
assert old in s, repr(s[s.find("return") - 40:s.find("return") + 40])
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
print("ok")
