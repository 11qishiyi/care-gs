import io

P = r"D:\3dsg_1\experiments\sota_report.py"
s = io.open(P, encoding="utf-8").read()

# 1) evaluate(): headroom filter + fidelity guardrail
a = """def evaluate(our: dict, base: dict, min_gain_pp: float = MIN_GAIN_PP,
             tol: float = TOL, frac: float = NEED_FRAC) -> dict:
    scenes = sorted(set(our) & set(base))
    detail, per_scene = [], {}
    for sc in scenes:
        wins = 0
        total = 0
        for b in base[sc]:
            mine = best_within(our[sc], b["rate"], tol)
            if mine is None:
                continue
            total += 1
            delta = mine["drop_pp"] - b["drop_pp"]
            # intervals: ours must lose less even at its pessimistic end
            sep = mine["drop_lo_pp"] > b["drop_hi_pp"]
            ok = delta >= min_gain_pp and sep
            wins += int(ok)
            detail.append(dict(scene=sc, baseline=b["variant"],
                               base_rate=b["rate"], base_drop=b["drop_pp"],
                               our_variant=mine["variant"], our_rate=mine["rate"],
                               our_drop=mine["drop_pp"], delta_pp=delta,
                               separated=bool(sep), win=bool(ok)))
        per_scene[sc] = dict(wins=wins, total=total,
                             all_beaten=bool(total > 0 and wins == total))"""
b = """def evaluate(our: dict, base: dict, min_gain_pp: float = MIN_GAIN_PP,
             tol: float = TOL, frac: float = NEED_FRAC,
             headroom_pp: float = 0.0, max_dpsnr_gap: float = 0.3) -> dict:
    \"\"\"Head-to-head at the baselines' own budgets.

    ``headroom_pp`` drops baselines whose own loss is better than ``-headroom_pp``:
    a baseline that already loses nothing leaves no room for a 1 pp win, so including
    it makes the criterion unpassable by construction (the ceiling lesson of N13).
    \"\"\"
    scenes = sorted(set(our) & set(base))
    detail, per_scene, skipped = [], {}, 0
    for sc in scenes:
        wins = 0
        total = 0
        for b in base[sc]:
            if b["drop_pp"] > -headroom_pp:
                skipped += 1
                continue
            mine = best_within(our[sc], b["rate"], tol)
            if mine is None:
                skipped += 1
                continue
            total += 1
            delta = mine["drop_pp"] - b["drop_pp"]
            # intervals: ours must lose less even at its pessimistic end
            sep = mine["drop_lo_pp"] > b["drop_hi_pp"]
            # S1b: we may win coverage but must not buy it with fidelity
            gap = None
            if mine.get("d_psnr") is not None and b.get("d_psnr") is not None:
                gap = float(mine["d_psnr"]) - float(b["d_psnr"])
            ok = delta >= min_gain_pp and sep and (gap is None or gap <= max_dpsnr_gap)
            wins += int(ok)
            detail.append(dict(scene=sc, baseline=b["variant"],
                               base_rate=b["rate"], base_drop=b["drop_pp"],
                               our_variant=mine["variant"], our_rate=mine["rate"],
                               our_drop=mine["drop_pp"], delta_pp=delta,
                               dpsnr_gap=gap, separated=bool(sep), win=bool(ok)))
        per_scene[sc] = dict(wins=wins, total=total,
                             all_beaten=bool(total > 0 and wins == total))"""
assert a in s
s = s.replace(a, b, 1)

# 2) report the skipped count and the headroom used
a2 = """        delta_max_pp=max(deltas) if deltas else None,
        verdict=bool(n_pass >= _need(n_scenes, frac)),
    )"""
b2 = """        delta_max_pp=max(deltas) if deltas else None,
        pairs_skipped=skipped, headroom_pp=headroom_pp,
        verdict=bool(n_pass >= _need(n_scenes, frac)),
    )"""
assert a2 in s
s = s.replace(a2, b2, 1)

# 3) CLI flag + pass-through
a3 = """    ap.add_argument("--tol", type=float, default=TOL)"""
b3 = """    ap.add_argument("--tol", type=float, default=TOL)
    ap.add_argument("--headroom-pp", type=float, default=0.0,
                    help="drop baselines that already lose less than this (a 1 pp win "
                         "is impossible when the baseline loses nothing)")"""
assert a3 in s
s = s.replace(a3, b3, 1)

a4 = "    res = evaluate(our, base, args.min_gain_pp, args.tol)"
b4 = ("    res = evaluate(our, base, args.min_gain_pp, args.tol,\n"
      "                  headroom_pp=args.headroom_pp)")
assert a4 in s
s = s.replace(a4, b4, 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("added headroom filter and the fidelity guardrail")
