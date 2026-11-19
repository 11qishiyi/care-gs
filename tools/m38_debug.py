"""Debug the M38 round trip: does the container describe the same primitives as the encoder's own answer?"""
import sys

import numpy as np

sys.path.insert(0, "experiments")

import m19_codec as C
import m38_vq as V
from tests.test_m38_vq import _Splats

s = _Splats()
rec = V.build(s, k=256, spec_name="gp6-6-6_c8_sh3", rank=4, bits_total=24, iters=6, log=lambda *a: None)
p = "experiments/artifacts/_m38_debug.gs1"
C.write_container(p, rec["streams"], rec["meta"], level=3)
meta, streams = C.read_container(p)
attrs = V.decode_attrs(streams, meta)
expect = rec["x"][np.asarray(rec["idx"], np.int64)]
got = np.asarray(attrs["scales"], np.float32).reshape(-1, 3)
print("shapes", got.shape, expect[:, :3].shape)
print("first 3 decoded", got[:3])
print("first 3 expect ", expect[:3, :3])
d = np.abs(got - expect[:, :3])
print("mean|d|", float(d.mean()), "max|d|", float(d.max()))
print("index match:", np.array_equal(np.asarray(rec["idx"]), C.unpack_bits(streams["geo_vq_idx"], meta["geo_vq_bits"], meta["n"], dtype=np.uint16).astype(np.uint32)))
print("meta n", meta["n"], "k", meta["geo_vq_k"], "bits", meta["geo_vq_bits"])
print("cb bytes", len(streams["geo_vq_cb"]))
