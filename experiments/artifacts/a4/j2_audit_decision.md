# J2 — is a tolerance certifiable without the audit?

Cells: **56** (8 scene-checkpoints x 7 edits; bonsai excluded upstream). Losses in pp, positive = coverage lost.

## Decision rule: cross-asset prior (leave-one-asset-out median)

| eps (pp) | n | correct accept | false accept | false reject | accuracy | mean excess on false accept (pp) |
|---|---|---|---|---|---|---|
| 0.5 | 56 | 53 | 0 | 3 | 0.946 | 0.0 |
| 1.0 | 56 | 48 | 4 | 4 | 0.857 | 1.38 |
| 2.0 | 56 | 54 | 2 | 0 | 0.964 | 1.36 |
| 5.0 | 56 | 52 | 3 | 1 | 0.929 | 1.8 |

## Decision rule: 2-view / full audit on shipped calibration views


**eps = 0.5 pp**

| safety margin delta (pp) | correct accept | false accept | false reject | accuracy | mean excess (pp) |
|---|---|---|---|---|---|
| 0.0 | 27 | 0 | 0 | 1.0 | 0.0 |
| 1.0 | 0 | 0 | 27 | 0.518 | 0.0 |
| 2.0 | 0 | 0 | 27 | 0.518 | 0.0 |
| 3.0 | 0 | 0 | 27 | 0.518 | 0.0 |

**eps = 1.0 pp**

| safety margin delta (pp) | correct accept | false accept | false reject | accuracy | mean excess (pp) |
|---|---|---|---|---|---|
| 0.0 | 28 | 0 | 0 | 1.0 | 0.0 |
| 1.0 | 13 | 0 | 15 | 0.732 | 0.0 |
| 2.0 | 0 | 0 | 28 | 0.5 | 0.0 |
| 3.0 | 0 | 0 | 28 | 0.5 | 0.0 |

**eps = 2.0 pp**

| safety margin delta (pp) | correct accept | false accept | false reject | accuracy | mean excess (pp) |
|---|---|---|---|---|---|
| 0.0 | 30 | 0 | 0 | 1.0 | 0.0 |
| 1.0 | 28 | 0 | 2 | 0.964 | 0.0 |
| 2.0 | 13 | 0 | 17 | 0.696 | 0.0 |
| 3.0 | 0 | 0 | 30 | 0.464 | 0.0 |

**eps = 5.0 pp**

| safety margin delta (pp) | correct accept | false accept | false reject | accuracy | mean excess (pp) |
|---|---|---|---|---|---|
| 0.0 | 38 | 0 | 0 | 1.0 | 0.0 |
| 1.0 | 34 | 0 | 4 | 0.929 | 0.0 |
| 2.0 | 31 | 0 | 7 | 0.875 | 0.0 |
| 3.0 | 30 | 0 | 8 | 0.857 | 0.0 |

## Smallest safety margin that removes every false accept

| eps (pp) | delta (pp) |
|---|---|
| 0.5 | 0.0 |
| 1.0 | 0.0 |
| 2.0 | 0.0 |
| 5.0 | 0.0 |
