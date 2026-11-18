# Jev agreement (test)

AUROC of reward vs gold match per field (95% CI from bootstrap resampling item ids). Probabilities are rounded to 2 decimals; ties get averaged ranks.

**Headline figures are parseable-only**: rows whose output does not parse get reward 0 and match False by construction, so they are separable trivially. AUROC that includes unparseable rows is shown for completeness but is NOT comparable across runs, because runs differ in parse rate and base rate. Pooled figures stack the same items once per run, so CIs resample item ids (cluster bootstrap).

## Unparseable outputs per run

| run | unparseable / total |
|---|---|
| gemma3-1b-lora-n207 | 2 / 176 |

## gemma3-1b-lora-n207

| field | gold acc | B1 AUROC (parseable) | B2 AUROC (parseable) | B1 AUROC (all rows) | B2 AUROC (all rows) |
|---|---|---|---|---|---|
| incident_type | 0.631 | 0.949 [0.915, 0.975] | 0.872 [0.815, 0.926] | 0.950 [0.922, 0.975] | 0.875 [0.824, 0.927] |
| severity | 0.483 | 0.878 [0.827, 0.923] | 0.713 [0.635, 0.791] | 0.881 [0.825, 0.926] | 0.719 [0.646, 0.795] |
| road_obstruction | 0.545 | 0.896 [0.848, 0.942] | 0.790 [0.721, 0.854] | 0.899 [0.850, 0.941] | 0.795 [0.727, 0.860] |
| road | 0.756 | 0.809 [0.732, 0.875] | 0.885 [0.808, 0.942] | 0.815 [0.745, 0.882] | 0.890 [0.821, 0.947] |

## Macro-averaged over runs (mean of per-run parseable-only AUROC)

| field | B1 AUROC | B2 AUROC |
|---|---|---|
| incident_type | 0.949 [0.915, 0.975] | 0.872 [0.815, 0.926] |
| severity | 0.878 [0.827, 0.923] | 0.713 [0.635, 0.791] |
| road_obstruction | 0.896 [0.848, 0.942] | 0.790 [0.721, 0.854] |
| road | 0.809 [0.732, 0.875] | 0.885 [0.808, 0.942] |

## Pooled over runs, parseable-only (secondary; mixes between-run differences)

| field | B1 AUROC | B2 AUROC |
|---|---|---|
| incident_type | 0.949 [0.915, 0.975] | 0.872 [0.815, 0.926] |
| severity | 0.878 [0.827, 0.923] | 0.713 [0.635, 0.791] |
| road_obstruction | 0.896 [0.848, 0.942] | 0.790 [0.721, 0.854] |
| road | 0.809 [0.732, 0.875] | 0.885 [0.808, 0.942] |

## Pooled over runs, all rows (not comparable across runs; confounded by parseability)

| field | B1 AUROC | B2 AUROC |
|---|---|---|
| incident_type | 0.950 [0.922, 0.975] | 0.875 [0.824, 0.927] |
| severity | 0.881 [0.825, 0.926] | 0.719 [0.646, 0.795] |
| road_obstruction | 0.899 [0.850, 0.941] | 0.795 [0.727, 0.860] |
| road | 0.815 [0.745, 0.882] | 0.890 [0.821, 0.947] |

## Run ranking: mean composite reward vs gold mean field accuracy

| run | gold mean field acc | B1 mean composite | B2 mean composite |
|---|---|---|---|
| gemma3-1b-lora-n207 | 0.604 | 0.564 | 0.632 |

Gold order (best first): gemma3-1b-lora-n207
- B1 order: gemma3-1b-lora-n207; Spearman n/a; pairwise order agreement 0/0
- B2 order: gemma3-1b-lora-n207; Spearman n/a; pairwise order agreement 0/0

Caution: with only 4 runs and near-tied pairs (see the table), Spearman 0.8 versus 1.0 is not a meaningful difference between designs; the ranking evidence is weak for both.
