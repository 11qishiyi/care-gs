"""Dose-response figure: coverage loss and quantile growth against the pruning budget."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

D = 'results_v70'
SC = ['bicycle', 'flowers', 'stump', 'treehill']
LEVELS = [('prune70', 70), ('prune50', 50), ('prune30', 30), ('prune10', 10)]
COL = {'bicycle': '#2b6cb0', 'flowers': '#2f855a', 'stump': '#b7791f', 'treehill': '#c53030'}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.3, 2.35), constrained_layout=True)
for s in SC:
    b = json.load(open(os.path.join(D, f'battery_{s}.json'), encoding='utf-8'))
    budget = [lv for _, lv in LEVELS]
    drop = [-100 * b['coverage'][k]['drop_mean'] for k, _ in LEVELS]
    qg = [100 * b['coverage'][k]['q_growth_mean'] for k, _ in LEVELS]
    ax1.plot(budget, drop, marker='o', ms=3.5, lw=1.2, color=COL[s], label=s)
    ax2.plot(budget, qg, marker='s', ms=3.5, lw=1.2, color=COL[s], label=s)

ax1.set_xlabel('primitives kept (%)')
ax1.set_ylabel('coverage loss (points)')
ax1.set_title('(a) damage vs budget')
ax1.invert_xaxis()
ax1.grid(alpha=0.25, lw=0.5)
ax1.set_axisbelow(True)
ax1.legend(frameon=False, fontsize=6.5, loc='upper left')

ax2.set_xlabel('primitives kept (%)')
ax2.set_ylabel('quantile growth (%)')
ax2.set_title('(b) cost of validity')
ax2.invert_xaxis()
ax2.grid(alpha=0.25, lw=0.5)
ax2.set_axisbelow(True)
ax2.legend(frameon=False, fontsize=6.5, loc='upper left')
# constrained layout handles the margins
os.makedirs('figures_v3', exist_ok=True)
fig.savefig(os.path.join('figures_v3', 'fig_dose.pdf'))
fig.savefig(os.path.join('figures_v3', 'fig_dose.png'), dpi=200)
print('wrote figures_v3/fig_dose.pdf')
for s in SC:
    b = json.load(open(os.path.join(D, f'battery_{s}.json'), encoding='utf-8'))
    print(s, [round(-100 * b['coverage'][k]['drop_mean'], 1) for k, _ in LEVELS],
          [round(100 * b['coverage'][k]['q_growth_mean'], 0) for k, _ in LEVELS])
