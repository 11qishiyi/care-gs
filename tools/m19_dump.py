import json
import sys

d = json.load(open(sys.argv[1]))


def walk(o, path="", depth=0):
    if depth > 3:
        return
    if isinstance(o, dict):
        print(path or "<root>", "dict", list(o)[:10])
        for k, v in list(o.items())[:4]:
            walk(v, f"{path}.{k}", depth + 1)
    elif isinstance(o, list):
        print(path, "list", len(o))
        if o:
            walk(o[0], f"{path}[0]", depth + 1)


walk(d)
