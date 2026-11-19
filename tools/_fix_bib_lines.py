"""Fix the two bibliography lines mangled by re.sub escape processing."""
from pathlib import Path

P = Path("submission/cviu/main.tex")
t = P.read_text(encoding="utf-8")
bad = "bibliographystyle{elsarticle-harv}\nbibliography{refs}"
# the corruption is a literal BACKSPACE (\x08) followed by "ibliographystyle"
for prefix in ("\x08ibliographystyle", "\\bibliographystyle"):
    t = t.replace(prefix, "\\bibliographystyle")
for prefix in ("\x08ibliography", "\\bibliography"):
    if prefix != "\\bibliography":
        t = t.replace(prefix, "\\bibliography")
t = t.replace("\x08", "")
P.write_text(t, encoding="utf-8")
print("backspace chars remaining:", t.count("\x08"))
print("bibliography lines:")
for line in t.splitlines():
    if "bibliograph" in line:
        print("   ", repr(line))
