import io

p = "experiments/m30_adapt.py"
s = io.open(p, encoding="utf-8").read()

if "def choose_bits_tilted" in s:
    print("tilt already there")
    raise SystemExit(0)

s = s.replace('''def adapt(gs1: str, out_gs1: str''', '''def choose_bits_tilted(ext: np.ndarray, nominal: int = 8, tilt: float = -0.5,
                       lo: int = 3, hi: int = 12) -> np.ndarray:
    """Width per cluster, tilted by ``tilt`` against the extent.

    ``tilt = 0`` reproduces the fixed width; ``tilt = -1`` gives clusters half the median size one extra
    bit and takes one from clusters twice the median -- i.e. it spends the same *total* budget but
    favours the dense regions.  The encoder is not allowed to look at a render, so the tilt is a
    property of the geometry alone.
    """
    mx = ext.max(axis=1)
    med = float(np.median(mx))
    rel = np.log2(np.maximum(mx, 1e-12) / max(med, 1e-12))
    b = float(nominal) + float(tilt) * rel
    return np.clip(np.rint(b), lo, hi).astype(np.int64)


def adapt(gs1: str, out_gs1: str''', 1)

s = s.replace('''          level: int = 12, target_div: float = None, log=print) -> dict:''',
              '''          level: int = 12, target_div: float = None, tilt: float = None,
          match_bytes: bool = False, log=print) -> dict:''', 1)

s = s.replace('''    ref = float(target_div if target_div else (1 << int(nominal)) - 1)
    bits = choose_bits(ext, lo=lo, hi=hi, ref=ref)''',
              '''    ref = float(target_div if target_div else (1 << int(nominal)) - 1)
    if tilt is not None:
        bits = choose_bits_tilted(ext, nominal=int(nominal), tilt=float(tilt), lo=lo, hi=hi)
        if match_bytes:
            #: budget-neutral: shift every width by the integer that lands closest to the fixed width
            base_len = len(streams["cluster_off"])
            best = None
            for shift in range(-3, 4):
                cand = np.clip(bits + shift, lo, hi)
                nbytes = int(np.sum(np.ceil(block * 3 * cand / 8.0))) + nblk
                if best is None or abs(nbytes - base_len) < abs(best[1] - base_len):
                    best = (cand, nbytes, shift)
            bits, _, shift = best
            log(f"  tilt {tilt} matched to the fixed-width budget with shift {shift:+d}")
    else:
        bits = choose_bits(ext, lo=lo, hi=hi, ref=ref)''', 1)

s = s.replace('''    ap.add_argument("--target-div", type=float, default=None)''',
              '''    ap.add_argument("--target-div", type=float, default=None)
    ap.add_argument("--tilt", type=float, default=None)
    ap.add_argument("--match-bytes", action="store_true")''', 1)

s = s.replace('''                target_div=a.target_div, log=log)''',
              '''                target_div=a.target_div, tilt=a.tilt, match_bytes=a.match_bytes, log=log)''', 1)
s = s.replace('''            "nominal": int(nominal), "target_div": float(target_div or 0)}''',
              '''            "nominal": int(nominal), "target_div": float(target_div or 0),
            "tilt": float(tilt if tilt is not None else 0.0)}''', 1)
io.open(p, "w", encoding="utf-8").write(s)
print("tilt wired")
