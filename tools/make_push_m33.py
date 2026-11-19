"""Build tools/push_m33.ps1 from the M31 bundle, adding the M33 files."""
import io

src = io.open("tools/push_m31.ps1", encoding="utf-8").read()
anchor = "  'experiments\\run_m24.sh', 'experiments\\run_m31.sh', 'experiments\\m31_sizes.py',"
assert anchor in src, "anchor line missing"
extra = anchor + ("\n  'experiments\\run_m33.sh', 'tools\\m33_damage.py',"
                  " 'experiments\\probe_render.sh', 'experiments\\make_m360_archive.py',\n"
                  "  'experiments\\m20_setup.sh', 'experiments\\run_m17.sh', 'tools\\m25_time.py',")
out = src.replace(anchor, extra)
out = out.replace("Push everything the M31/M32 round needs", "Push everything the M33 round needs")
out = out.replace("tools\\push_m31.ps1", "tools\\push_m33.ps1")
out = out.replace("-BundleName m31", "-BundleName m33")
io.open("tools/push_m33.ps1", "w", encoding="utf-8").write(out)
print("wrote tools/push_m33.ps1")
