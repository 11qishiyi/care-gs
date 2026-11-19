import json, io, re
p = r"C:\Users\71736\.dsh\skills\research-expert-team\data\methods.json"
j = json.load(io.open(p, encoding="utf-8"))
ms = j["methods"]
kw = ["conformal","certificat","certified","calibrated","audit","assurance","guarantee"]
hits=[]
for m in ms:
    name = (m.get("name") or "") + " " + (m.get("title") or "")
    desc = (m.get("desc") or "")
    blob = (name + " " + desc).lower()
    if any(k in blob for k in kw):
        hits.append(m)
print(f"narrow hits: {len(hits)}")
for m in hits[:25]:
    print(f"  {str(m.get('name'))[:34]:34s} {str(m.get('year','')):6s} {str(m.get('venue',''))[:18]:18s} {(m.get('arxiv_id') or '')}")
