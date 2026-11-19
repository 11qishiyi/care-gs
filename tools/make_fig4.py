"""Regenerate the four-yardstick figure: coverage, local matching, registration, pose."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

D = 'results_v70'
D80 = 'results_v80'
scenes = ['bicycle', 'flowers']

cov, loc, reg, pose = {}, {}, {}, {}
for s in scenes:
    diag = json.load(open(os.path.join(D, f'diag_{s}.json'), encoding='utf-8'))[0]
    cov[s] = -100 * diag['protocols']['raw']['drop_mean']
    b = json.load(open(os.path.join(D80, 'battery', f'{s}.json'), encoding='utf-8'))
    v = b['task_sweep']['s32_w24']['tol2_peak0.6']
    loc[s] = 100 * (v['prune30'] - v['clean'])
    st = json.load(open(os.path.join(D, 'second_task.json'), encoding='utf-8'))
    d = [x for x in st if x['scene'] == s][0]
    clean = np.array([r['inlier_ratio'] for r in d['variants']['clean']['per_view']])
    pr = np.array([r['inlier_ratio'] for r in d['variants']['prune30']['per_view']])
    reg[s] = float(100 * (pr - clean).mean())
    tt = json.load(open(os.path.join(D80, 'third_task.json'), encoding='utf-8'))
    t = [x for x in tt if x['scene'] == s][0]
    pose[s] = 100 * (t['variants']['prune30']['success_5deg'] - t['variants']['clean']['success_5deg'])

labels = ['coverage\ncertificate', 'local\nre-localisation', 'registration\nconsensus',
          'relative pose\n(success@5 deg)']
vals = {
    'bicycle': [-cov['bicycle'], loc['bicycle'], reg['bicycle'], pose['bicycle']],
    'flowers': [-cov['flowers'], loc['flowers'], reg['flowers'], pose['flowers']],
}
print('bicycle', [round(x, 1) for x in vals['bicycle']])
print('flowers', [round(x, 1) for x in vals['flowers']])

fig, ax = plt.subplots(figsize=(6.2, 2.3), constrained_layout=True)
x = np.arange(len(labels))
w = 0.36
ax.bar(x - w / 2, vals['bicycle'], w, label='bicycle', color='#2b6cb0')
ax.bar(x + w / 2, vals['flowers'], w, label='flowers', color='#63b3ed')
ax.axhline(0, color='#4a5568', linewidth=0.6)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=7)
ax.set_ylabel('loss at 30% pruning (points)', fontsize=7.5)
ax.tick_params(labelsize=7)
ax.legend(frameon=False, fontsize=7)
ax.grid(axis='y', alpha=0.25, linewidth=0.5)
ax.set_axisbelow(True)
os.makedirs('figures_v2', exist_ok=True)
fig.savefig(os.path.join('figures_v2', 'fig_three.pdf'))
fig.savefig(os.path.join('figures_v2', 'fig_three.png'), dpi=200)
print('wrote figures_v2/fig_three.pdf')
