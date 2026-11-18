> Historical note: this is the design as approved before the work. Approach B was chosen; names in the plan differ from what was built (for example `jev_reward.py` became `reward.py`, `analyze.py` and `exploit.py`). Not rewritten; see `findings.md` for what was actually done.

# Jev as a reward: mini research sprint (design)

Status: approved 2026-11-18. Approach B chosen. Scope is a lean mini sprint, not a comprehensive study: skip approach C,
skip the optional second dataset, keep the exploit suite to a few corruption types, report point estimates with a
simple bootstrap CI.

## Research question

**How closely can a Jev-based reward reproduce gold-label supervision on SFT data, and where does it break?**

Jev is `typesafe/jev-1.14`, OpenRouter `/api/alpha/decisions`: it answers typed questions (`noul`, `choice`, `score`)
about a state and returns probabilities. "SFT data" means inputs with labeled target outputs. The traffic-report data
in this repo is the case study; the question is meant to be general.

## Why

Cole wants to know if RL with a Jev reward could replace SFT where labels exist (and later where they don't). The
question is empirical (fidelity and failure modes), not a recipe. A tutorial may follow as a byproduct.

## Sub-questions

1. **Agreement.** Does Jev's per-field probability predict whether a field matches gold? (AUROC, calibration, per field.)
2. **Ranking.** Does mean Jev reward order the stored runs (zero-shot, few-shot, LoRA n50/n100/n207, Qwen, 4-bit) the
   same way the gold metrics do?
3. **Exploitability.** Can an output score high while wrong? Tested offline on controlled corruptions of gold outputs
   (swapped label, hedge to `unknown`, copied input span, fluent wrong answer).
4. **Label audit (secondary).** Where Jev and gold disagree confidently, is Jev wrong or is the label noisy?

## Goals / non-goals / anti-goals

- Goals: measure reward fidelity and failure modes; keep protocol clean enough to trust.
- Non-goals: no RL training run; no claim that RL with Jev improves a model; no tutorial in this sprint.
- Anti-goals: tuning question wording on test (contaminates results); reporting only the favorable field or run.

## Data and constraints

- Case study: `data/processed/{validation,test}.jsonl` (40 / 176 items, synthetic, single author) plus stored
  `experiments/*/predictions*.jsonl` from the nine declared runs. No model inference needed.
- Freeze rule applies: do not edit `data/`, stored predictions or `results*.json`. New outputs go under
  `jev_rl/results/` and new scripts under `jev_rl/scripts/`.
- Question wording is developed on **validation only**, then frozen and run once on test.
- Limits to state in the write-up: small n, one seed, synthetic text, label noise acknowledged in the original fine-tuning study (not included in this repo).
- API: key in `.env` via `load_dotenv()`. `.env` is currently untracked and not git-ignored; add it to `.gitignore`
  before any commit. Run with `uv run --with python-dotenv --with requests` unless Cole wants them added to
  `pyproject.toml`. Cache every response to disk so reruns cost nothing. Check Jev pricing before the test run.

## Approaches (my proposal, not yet chosen by Cole)

- **A. One whole-JSON `noul` question.** Cheapest (1 call per item). First probe (6 items) gave 0.09 to 0.23 for
  everything, including correct incident types, so it looks too coarse. Keep only as a baseline.
- **B. Per-field questions (chosen).** Two reward designs, compared head to head on the same runs:
  - **B1, classifier-style:** Jev sees only the report and answers a `choice` question per field (`noul` for road);
    reward = probability Jev gives to the candidate's value. One cached call per item scores every candidate.
  - **B2, verifier-style:** Jev sees the report and the candidate extraction and answers a `noul` per field
    ("is this field correct?"). One call per (item, candidate); makes hedging and echo exploits meaningful.
  Both give per-field AUROC, a composite reward, run ranking and exploit results. The research question's "how" is
  the comparison: how the reward design changes fidelity and failure modes.
- **C. Pairwise or `score` rubric.** Ask Jev to prefer one candidate or grade quality 1 to 3. Closer to how RL
  rewards are often built, but more design freedom and harder to compare with exact match. Defer to a second round.

Decision: B1 and B2 on validation (all 40 items, 3 to 4 runs), freeze wording, then B on test for the declared runs;
A as baseline; C only if B is promising.

## Plan outline

1. Script `jev_rl/scripts/jev_reward.py`: builds questions per field, calls Jev, caches responses.
2. Validation pass: iterate wording, pick aggregation (mean, min, thresholded).
3. Corruption suite for exploitability on validation items.
4. Freeze, then one test pass over the stored runs; compute AUROC, calibration, run ranking vs gold metrics.
5. Write `jev_rl/docs/findings.md` with results, failures and limits.

## Left to the builder

Exact question wording, aggregation choice, bootstrap CIs for AUROC, and the subset of runs for the validation pass.
