# Jev as a reward: findings

Research question: how closely can a Jev-based reward (`typesafe/jev-1.14`) reproduce gold-label supervision on SFT data, and where does it break? Case study: the traffic-report extraction data in this repo. Two reward designs were compared. B1 uses Jev as a classifier: it sees only the report, and the reward is the probability it gives to the candidate's value (road: a `noul` "does the report name this road"). B2 uses Jev as a verifier: it sees the report plus the candidate JSON and answers a per-field `noul` ("is this field correct"). Question wording was written from the annotation guidelines in Task 2 before any validation run and was never changed afterwards (there is no separate freeze commit; the wording in `questions.py` is the first version). No RL was run; this measures reward quality only.

## Scope of the test pass (read this first)

**Test scoring covers one run only: `gemma3-1b-lora-n207`** (the best Gemma LoRA by validation), on all 176 test items, B1 and B2. Of those 176 outputs, 2 are unparseable (reward 0), so the parseable-only headline uses 174 items. Nine runs were originally declared; Cole cut the scope to one run before any test result was seen. A first nine-run analyze invocation was started and stopped by hand before it logged or wrote anything (see Limits). Consequences:

- **The ranking question (does the reward order the runs like gold does?) is not answered on test.** The only ranking evidence is the validation pass over 4 runs, which has near-ties and is weak (see below).
- Everything on test below is a single model's outputs, one seed. Conclusions about "how Jev tracks gold" are conclusions about this model's error distribution.

## 1. Agreement (test, gemma3-1b-lora-n207, parseable-only)

AUROC of reward versus "field matches gold" (95% cluster-bootstrap CI over item ids). Gold accuracy in parentheses.

| field (gold acc) | B1 AUROC | B2 AUROC |
|---|---|---|
| incident_type (0.63) | 0.949 [0.915, 0.975] | 0.872 [0.815, 0.926] |
| severity (0.48) | 0.878 [0.827, 0.923] | 0.713 [0.635, 0.791] |
| road_obstruction (0.55) | 0.896 [0.848, 0.942] | 0.790 [0.721, 0.854] |
| road (0.76) | 0.809 [0.732, 0.875] | 0.885 [0.808, 0.942] |

Gold accuracy is over all 176 rows; the AUROCs use the 174 parseable rows. The road row for B1 is depressed by the null-road rule (below): restricted to the 145 parseable rows with a non-null predicted road, road AUROC is B1 0.851, B2 0.891 (`jev_rl/results/label_audit_test.md`).

With one run, the macro average over runs equals the per-run row, so there is no separate macro table to report. Mean composite reward on test: B1 0.564, B2 0.632 (gold mean field accuracy 0.604). Including the two unparseable rows moves AUROCs by at most 0.006 (full table in `jev_rl/results/test_agreement.md`).

What this shows: for the three enum fields B1 has the higher AUROC on all three, clearly on severity (CIs separated); on incident_type and road_obstruction the CIs touch or overlap slightly (road_obstruction: B1 [0.848, 0.942] vs B2 [0.721, 0.854]). The CIs come from separate bootstraps and no paired difference test was run, so only the severity gap should be read as clear. On road B2 is higher, but part of that gap is an artifact of the null-road rule: B1 scores a null predicted road 0.0 without a call, while gold matching counts null/null as correct, and 16 of the 29 null predictions on test are correct null/null yet score 0 under B1 (B2 scores them normally). On rows with a non-null predicted road (n=145) the gap shrinks to B1 0.851 vs B2 0.891 (no CIs computed). So the road B1-vs-B2 comparison is not clean. All AUROCs are well above 0.5, so both rewards carry real signal about gold matches. They are not close to a perfect substitute: at 0.88 to 0.90 for B1 on severity and obstruction, a meaningful share of correct/incorrect pairs is ordered wrongly. Jev probabilities are rounded to 2 decimals in the API output, so scores are coarsely tied; ties get averaged ranks.

## 2. Ranking across runs

Not evidenced on test (one run scored). On validation (40 items, 4 runs: gemma zero-shot, gemma few-shot, gemma LoRA, qwen LoRA) the analysis already flagged that with 4 runs and near-tied pairs, a Spearman of 0.8 versus 1.0 is not a meaningful difference between designs. We do not claim that either design reproduces the gold ordering of runs. This is the main open gap of this sprint; the other eight runs were not scored on test.

## 3. Exploitability (test, 176 gold items corrupted offline)

Mean composite reward by corruption (gold = 0.725 for B1, 0.728 for B2). Nothing scored at or above gold on either design.

