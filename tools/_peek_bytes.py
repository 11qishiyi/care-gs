import json
import sys

p = sys.argv[1]
d = json.load(open(p))
print("scenes:", [s["scene"] for s in d.get("scenes", [])])
for s in d.get("scenes", []):
    print(s["scene"], s.get("n"), len(s.get("rows", [])))
