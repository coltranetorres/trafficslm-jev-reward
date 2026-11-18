# Jev agreement (validation)

AUROC of reward vs gold match per field (95% CI from bootstrap resampling item ids). Probabilities are rounded to 2 decimals; ties get averaged ranks.

**Headline figures are parseable-only**: rows whose output does not parse get reward 0 and match False by construction, so they are separable trivially. AUROC that includes unparseable rows is shown for completeness but is NOT comparable across runs, because runs differ in parse rate and base rate. Pooled figures stack the same items once per run, so CIs resample item ids (cluster bootstrap).

## Unparseable outputs per run

| run | unparseable / total |
|---|---|
| gemma3-1b-zeroshot | 27 / 40 |
| gemma3-1b-fewshot | 24 / 40 |
| gemma3-1b-lora-n207 | 0 / 40 |
| qwen2.5-1.5b-lora-n207 | 0 / 40 |

## gemma3-1b-zeroshot

| field | gold acc | B1 AUROC (parseable) | B2 AUROC (parseable) | B1 AUROC (all rows) | B2 AUROC (all rows) |
|---|---|---|---|---|---|
| incident_type | 0.100 | 0.944 [0.762, 1.000] | 0.861 [0.583, 1.000] | 0.986 [0.941, 1.000] | 0.965 [0.892, 1.000] |
| severity | 0.225 | 0.944 [0.762, 1.000] | 0.806 [0.429, 1.000] | 0.993 [0.965, 1.000] | 0.975 [0.917, 1.000] |
| road_obstruction | 0.225 | 1.000 [1.000, 1.000] | 0.944 [0.762, 1.000] | 1.000 [1.000, 1.000] | 0.993 [0.964, 1.000] |
| road | 0.175 | 0.643 [0.381, 0.900] | 0.750 [0.389, 1.000] | 0.935 [0.858, 0.987] | 0.955 [0.875, 1.000] |

## gemma3-1b-fewshot

| field | gold acc | B1 AUROC (parseable) | B2 AUROC (parseable) | B1 AUROC (all rows) | B2 AUROC (all rows) |
|---|---|---|---|---|---|
| incident_type | 0.125 | 0.927 [0.750, 1.000] | 0.818 [0.500, 1.000] | 0.977 [0.913, 1.000] | 0.943 [0.833, 1.000] |
| severity | 0.225 | 0.944 [0.809, 1.000] | 0.810 [0.550, 1.000] | 0.987 [0.947, 1.000] | 0.957 [0.883, 1.000] |
| road_obstruction | 0.275 | 0.909 [0.717, 1.000] | 0.827 [0.562, 1.000] | 0.984 [0.948, 1.000] | 0.970 [0.915, 1.000] |
| road | 0.250 | 0.600 [0.292, 0.892] | 0.700 [0.391, 1.000] | 0.920 [0.826, 0.989] | 0.940 [0.856, 1.000] |

## gemma3-1b-lora-n207

| field | gold acc | B1 AUROC (parseable) | B2 AUROC (parseable) | B1 AUROC (all rows) | B2 AUROC (all rows) |
|---|---|---|---|---|---|
| incident_type | 0.775 | 0.887 [0.764, 0.976] | 0.509 [0.312, 0.711] | 0.887 [0.764, 0.976] | 0.509 [0.312, 0.711] |
| severity | 0.725 | 0.906 [0.793, 0.983] | 0.746 [0.555, 0.902] | 0.906 [0.793, 0.983] | 0.746 [0.555, 0.902] |
| road_obstruction | 0.775 | 0.894 [0.777, 0.986] | 0.891 [0.769, 0.984] | 0.894 [0.777, 0.986] | 0.891 [0.769, 0.984] |
| road | 0.750 | 0.813 [0.677, 0.933] | 0.897 [0.790, 0.980] | 0.813 [0.677, 0.933] | 0.897 [0.790, 0.980] |

