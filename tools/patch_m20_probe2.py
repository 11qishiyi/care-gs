import io

p = "experiments/m20_probe.py"
s = io.open(p, encoding="utf-8").read()

# MB/prim print for the variants
s = s.replace('f"{v / 1e6:8.2f} MB {v * 8 / n:6.2f} B/prim "', 'f"{v / 1e6:8.2f} MB {v / n:6.2f} B/prim "')
s = s.replace('f"{v / 1e6:8.2f} MB {v / n:6.2f} B/prim "\n                      f"{100.0 * (1 - v / base):+6.1f} %"',
              'f"{v / 1e6:8.2f} MB {v / n:6.2f} B/prim "\n                      f"{100.0 * (1 - v / base):+6.1f} %"')

# the DC block keeps its (N, 1, 3) shape from the PLY
s = s.replace("            dcq = np.clip((dc[:, 0] + dc[:, 1] + dc[:, 2]) * 0.5 + 0.5, 0, 0.999)",
              "            dcq = np.clip(dc.reshape(n, -1).mean(axis=1) * 0.5 + 0.5, 0, 0.999)")
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("dc fix:", "dc.reshape(n, -1).mean" in s, "| variant print:", s.count("{v / n:6.2f} B/prim"))
