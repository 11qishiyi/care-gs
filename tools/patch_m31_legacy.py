"""Add the --no-legacy switch to m24_alpha.report so a run can time the one file that ships."""
import io

P = "experiments/m24_alpha.py"
s = io.open(P, encoding="utf-8").read()

old_row = '''        row = {"plan": tag, "rank": rank, "bits": bits, "n": n,
               "bytes_auto": os.path.getsize(p), "bytes_legacy": os.path.getsize(pl),
               "bytes_per_prim": os.path.getsize(p) / n, "choice": rec["choice"],
               "table": rec["table"], "file": p, "file_legacy": pl}'''
new_row = '''        row = {"plan": tag, "rank": rank, "bits": bits, "n": n,
               "bytes_auto": os.path.getsize(p),
               "bytes_legacy": os.path.getsize(pl) if emit_legacy else os.path.getsize(p),
               "bytes_per_prim": os.path.getsize(p) / n, "choice": rec["choice"],
               "table": rec["table"], "file": p,
               "file_legacy": pl if emit_legacy else None}'''
assert old_row in s, "row block not found"
s = s.replace(old_row, new_row)

old_arg = '    ap.add_argument("--no-ply", action="store_true")'
new_arg = ('    ap.add_argument("--no-ply", action="store_true")\n'
           '    ap.add_argument("--no-legacy", action="store_true",\n'
           '                    help="skip the bytes-alphabet container; times the one file that ships")')
assert old_arg in s, "arg block not found"
s = s.replace(old_arg, new_arg)

old_call = "    report(a.ply, plans, a.level, a.out, emit_ply=not a.no_ply)"
new_call = ("    report(a.ply, plans, a.level, a.out, emit_ply=not a.no_ply, "
            "emit_legacy=not a.no_legacy)")
assert old_call in s, "call block not found"
s = s.replace(old_call, new_call)

io.open(P, "w", encoding="utf-8").write(s)
print("patched", P)
