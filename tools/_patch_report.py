import io
p = r"experiments\m1_report.py"
lines = io.open(p, encoding="utf-8").read().split("\n")
start = next(i for i, l in enumerate(lines) if "for row in sorted(scenes[0]" in l)
end = next(i for i, l in enumerate(lines) if i > start and l.strip() == 'A("")')
new = [
    "        for row in sorted(scenes[0][\"rows\"], key=lambda r: (r[\"family\"], r.get(\"rate\") or 0)):",
    "            bpp = \"-\" if row[\"bytes_per_prim\"] is None else \"%.2f\" % row[\"bytes_per_prim\"]",
    "            rate = \"-\" if row[\"rate\"] is None else \"%.2fx\" % row[\"rate\"]",
    "            A(\"| `%s` | %s | %s | %s | %.2f | %s |\" % (row[\"variant\"], row[\"family\"], bpp, rate,",
    "                                                 row[\"drop_pp\"], _fmt(row[\"d_psnr\"], 3)))",
]
lines[start:end] = new
io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("patched lines", start, end)