## qwen2.5-1.5b-lora-n207

| field | gold acc | B1 AUROC (parseable) | B2 AUROC (parseable) | B1 AUROC (all rows) | B2 AUROC (all rows) |
|---|---|---|---|---|---|
| incident_type | 0.600 | 0.969 [0.912, 1.000] | 0.867 [0.745, 0.968] | 0.969 [0.912, 1.000] | 0.867 [0.745, 0.968] |
| severity | 0.625 | 0.908 [0.804, 0.986] | 0.764 [0.601, 0.910] | 0.908 [0.804, 0.986] | 0.764 [0.601, 0.910] |
| road_obstruction | 0.550 | 0.832 [0.693, 0.944] | 0.871 [0.739, 0.956] | 0.832 [0.693, 0.944] | 0.871 [0.739, 0.956] |
| road | 0.800 | 0.930 [0.840, 1.000] | 0.922 [0.771, 1.000] | 0.930 [0.840, 1.000] | 0.922 [0.771, 1.000] |

## Macro-averaged over runs (mean of per-run parseable-only AUROC)

| field | B1 AUROC | B2 AUROC |
|---|---|---|
| incident_type | 0.932 [0.836, 0.990] | 0.764 [0.627, 0.881] |
| severity | 0.926 [0.832, 0.981] | 0.781 [0.620, 0.898] |
| road_obstruction | 0.909 [0.823, 0.973] | 0.883 [0.781, 0.960] |
| road | 0.746 [0.656, 0.856] | 0.817 [0.683, 0.931] |

## Pooled over runs, parseable-only (secondary; mixes between-run differences)

| field | B1 AUROC | B2 AUROC |
|---|---|---|
| incident_type | 0.947 [0.882, 0.989] | 0.777 [0.653, 0.887] |
| severity | 0.910 [0.813, 0.971] | 0.762 [0.621, 0.875] |
| road_obstruction | 0.876 [0.766, 0.959] | 0.880 [0.786, 0.946] |
| road | 0.736 [0.600, 0.854] | 0.820 [0.693, 0.921] |

## Pooled over runs, all rows (not comparable across runs; confounded by parseability)

| field | B1 AUROC | B2 AUROC |
|---|---|---|
| incident_type | 0.975 [0.944, 0.995] | 0.896 [0.822, 0.951] |
| severity | 0.954 [0.906, 0.987] | 0.900 [0.840, 0.953] |
| road_obstruction | 0.945 [0.899, 0.983] | 0.950 [0.911, 0.978] |
| road | 0.875 [0.804, 0.937] | 0.933 [0.879, 0.972] |

## Run ranking: mean composite reward vs gold mean field accuracy

| run | gold mean field acc | B1 mean composite | B2 mean composite |
|---|---|---|---|
| gemma3-1b-zeroshot | 0.181 | 0.211 | 0.187 |
| gemma3-1b-fewshot | 0.219 | 0.208 | 0.240 |
| gemma3-1b-lora-n207 | 0.756 | 0.634 | 0.674 |
| qwen2.5-1.5b-lora-n207 | 0.644 | 0.611 | 0.634 |

Gold order (best first): gemma3-1b-lora-n207 > qwen2.5-1.5b-lora-n207 > gemma3-1b-fewshot > gemma3-1b-zeroshot
- B1 order: gemma3-1b-lora-n207 > qwen2.5-1.5b-lora-n207 > gemma3-1b-zeroshot > gemma3-1b-fewshot; Spearman 0.800; pairwise order agreement 5/6
- B2 order: gemma3-1b-lora-n207 > qwen2.5-1.5b-lora-n207 > gemma3-1b-fewshot > gemma3-1b-zeroshot; Spearman 1.000; pairwise order agreement 6/6

Caution: with only 4 runs and near-tied pairs (see the table), Spearman 0.8 versus 1.0 is not a meaningful difference between designs; the ranking evidence is weak for both.
