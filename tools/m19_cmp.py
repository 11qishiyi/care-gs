import json
import sys

d = json.load(open(sys.argv[1]))
r = [x for x in d["scenes"][0]["rows"] if x["spec"] == sys.argv[2]][0]
print("n", r["stored"], "model", r["model_bytes_per_prim"], "packed", r["packed_bytes_per_prim"],
      "zstd", r["zstd_bytes_per_prim"], "zm", r["zstd_morton_bytes_per_prim"])
print(json.dumps(r["streams"], sort_keys=True))
