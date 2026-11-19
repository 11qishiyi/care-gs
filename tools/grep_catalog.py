import json, io, re
p = r"C:\Users\71736\.dsh\skills\research-expert-team\data\methods.json"
j = json.load(io.open(p, encoding="utf-8"))
ms = j["methods"]
print("total methods:", len(ms))
print("sample record keys:", list(ms[0].keys()))
kw = ["conformal","certificat","calibrat","uncertain","guarantee","audit","quality","reliab"]
hits = []
for m in ms:
    blob = json.dumps(m, ensure_ascii=False).lower()
    if any(k in blob for k in kw):
        hits.append((m.get("name") or m.get("title") or "?", (m.get("arxiv") or "")[:20]))
print(f"keyword hits: {len(hits)}")
for h in hits[:20]:
    print("  ", h[0][:70], h[1])
