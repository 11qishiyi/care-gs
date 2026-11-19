import io

p = "experiments/m19_codec.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("        damage_file(path, dst, frac=frac, seed=seed, stream=stream)",
              "        damage_file(path, dst, frac=frac, seed=seed, stream=stream, burst=True)")
s = s.replace('"sh_changed": d["sh_dc"]["prims_changed_frac"],',
              '"sh_changed": max(d["sh_dc"]["prims_changed_frac"],'
              ' d["sh_rest"]["prims_changed_frac"]),')
s = s.replace('"sh_max_abs": d["sh_dc"]["max_abs"]})',
              '"sh_max_abs": max(d["sh_dc"]["max_abs"], d["sh_rest"]["max_abs"])})')
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("burst:", s.count("burst=True"), "rest-metric:", s.count('d["sh_rest"]["prims_changed_frac"]'))
