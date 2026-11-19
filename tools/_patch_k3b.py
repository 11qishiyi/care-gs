"""K3 verdict: unmeasurable accounting is a failure, not a pass."""
import io

p = r"D:\3dsg_1\experiments\m9_report.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace(
    """    k3["verdict"] = not unpaid""",
    """    # A dictionary whose size cannot be checked against the file is not "paid for":
    # the ledger only passes when every dictionary row got a measured share.
    n_vq_rows = sum(len(p["k3"]) for p in per)
    k3["n_vq_rows"] = n_vq_rows
    k3["verdict"] = (not unpaid) and n_vq_rows > 0 and k3["n_measured_shares"] == n_vq_rows""", 1)

s = s.replace(
    """    res = evaluate(world(0.0))
    check("a dictionary at fewer bytes passes K1", res["K1_frontier_12x"]["verdict"],
          f"{res['K1_frontier_12x']['assets_with_member']}/8")
    check("K2 fails when the dictionaries do not beat the scalar rows",
          not res["K2_vq_vs_scalar"]["verdict"], str(res["K2_vq_vs_scalar"]["median_diff_pp"]))
    check("outcome falls back to the frontier claim", res["outcome"] == "frontier_only_vq",
          res["outcome"])

    res = evaluate(world(3.0))
    check("K2 passes when the dictionary wins by >= 1 pp",
          res["K2_vq_vs_scalar"]["verdict"],
          f"{res['K2_vq_vs_scalar']['assets_meeting_gap']}/8")
    check("outcome is the full claim", res["outcome"] == "vq_dictionary_holds", res["outcome"])

    res = evaluate(world(3.0, with_codebook=False))
    check("an unpaid codebook fails K3", not res["K3_codebook"]["verdict"],
          str(res["K3_codebook"]["rows_without_codebook"]))
    check("outcome refuses to claim anything without the ledger",
          res["outcome"] == "dead_write_N18", res["outcome"])""",
    """    def ledger(doc, stored=5_000_000):
        return dict(scenes=[dict(scene=sc["scene"],
                                 rows=[dict(spec=r["variant"], stored=stored)
                                       for r in sc["rows"]])
                            for sc in doc["scenes"]])

    doc = world(0.0)
    res = evaluate(doc, bytes_doc=ledger(doc))
    check("a dictionary at fewer bytes passes K1", res["K1_frontier_12x"]["verdict"],
          f"{res['K1_frontier_12x']['assets_with_member']}/8")
    check("K2 fails when the dictionaries do not beat the scalar rows",
          not res["K2_vq_vs_scalar"]["verdict"], str(res["K2_vq_vs_scalar"]["median_diff_pp"]))
    check("outcome falls back to the frontier claim", res["outcome"] == "frontier_only_vq",
          res["outcome"])
    check("the codebook share is reported", res["K3_codebook"]["verdict"],
          f"median {100 * (res['K3_codebook']['median_codebook_share'] or 0):.3f}%")

    doc = world(3.0)
    res = evaluate(doc, bytes_doc=ledger(doc))
    check("K2 passes when the dictionary wins by >= 1 pp",
          res["K2_vq_vs_scalar"]["verdict"],
          f"{res['K2_vq_vs_scalar']['assets_meeting_gap']}/8")
    check("outcome is the full claim", res["outcome"] == "vq_dictionary_holds", res["outcome"])

    res = evaluate(world(3.0))
    check("an unmeasurable ledger fails K3", not res["K3_codebook"]["verdict"],
          str(res["K3_codebook"]["n_measured_shares"]))
    check("outcome refuses to claim anything without the ledger",
          res["outcome"] == "dead_write_N18", res["outcome"])""", 1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched", len(s))
