import pathlib

p = pathlib.Path("submission/cviu/main.tex")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
# line 604 (1-based) is the fidelity table, 1084 the audit table, 1094 the k-view table
for idx, target in [(603, "tab_fidelity"), (1083, "tab_audit"), (1093, "tab_kview")]:
    assert lines[idx].lstrip().startswith("\\TBD{table"), (idx + 1, lines[idx][:60])
    lines[idx] = "\\input{" + target + "}\n"
p.write_text("".join(lines), encoding="utf-8")
print("wired:", [(l.strip()) for l in lines if l.startswith("\\input{tab_")])
