import io

p = "tools/m25_time.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('ap.add_argument("--dir", default="/workspace/res/m25")',
              'ap.add_argument("--dir", default="/workspace/res/m25")\n'
              '    ap.add_argument("--glob", default="*_auto.gs1")')
s = s.replace('glob.glob(os.path.join(a.dir, "*_auto.gs1"))',
              'glob.glob(os.path.join(a.dir, a.glob))')
io.open(p, "w", encoding="utf-8").write(s)
print("patched timer")
