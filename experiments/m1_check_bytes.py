"""Assert the mirrored byte model in m1_analyse agrees with qfp_rd on every variant.

The CPU analyser reimplements the byte model so that it never needs torch; a silent
divergence between the two would make every rate in the verdict wrong, so this gate
compares them name by name.  Dictionary-coded variants (``vq``) charge the codebook
to the asset, so both sides are fed the same primitive count.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m1_analyse as A                                          # noqa: E402
import qfp_rd as Q                                             # noqa: E402

#: a mid-sized asset, so the codebook share is exercised at a realistic denominator
N_STORED = 5_000_000


def main() -> int:
    # Product quantisation splits the block, so it only exists for degrees whose
    # coefficient count is divisible by the group count; skip those pairs instead of
    # pretending the variant is measurable there.
    def _splits(name, deg):
        tok = [t for t in name.split("_") if t.startswith("pq")]
        if not tok:
            return True
        m = int(tok[0][2:].split("-")[0])
        return Q.sh_cols(deg) % m == 0

    grids = {"m1": Q.DEFAULT_VARIANTS, "m2": Q.AFQ_VARIANTS, "m3": Q.M3_VARIANTS,
             "m7": Q.M7_VARIANTS, "m8": Q.M8_VARIANTS, "m9": Q.M9_VARIANTS,
             "m10": Q.M10_VARIANTS, "m11": Q.M11_VARIANTS, "m12": Q.M12_VARIANTS,
             "m15": Q.M15_VARIANTS, "m16": Q.M16_VARIANTS, "sota": Q.SOTA_VARIANTS}
    bad = 0
    total = 0
    for grid, raw in grids.items():
        names = [v.strip() for v in raw.split(",")] if isinstance(raw, str) else list(raw)
        for deg in (0, 1, 2, 3):
            for name in names:
                if not _splits(name, deg):
                    continue
                total += 1
                spec = Q.parse_spec(name)
                n_st = int(round(N_STORED * spec.keep))
                r_ref = spec.rate_vs_fp32(deg, n_stored=n_st)
                b_ref = spec.bytes_per_prim(deg, n_stored=n_st)
                r_got, b_got = A.spec_rate(name, deg, n_stored=n_st)
                ok = (abs(r_ref - r_got) < 1e-12 and abs(b_ref - b_got) < 1e-12)
                fam_ok = spec.family == A.family_of(name)
                if not (ok and fam_ok):
                    bad += 1
                    print(f"FAIL {grid} deg={deg} {name}: rate {r_ref} vs {r_got}, "
                          f"bpp {b_ref} vs {b_got}, family {spec.family} vs {A.family_of(name)}")
    print(f"{'FAIL' if bad else 'PASS'}: {bad} mismatch(es) over {total} case(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
