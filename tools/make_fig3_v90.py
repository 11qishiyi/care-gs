"""Figure 2 (fig_three) rebuilt for the v90 battery: four scenes x four yardsticks.

The previous version (tools/make_fig3.py) drew two scenes (bicycle, flowers) at
two pruning budgets.  This version draws the 30 %-pruning drop of four certificate
yardsticks for four scenes: coverage (pixel certificate), local re-localisation,
registration consensus (paired per-view inlier ratio) and two-view relative pose.

Run from the repository root (``D:\\3dsg_1``)::

    python tools/make_fig3_v90.py

Outputs
-------
figures_v2/fig_three.pdf   (vector, the file the paper already includes)
figures_v2/fig_three.png   (dpi 200, inspection only)

Every plotted number is printed to stdout and checked against the values tabulated
in the paper; the script aborts instead of plotting if any of them is off by more
than 0.1 points.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENES = ['bicycle', 'flowers', 'stump', 'treehill']


def path(*parts):
    return os.path.join(ROOT, *parts)


def load_json(*parts):
    with open(path(*parts), encoding='utf-8') as fh:
        return json.load(fh)


def boot(x, n=4000, seed=0):
    """Paired view-level bootstrap of the mean (identical to tools/make_fig3.py)."""
    v = np.asarray(x, np.float64)
    v = v[~np.isnan(v)]
    rng = np.random.default_rng(seed)
    m = rng.choice(v, size=(n, v.size), replace=True).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


# --------------------------------------------------------------------------- data
# 1) coverage + local re-localisation: one-pass measurement per scene (results_v90)
coverage, local = {}, {}
for s in SCENES:
    d = load_json('results_v90', 'stage9', f'{s}.json')
    assert d['scene'] == s, (s, d['scene'])
    coverage[s] = 100.0 * d['coverage']['opacity30']['drop_mean']
    t = d['task']['tol2_peak0.6']
    local[s] = 100.0 * (t['opacity30'] - t['clean'])

# 2) registration consensus: paired per-view inlier ratio, clean vs prune30
#    (bicycle/flowers in results_v70, stump/treehill in results_v90)
reg = {}
for rel in (('results_v70', 'second_task.json'),
            ('results_v90', 'second_task_stump_treehill.json')):
    for d in load_json(*rel):
        clean = np.array([r['inlier_ratio'] for r in d['variants']['clean']['per_view']])
        pr30 = np.array([r['inlier_ratio'] for r in d['variants']['prune30']['per_view']])
        diff = 100.0 * (pr30 - clean)
        lo, hi = boot(diff)
        reg[d['scene']] = dict(drop=float(diff.mean()), lo=lo, hi=hi, n=diff.size)

# 3) two-view relative pose: success rate at 5 deg, prune30 vs clean
#    (bicycle/flowers in results_v80, stump/treehill in results_v90)
pose = {}
for rel in (('results_v80', 'third_task.json'),
            ('results_v90', 'third_task_stump_treehill.json')):
    for d in load_json(*rel):
        v = d['variants']
        pose[d['scene']] = 100.0 * (v['prune30']['success_5deg'] - v['clean']['success_5deg'])

series = {
    'coverage': [coverage[s] for s in SCENES],
    'local': [local[s] for s in SCENES],
    'registration': [reg[s]['drop'] for s in SCENES],
    'pose': [pose[s] for s in SCENES],
}

# values as tabulated in the paper (points, 30 % pruning)
EXPECTED = {
    'coverage': [-22.1, -10.8, -27.7, -15.2],
    'local': [-27.3, -11.1, -12.8, -34.4],
    'registration': [-3.9, -2.6, -2.5, -11.3],
    'pose': [-8.3, -4.8, -6.7, 5.9],
}

print('=== Figure 2 inputs: drop from the fresh asset at 30 % pruning (points) ===')
print(f"{'scene':9s}" + ''.join(f'{k:>15s}' for k in series))
for i, s in enumerate(SCENES):
    row = ''.join(f'{series[k][i]:15.1f}' for k in series)
    print(f'{s:9s}{row}')
print('\nregistration consensus 95 % paired bootstrap CI (4000 resamples, seed 0):')
for s in SCENES:
    r = reg[s]
    print(f'  {s:9s} drop={r["drop"]:+5.1f}pp  [{r["lo"]:+.1f},{r["hi"]:+.1f}]  n_views={r["n"]}')

bad = [(k, s, series[k][i], EXPECTED[k][i])
       for k in series for i, s in enumerate(SCENES)
       if abs(series[k][i] - EXPECTED[k][i]) > 0.1]
if bad:
    for k, s, got, want in bad:
        print(f'MISMATCH {k:13s} {s:9s} got {got:+.2f} expected {want:+.1f}')
    raise SystemExit('refusing to plot: values disagree with the paper table')

# --------------------------------------------------------------------------- plot
plt.rcParams.update({
    'font.size': 7,
    'axes.labelsize': 7,
    'xtick.labelsize': 7,
    'ytick.labelsize': 7,
    'legend.fontsize': 7,
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
    'xtick.major.size': 2.5,
    'ytick.major.size': 2.5,
    'pdf.fonttype': 42,
})

fig, ax = plt.subplots(figsize=(6.0, 2.3))
xs = np.arange(len(SCENES))
w = 0.2
off = [-1.5 * w, -0.5 * w, 0.5 * w, 1.5 * w]

bars = [
    ('coverage certificate', '#2b6cb0', None, off[0]),
    ('local re-localisation', '#63b3ed', None, off[1]),
    ('registration consensus', '#cbd5e0', '#4a5568', off[2]),
    ('two-view pose', '#f6ad55', None, off[3]),
]
for (label, color, edge, dx), key in zip(bars, ('coverage', 'local', 'registration', 'pose')):
    ax.bar(xs + dx, series[key], w, label=label, color=color,
           edgecolor=edge, linewidth=0.5 if edge else 0)

ax.axhline(0, color='#4a5568', linewidth=0.6)
ax.set_xticks(xs)
ax.set_xticklabels(SCENES)
ax.set_xlim(-0.5, len(SCENES) - 0.5)
ax.set_ylim(-40, 15)
ax.set_yticks(np.arange(-40, 11, 10))
ax.set_ylabel('drop from fresh asset (points)')
ax.grid(axis='y', alpha=0.25, linewidth=0.5)
ax.set_axisbelow(True)
ax.legend(frameon=False, ncol=4, loc='upper center', handlelength=1.3,
          columnspacing=1.1, handletextpad=0.45, borderaxespad=0.25)
fig.tight_layout(pad=0.3)

os.makedirs(path('figures_v2'), exist_ok=True)
out_pdf = path('figures_v2', 'fig_three.pdf')
out_png = path('figures_v2', 'fig_three.png')
fig.savefig(out_pdf, metadata={'CreationDate': None})
fig.savefig(out_png, dpi=200)
print('\nwrote figures_v2/fig_three.pdf and figures_v2/fig_three.png')
