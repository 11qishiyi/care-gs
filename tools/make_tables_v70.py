"""Emit LaTeX table bodies for the corrected-protocol section from results_v70."""
import glob
import json
import os

D = 'results_v70'


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


diag = {}
for p in sorted(glob.glob(os.path.join(D, 'diag_*.json'))):
    d = load(p)
    diag[(d[0] if isinstance(d, list) else d)['scene']] = (d[0] if isinstance(d, list) else d)
bat = {}
for p in sorted(glob.glob(os.path.join(D, 'battery_*.json'))):
    d = load(p)
    bat[d['scene']] = d

SC = [s for s in ('bicycle', 'flowers', 'stump', 'treehill') if s in diag]

print('% ==== TABLE: asset and fresh certificate, honest protocol ====')
for s in SC:
    d = diag[s]
    r = d['protocols']['raw']
    print(f"{s:9s} & {d['n_primitives']/1e6:.2f}M & {d['n_views']} & {r['psnr']:.1f} & "
          f"{r['resid_median']:.4f} & {r['clean_mean']:.3f} & "
          f"${100*r['drop_mean']:+.1f}\\,[{100*r['drop_lo']:+.1f},{100*r['drop_hi']:+.1f}]$ & "
          f"${100*r['q_growth_mean']:+.0f}\\%$ \\\\")

print('% ==== TABLE: GT convention comparison ====')
for s in SC:
    d = diag[s]
    a, b = d['protocols']['raw'], d['protocols']['norm_gt']
    ratio = (b['drop_mean'] / a['drop_mean']) if a['drop_mean'] else float('nan')
    print(f"{s:9s} & {a['psnr']:.1f} & {b['psnr']:.1f} & {a['resid_median']:.4f} & "
          f"{b['resid_median']:.4f} & ${100*a['drop_mean']:+.1f}$ & ${100*b['drop_mean']:+.1f}$ & "
          f"{ratio:.2f}$\\times$ \\\\")

print('% ==== TABLE: dose-response (battery scenes) ====')
for s in bat:
    b = bat[s]
    row = [f"{s:9s}"]
    for name in ('prune70', 'prune50', 'prune30', 'prune10'):
        c = b['coverage'].get(name)
        row.append(f"${100*c['drop_mean']:+.1f}$" if c else "--")
    for name in ('prune70', 'prune50', 'prune30', 'prune10'):
        c = b['coverage'].get(name)
        row.append(f"${100*c['q_growth_mean']:+.0f}\\%$" if c else "--")
    for name in ('shdeg1', 'quant8'):
        c = b['coverage'].get(name)
        row.append(f"${100*c['drop_mean']:+.1f}$" if c else "--")
    print(' & '.join(row) + ' \\\\')

print('% ==== task sweep summary ====')
for s in bat:
    b = bat[s]
    cov30 = -100 * b['coverage']['prune30']['drop_mean']
    n = h = w = 0
    for key, grid in b['task_sweep'].items():
        for cfg, vals in grid.items():
            if 'clean' not in vals or 'prune30' not in vals:
                continue
            n += 1
            d30 = 100 * (vals['clean'] - vals['prune30'])
            h += 1 if d30 > 0 else 0
            w += 1 if d30 > cov30 else 0
    drop = [100 * (b['task_sweep'][k]['tol2_peak0.6']['prune30'] - b['task_sweep'][k]['tol2_peak0.6']['clean'])
            for k in b['task_sweep'] if 'tol2_peak0.6' in b['task_sweep'][k]]
    print(f"{s}: coverage30={cov30:.1f}pp  task30(default cfg)={drop[0]:+.1f}pp  "
          f"task hurts in {h}/{n} cells  task>coverage in {w}/{n} cells")
