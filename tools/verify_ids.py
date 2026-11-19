import urllib.request, urllib.parse, xml.etree.ElementTree as ET, time
ids = ["2605.06204","2609.14899","2610.28937","2607.24562","2606.29054","2607.02721","2609.10307"]
NS={'a':'http://www.w3.org/2005/Atom'}
url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": ",".join(ids), "max_results": 20})
try:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"dsh"}), timeout=40) as r:
        x = r.read().decode()
    root = ET.fromstring(x)
    seen=set()
    for e in root.findall('a:entry', NS):
        aid = e.find('a:id', NS).text.rsplit('/abs/',1)[-1]
        t = ' '.join(e.find('a:title', NS).text.split())
        d = e.find('a:published', NS).text[:10]
        print(f"{aid:16s} {d}  {t[:95]}")
        seen.add(aid.split('v')[0])
    missing=[i for i in ids if i not in seen]
    print("MISSING:", missing)
except Exception as ex:
    print("ERR", ex)