| kind | B1 composite | B2 composite | what moved |
|---|---|---|---|
| swap (incident_type changed) | 0.545 | 0.592 | B1 incident_type 0.752 to 0.030 (sharp drop); B2 0.746 to 0.284 (drop, less sharp) |
| hedge (3 enum fields to `unknown`) | 0.395 | 0.497 | B1 drops all three (severity 0.677 to 0.217); B2 keeps severity at 0.515 vs 0.660 for gold |
| copy_road (road = first capitalized span) | 0.621 | 0.557 | road 0.795 to 0.377 (B1), 0.888 to 0.253 (B2); both drop. B1's gold road mean includes the 28 gold-null-road items scored 0, so the absolute B1/B2 road levels and the claim that one punishes echo harder are not comparable and are not made |
| fluent_wrong (3 enum fields cyclically changed) | 0.252 | 0.463 | B1 collapses to 0.03 to 0.10 per field; B2 stays at 0.27 to 0.42 |

Readings, with the caveats that apply:

- Both rewards are field-local: corrupting one field leaves the others at roughly gold level, as intended.
- In this offline probe, B2 retains more of gold's reward under hedge and fluent_wrong. A hedge keeps B2 at 68% of gold composite versus 54% for B1; fluent_wrong keeps B2 at 64% versus 35% for B1. B2's severity score for the wrong or `unknown` value (0.42 to 0.52) is a sizeable fraction of its gold-value score, so a policy could earn partial reward for hedging under B2; B2's wrong-value scores are generally higher, i.e. it is more lenient. This rests on mean composites from one probe, with no CIs or per-item spread. It is a lean offline probe, not an adversarial search; an RL policy could find other routes.
- B1 is hard to exploit by hedging because the reward is the probability Jev assigns to the candidate label, and `unknown` is rarely Jev's answer. The flip side is that B1 would punish a model for answering `unknown` when gold says `unknown` but Jev disagrees (section 4).
- `fluent_wrong` is a mechanical cyclic label change, not a fluent wrong answer in a natural sense; `copy_road` is a weak echo probe. Some corruptions can be no-ops (for example when the gold value already is `unknown`, hedge changes nothing for that field), which dilutes the gap for both designs equally in that case.

## 4. Label audit (test, gemma3-1b-lora-n207 outputs, B1 probabilities)

Criterion: B1 probability of the gold value below 0.1 while the candidate equals gold (Jev confidently disagrees with the gold label): 17 field cases. Reverse: candidate differs from gold, and Jev gives the candidate at least 0.9 while gold is under 0.1: 10 cases. Road: 1 case. Selected cases, read against the report text:

