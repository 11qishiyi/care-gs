import io

p = "experiments/m27_anchor.py"
s = io.open(p, encoding="utf-8").read()

old = '''    sh = splats["sh"]
    shn = sh["shN"] if isinstance(sh, dict) else sh.shN
    rest_all = np.asarray(shn, dtype=np.float32).reshape(n, -1)
    dc_all = np.asarray(sh["sh0"] if isinstance(sh, dict) else sh.sh0, dtype=np.float32).reshape(n, 3)
'''
new = '''    rest_all = np.asarray(shn, dtype=np.float32).reshape(n, -1)
    dc_all = np.asarray(sh0, dtype=np.float32).reshape(n, 3)
'''
assert old in s
s = s.replace(old, new)

# a tolerant getter for dicts and namespaces alike
anchor = '''# ----------------------------------------------------------------------------- encoding
'''
helper = '''# ----------------------------------------------------------------------------- encoding

def _get(obj, key: str, default=None):
    """Attribute or key, whichever the caller's container uses (dict or ``SimpleNamespace``)."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

'''
assert anchor in s
s = s.replace(anchor, helper, 1)

# the other splats["..."] reads
s = s.replace('np.asarray(splats["scales"], dtype=np.float64)', 'np.asarray(_get(splats, "scales"), dtype=np.float64)')
s = s.replace('np.asarray(splats["opacities"], dtype=np.float64).reshape(-1)', 'np.asarray(_get(splats, "opacities"), dtype=np.float64).reshape(-1)')
s = s.replace('np.asarray(splats["quats"], dtype=np.float64)', 'np.asarray(_get(splats, "quats"), dtype=np.float64)')
io.open(p, "w", encoding="utf-8").write(s)
print("patched")
