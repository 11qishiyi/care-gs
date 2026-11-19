"""m4_bytes selftest: the two-stage payload must be accounted for stream by stream."""
import io

B = r"D:\3dsg_1\experiments\m4_bytes.py"
b = io.open(B, encoding="utf-8").read()

b = b.replace(
    '''    order = morton_order(means)''',
    '''    # M10: two-stage dictionary.  Both index streams and both centroid tables are
    # part of the file, and packed bytes must still land on the model's arithmetic.
    res_rvq = measure_scene(sp, ["rvq6-2_c8_o8", "rvq8-4_c8_o8"], level=9)
    rvq_row = res_rvq["rows"][0]
    check("two-stage streams carry both indexes and both codebooks",
          {"sh_index", "sh_index2", "sh_cb_centroids", "sh_cb2_centroids"}
          <= set(rvq_row["streams"]), str(sorted(rvq_row["streams"])))
    tol_rvq = (len(rvq_row["streams"]) + 1) / float(rvq_row["stored"])
    check("packed == model for a two-stage spec",
          abs(rvq_row["packed_bytes_per_prim"] - rvq_row["model_bytes_per_prim"])
          <= tol_rvq + pad,
          f"model {rvq_row['model_bytes_per_prim']:.3f} packed "
          f"{rvq_row['packed_bytes_per_prim']:.3f}")
    check("more residual bits cost more bytes",
          res_rvq["rows"][1]["model_bytes_per_prim"]
          > rvq_row["model_bytes_per_prim"],
          f"{rvq_row['model_bytes_per_prim']:.2f} vs "
          f"{res_rvq['rows'][1]['model_bytes_per_prim']:.2f} B/prim")

    order = morton_order(means)''', 1)

io.open(B, "w", encoding="utf-8", newline="\n").write(b)
print("ok")
