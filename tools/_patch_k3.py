"""K3 needs a denominator: read stored counts from m9_bytes.json and size the codebook
from the model, so the ledger is measurable from the artefacts we actually ship."""
import io

p = r"D:\3dsg_1\experiments\m9_report.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace(
    """def evaluate(doc: dict, min_rate: float = 12.0, max_drop: float = 1.0,
             max_dpsnr: float = 0.3, window: float = 0.15, gap_pp: float = 1.0,
             frac: float = 0.75) -> dict:
    scenes = doc.get("scenes", [])""",
    """def evaluate(doc: dict, min_rate: float = 12.0, max_drop: float = 1.0,
             max_dpsnr: float = 0.3, window: float = 0.15, gap_pp: float = 1.0,
             frac: float = 0.75, bytes_doc: dict = None) -> dict:
    scenes = doc.get("scenes", [])
    stored = {}
    for sc_b in (bytes_doc or {}).get("scenes", []):
        for row in sc_b.get("rows", []):
            stored[(sc_b.get("scene"), row.get("spec"))] = row.get("stored")""", 1)

s = s.replace(
    """    unpaid = [p["scene"] for p in per for c in p["k3"] if not c["codebook_bytes"]]
    shares = [c["share"] for p in per for c in p["k3"] if c["share"] is not None]""",
    """    unpaid = [p["scene"] for p in per for c in p["k3"] if not c["codebook_bytes"]]
    shares = [c["share"] for p in per for c in p["k3"] if c["share"] is not None]
    sizes = [c["codebook_bytes"] for p in per for c in p["k3"] if c["codebook_bytes"]]""", 1)

s = s.replace(
    """    k3 = dict(rows_without_codebook=len(unpaid), scenes=unpaid,
              median_codebook_share=_median(shares), max_codebook_share=max(shares or [0.0]))""",
    """    k3 = dict(rows_without_codebook=len(unpaid), scenes=sorted(set(unpaid)),
              median_codebook_share=_median(shares), max_codebook_share=max(shares or [0.0]),
              max_codebook_bytes=max(sizes or [0.0]), n_measured_shares=len(shares))""", 1)

s = s.replace(
    """    ap.add_argument("--selftest", action="store_true")""",
    """    ap.add_argument("--bytes", default=None,
                    help="m9_bytes.json; only used to turn the codebook into a share "
                         "of the file (the rd json carries no byte accounting)")
    ap.add_argument("--selftest", action="store_true")""", 1)

s = s.replace(
    """    res = evaluate(doc, min_rate=args.min_rate, gap_pp=args.gap_pp, window=args.window)""",
    """    bytes_doc = None
    if args.bytes and os.path.exists(args.bytes):
        with open(args.bytes, "r", encoding="utf-8") as fh:
            bytes_doc = json.load(fh)
    res = evaluate(doc, min_rate=args.min_rate, gap_pp=args.gap_pp, window=args.window,
                   bytes_doc=bytes_doc)""", 1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched", len(s))
