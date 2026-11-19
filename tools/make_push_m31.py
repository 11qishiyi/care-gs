"""Build tools/push_m31.ps1 from the M21 core bundle, adding the rounds since (M22, M24, M29-M32)."""
import io

src = io.open("tools/push_m21.ps1", encoding="utf-8").read()
extra = ("  'experiments\\m22_basis.py', 'experiments\\m24_alpha.py', 'experiments\\m25_time.py',\n"
         "  'experiments\\m27_anchor.py', 'experiments\\m29_split.py', 'experiments\\m29_entropy.py',\n"
         "  'experiments\\m30_adapt.py', 'experiments\\m30_pos.py', 'experiments\\m20_setup.sh',\n"
         "  'experiments\\run_m24.sh', 'experiments\\run_m31.sh', 'experiments\\m31_sizes.py',\n")
anchor = "  'experiments\\m21_lut_probe.py',"
assert anchor in src, "anchor line missing"
out = src.replace(anchor, anchor + "\n" + extra.rstrip("\n"))
out = out.replace("Push everything the M21 round needs", "Push everything the M31/M32 round needs")
out = out.replace("tools\\push_m21.ps1", "tools\\push_m31.ps1")
out = out.replace("-BundleName m21", "-BundleName m31")
io.open("tools/push_m31.ps1", "w", encoding="utf-8").write(out)
print("wrote tools/push_m31.ps1")
for line in out.splitlines():
    if "m2" in line or "m3" in line:
        print("  ", line.strip()[:150])