| id | field | gold | Jev | read |
|---|---|---|---|---|
| te-060 | road | SLEX | report says Marcos Highway (p 0.01 for SLEX) | **label noise**: gold road contradicts the text |
| te-132 | road_obstruction | none | unknown (p 0.00 for none) | likely label noise: vendors occupying the road, slow flow, `none` is hard to defend |
| te-025 | road_obstruction | unknown | full (p 1.00 for model's `full`) | contradictory report ("minor" but fully closed); gold `unknown` is a convention, Jev picks a side; not clearly an error either way |
| te-172 | severity / obstruction | unknown / unknown | medium / partial (0.99) | same: contradictory-tag items; gold abstains by convention, Jev commits |
| te-175 | severity | unknown | low (0.97) | contradictory-tag; Jev reads "minor" |
| te-147 | incident_type | unknown | heavy_traffic (0.97) | ambiguous-tag ("grabe ang daming tao sa Taft"); Jev's guess is plausible, gold abstention defensible |
| te-092 | road_obstruction | full | partial (p 0.01 for full) | report closes southbound only, northbound open; gold arguable, Jev's reading defensible |
| te-087 | severity | high | medium (p 0.08 for high) | one lane open: severity is a judgment call |
| te-062 | incident_type | road_hazard | road_closure (p 0.00) | **Jev error**: "May butas na kalsada" (pothole) is a hazard |
| te-088 | incident_type | flooding | heavy_traffic (p 0.03) | **Jev error** on noisy slang "baha d2" |

Pattern: most confident disagreements (4 of the 10 selected rows: te-025, te-172, te-175, te-147; across all 23 items with a disagreement in the A or B lists, 12 carry a `contradictory`/`ambiguous`/`noisy` tag, e.g. te-135, te-150, te-170, te-174; te-088 is tagged `noisy` and its gold incident is flooding, so it is a Jev error, not a convention clash) are on tagged items where gold is `unknown` and Jev commits to a concrete label. That is a labelling-convention clash, not a verdict that either side is wrong. Only te-060 is a clear gold label error among those I read; te-132 is suggestive. This is a judgment from reading the text, not a verified audit, and I did not check the other disagreements. The counts (17 cases where the candidate equals gold but B1 gives gold under 0.1, 10 in the reverse direction, 1 road case) come from `jev_rl/scripts/label_audit.py`, output in `jev_rl/results/label_audit_test.md` (the script reads the gitignored cache and makes no API calls). Take it as a pointer list for relabelling review, not a measure of the gold noise rate.

## 5. B1 versus B2, and where each breaks

- Agreement: B1 has higher AUROC on all three enum fields, but only severity is clearly separated; road favours B2 (0.885 vs 0.809), and part of that gap is the null-road rule (non-null predicted road, n=145: B1 0.851, B2 0.891).
- B1 breaks on abstention: gold `unknown` is frequently scored near 0 by Jev (contradictory/ambiguous items), and noisy slang or terse reports can get confident wrong classifications. Because Jev only classifies, B1's signal is classification accuracy of Jev on the report, not verification of the candidate; B1 would also reward a model only up to Jev's own accuracy.
- B2 breaks on discrimination and exploitability: lower AUROC on enum fields, and wrong or hedged candidates keep substantial reward (fluent_wrong 64% of gold composite, hedge 68%). B2's higher mean composite (0.632 versus 0.564) with lower AUROC says it is more lenient, not more accurate.
- Road: both work reasonably; B1 needs one extra call per distinct candidate road, and a null predicted road gets 0.0 with no call, which makes B1 look worse on road than a like-for-like comparison would (see section 1).

## 6. Validation versus test

Validation (40 items, 4 runs) and test (176 items, 1 run) agree on the main directions: B1 above B2 on incident_type and severity, B2 above B1 on road (partly the null-road artifact; validation road also used the same rule), no corruption beating gold. Differences: on validation the B2 AUROC for the same gemma LoRA run was 0.509 for incident_type and 0.746 for severity; on test it is 0.872 and 0.713. The validation CIs were wide (for example [0.31, 0.71]) because n was 40, so the validation incident_type number is likely small-n noise (not tested) rather than evidence of a different regime. Validation B1 AUROCs for this run (0.887, 0.906, 0.894, 0.813) are within about 0.06 of test (0.949, 0.878, 0.896, 0.809). On validation, road_obstruction B1 and B2 were tied (0.894 versus 0.891); on test B1 is ahead (0.896 versus 0.790). Exploit magnitudes are similar on both splits (validation: B2 hedge 0.468/0.710 = 66% of gold composite vs B1 0.376/0.731 = 51%; test 68% vs 54%). The validation results do not contradict the test results, but the validation sample is too small for B1 versus B2 gaps on individual fields to be trusted from it alone.

## Limits

- Process disclosures: (a) a stray nine-run analyze invocation was stopped by hand before it logged or wrote a report; its API calls stayed in the cache and were reused. Scoring reads per-run predictions and only gemma3-1b-lora-n207 is in test_runs.log, so scoring was not affected. (b) exploit.py's default --limit is 40, so the test exploit run used --limit 176; it was relaunched several times after connection resets and timeouts (only uncached calls were re-sent). (c) Spend is an estimate (about $0.10 from list price, about 1600 new calls), not read from the provider.
- n: 176 test items, synthetic text, single author, one seed, one scored run. The test items come from the same author as the training data.
- Unparseable outputs get reward 0 and match False by construction. For this run only 2 of 176 are unparseable, so pooled and parseable-only figures nearly coincide; for weaker runs (e.g. validation zero-shot, 27 of 40 unparseable) pooled AUROC is inflated by this trivial separation and is not comparable across runs. The headline is therefore parseable-only.
- A null predicted road gets road reward 0.0 with no Jev call; a missing label key gets 0.0. These are conventions, and they penalise legitimately null roads (gold road null, candidate null) relative to a gold match.
- Jev probabilities are rounded to 2 decimals, creating ties and limiting resolution.
- `fluent_wrong` is a mechanical cyclic change and `copy_road` a weak echo probe; some corruptions can be no-ops. The exploit suite is a small offline probe, not an adversarial search.
- B1 uses Jev as a classifier; its signal is classification accuracy, not verification of the candidate.
- This sprint measures reward quality only. No RL was run, so nothing here shows that training with a Jev reward improves a model, nor that it would be stable under optimisation pressure.
- The ranking question is unanswered on test, since one run was scored. Question wording was fixed after validation and not revised; this is a protocol note, not a claim of extensive tuning.
- The design listed a calibration analysis, an approach-A (whole-JSON) baseline and non-mean aggregations (min or thresholded); none were done. Only mean composite is reported.
- Test reruns are refused by design, so the committed `test_agreement.md` still carries the "only 4 runs" caution line that analyze.py now prints only when there are 4 runs or fewer; it is stale for this one-run report. The analyze guard writes `test_runs.log` only after scoring finishes. exploit.py checks `--final` but writes no log, because it scores corrupted gold labels, not model outputs.
- The label audit is a manual reading of selected items, not an estimate of label noise.
