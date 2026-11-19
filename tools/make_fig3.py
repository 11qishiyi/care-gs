"""Paired bootstrap for the second-task (registration) deltas + the three-yardsticks figure."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

D = 'results_v70'
st = json.load(open(os.path.join(D, 'second_task.json'), encoding='utf-8'))


def boot(x, n=4000, seed=0):
    v = np.asarray(x, np.float64)
    v = v[~np.isnan(v)]
    rng = np.random.default_rng(seed)
    m = rng.choice(v, size=(n, v.size), replace=True).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


print('=== paired registration deltas (in points) ===')
summary = {}
for d in st:
    s = d['scene']
    clean = np.array([r['inlier_ratio'] for r in d['variants']['clean']['per_view']])
    summary[s] = {}
    for name in ('prune50', 'prune30', 'prune10'):
        v = np.array([r['inlier_ratio'] for r in d['variants'][name]['per_view']])
        dd = 100 * (v - clean)
        lo, hi = boot(dd)
        summary[s][name] = (dd.mean(), lo, hi)
        print(f"  {s:9s} {name:8s} delta={dd.mean():+6.1f}pp  [{lo:+.1f},{hi:+.1f}]")

# coverage + local-task numbers from the battery / diag artifacts
cov = {'bicycle': {'30': -22.1, '10': -60.0}, 'flowers': {'30': -10.8, '10': -40.8}}
bat = {s: json.load(open(os.path.join(D, f'battery_{s}.json'), encoding='utf-8'))
       for s in ('bicycle', 'flowers')}
loc = {}
for s, b in bat.items():
    c = b['task_sweep']['s32_w24']['tol2_peak0.6']
    loc[s] = {'30': 100 * (c['prune30'] - c['clean']), '10': 100 * (c['prune10'] - c['clean'])}

fig, ax = plt.subplots(figsize=(6.0, 2.3))
xs = np.arange(4)
lbl = ['bicycle\n30%', 'bicycle\n10%', 'flowers\n30%', 'flowers\n10%']
covv, locv, regv = [], [], []
for s in ('bicycle', 'flowers'):
    for k in ('30', '10'):
        covv.append(cov[s][k])
        locv.append(loc[s][k])
        regv.append(summary[s]['prune' + k][0])
w = 0.26
ax.bar(xs - w, covv, w, label='coverage certificate', color='#2b6cb0')
ax.bar(xs, locv, w, label='local re-localisation', color='#63b3ed')
ax.bar(xs + w, regv, w, label='registration consensus', color='#cbd5e0',
       edgecolor='#4a5568', linewidth=0.5)
ax.axhline(0, color='#4a5568', linewidth=0.6)
ax.set_xticks(xs)
ax.set_xticklabels(lbl)
ax.set_ylabel('drop from fresh asset (points)')
ax.legend(frameon=False, fontsize=7, loc='lower left')
ax.grid(axis='y', alpha=0.25, linewidth=0.5)
ax.set_axisbelow(True)
fig.tight_layout(pad=0.3)
os.makedirs('figures_v2', exist_ok=True)
fig.savefig(os.path.join('figures_v2', 'fig_three.pdf'))
fig.savefig(os.path.join('figures_v2', 'fig_three.png'), dpi=200)
print('wrote figures_v2/fig_three.pdf')
print('coverage', [round(x, 1) for x in covv])
print('local   ', [round(x, 1) for x in locv])
print('registration', [round(x, 1) for x in regv])
