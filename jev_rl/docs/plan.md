# Jev Reward Sprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure how well per-field Jev probabilities reproduce gold-label correctness on the traffic extraction runs, and where that reward can be exploited.

**Architecture:** Two reward designs are compared on the same runs. **B1 (classifier-style):** Jev classifies each field from the report alone (`choice` over the label set); the reward is the probability Jev gives to the candidate's value, so one cached call per item scores every run and corruption; road uses one `noul` call per (item, candidate road). **B2 (verifier-style):** Jev sees the report and the candidate JSON and answers one `noul` per field ("is this field correct?"); one call per (item, candidate). Everything is cached on disk. Both designs share one reward interface so the analysis code is identical.

**Tech Stack:** Python 3.12, `requests`, `python-dotenv`, pytest, existing `trafficslm` package (read-only).

**Spec:** `jev_rl/docs/design.md` (approach B, lean scope).

## Global Constraints

- Nothing outside `jev_rl/` is modified (no edits to `data/`, `experiments/`, `results/`, `src/`, `pyproject.toml`).
- Model id `typesafe/jev-1.14`; endpoint `https://openrouter.ai/api/alpha/decisions`; key from `OPENROUTER_API_KEY` via `load_dotenv()`.
- Never print or log the API key; cache keys must not include it.
- Question wording is developed on **validation only**, then frozen; test is scored once, behind a `--final` guard and a `jev_rl/results/test_runs.log` check (same pattern as `trafficslm.evaluate`).
- Run commands from repo root; extra deps via `uv run --with python-dotenv --with requests`.
- Lean scope: no approach C, no second dataset; point estimates plus bootstrap CI.

## Review Focus

- Unparseable or `None` predicted report: reward 0 for every field, never an exception.
- API errors (429, 5xx, timeout): retried with backoff, then raised; a failed call must never be cached.
- Predicted road or gold road is `null`: road reward and road match are defined (null/null counts as a match; null vs value does not).
- AUROC with a single class present (all correct or all wrong) or tied scores: returns `None` or handles ties, no crash.
- Test split run twice: second run refuses.

---

### Task 1: Cached Jev client

**Files:**
- Create: `jev_rl/scripts/jev_client.py`
- Test: `jev_rl/tests/test_jev_client.py`

**Interfaces:**
- Produces: `query_jev(state: list, questions: dict, cache_dir: Path, model: str = "typesafe/jev-1.14") -> dict` returning the response's `answers` dict. `cache_key(model, state, questions) -> str` (sha256 of canonical JSON).

- [ ] **Step 1: Write failing tests** in `test_jev_client.py`, patching `jev_client.requests.post`:
  `test_cache_hit_skips_network` (second identical call makes 1 total post), `test_error_not_cached` (500 then 200 returns answers and writes exactly one cache file), `test_retries_on_429` (two 429s then 200 succeeds, sleep patched), `test_key_not_in_cache_key` (cache key identical regardless of env key).
- [ ] **Step 2:** Run `uv run --with python-dotenv --with requests --with pytest pytest jev_rl/tests/test_jev_client.py -q`; expect FAIL (module missing).
- [ ] **Step 3: Implement** `query_jev` and `cache_key` in `jev_client.py`: `load_dotenv()` at import of the key lookup, `requests.post` with 60 s timeout, up to 4 attempts on 429/5xx with exponential backoff, `raise_for_status` otherwise, cache JSON written only on 200.
- [ ] **Step 4:** Re-run the tests; expect PASS.
- [ ] **Step 5: Live shape check (one real call, validation item `va-001` or the first validation id).** Save the raw `answers` to `jev_rl/results/shape_check.json` and confirm that a `choice` answer has `choice` and `probabilities` (label to float). If the shape differs, fix `jev_client` docs and Task 2's parsing before continuing.
- [ ] **Step 6: Commit** `git add jev_rl/scripts/jev_client.py jev_rl/tests/test_jev_client.py && git commit -m "feat(jev_rl): cached Jev client"`

### Task 2: Field questions

**Files:**
- Create: `jev_rl/scripts/questions.py`
- Test: `jev_rl/tests/test_questions.py`

**Interfaces:**
- Consumes: `trafficslm.schema.INCIDENT_TYPES, SEVERITIES, OBSTRUCTIONS`.
- Produces: B1: `field_questions() -> dict` with keys `incident_type`, `severity`, `road_obstruction`, each `{"type": "choice", "instructions": str, "criteria": {label: description}}` covering exactly the schema label sets. `road_question(road: str) -> dict` returning `{"road_match": {"type": "noul", ...}}`. `choice_probs(answers: dict, field: str) -> dict[str, float]`. B2: `verify_questions() -> dict` with one `noul` per field in `FIELDS` (keys `incident_type`, `severity`, `road_obstruction`, `road`), and `state_for_verify(text: str, raw: str) -> list` (report plus candidate JSON).

- [ ] **Step 1: Write failing tests:** `test_criteria_match_label_sets` (criteria keys equal the three schema tuples), `test_road_question_mentions_road`, `test_choice_probs_reads_probabilities` (fed a fake answers dict from the Task 1 shape), `test_verify_questions_cover_all_fields`, `test_verify_state_contains_candidate`.
- [ ] **Step 2:** Run; expect FAIL.
- [ ] **Step 3: Implement.** Label descriptions come from `docs/annotation-guidelines.md` definitions, shortened to one line each. State is `["Traffic report: <text>"]`; provide `state_for(text: str) -> list`.
- [ ] **Step 4:** Run; expect PASS.
- [ ] **Step 5: Commit** `feat(jev_rl): field questions`

### Task 3: Per-field reward

**Files:**
- Create: `jev_rl/scripts/reward.py`
- Test: `jev_rl/tests/test_reward.py`

**Interfaces:**
- Consumes: `query_jev`, `field_questions`, `road_question`, `choice_probs`, `trafficslm.schema.parse_report`, `trafficslm.metrics.normalize`.
- Produces: `FIELDS = ("incident_type", "severity", "road_obstruction", "road")`. `reward_for(rec_text: str, raw: str, cache_dir: Path, design: Literal["b1", "b2"]) -> dict[str, float]` returning per-field Jev probability plus `"composite"` (mean of the four); `design="b1"` is classifier-style, `"b2"` verifier-style (one call with `verify_questions`; unparseable candidate still gives 0 without a call). `gold_match(gold: Record, report: Report | None) -> dict[str, bool]` per field, using `normalize` with the alias file for road.

- [ ] **Step 1: Write failing tests** with `query_jev` patched: `test_b2_reward_is_noul_per_field`, `test_unparseable_prediction_gives_zero_rewards` (both designs), `test_reward_is_prob_of_predicted_label` (fake probs, predicted `flooding` gets its probability), `test_null_road_pair_matches` and `test_null_vs_value_no_match` for `gold_match`.
- [ ] **Step 2:** Run; expect FAIL.
- [ ] **Step 3: Implement.** One shared `choice` call per item (all three questions in one request); road uses `road_question(pred_road)` with the `noul` probability. A null predicted road gets road reward 0.0 (no extra Jev call); record this convention in the findings limits.
- [ ] **Step 4:** Run; expect PASS.
- [ ] **Step 5: Commit** `feat(jev_rl): per-field reward and gold match`

### Task 4: Analysis (agreement and ranking)

**Files:**
- Create: `jev_rl/scripts/analyze.py`
- Test: `jev_rl/tests/test_analyze.py`

**Interfaces:**
- Consumes: `reward_for`, `gold_match`, `trafficslm.data.load_split`, `trafficslm.metrics.bootstrap_ci`.
- Produces: `auroc(scores: list[float], labels: list[bool]) -> float | None` (rank-based, ties averaged, `None` if one class). `score_run(run_dir: Path, split: str, cache_dir: Path) -> list[dict]` (per item: per-field reward and match). `score_run` takes `design`. CLI: `uv run --with python-dotenv --with requests python jev_rl/scripts/analyze.py --split validation --runs a,b,c` writes `jev_rl/results/<split>_agreement.md` with B1 and B2 side by side (per-field AUROC with bootstrap CI, per-run mean composite reward next to gold per-field accuracy, and a rank-order comparison). `--split test` requires `--final` and refuses if `jev_rl/results/test_runs.log` already has the run.

- [ ] **Step 1: Write failing tests:** `test_auroc_perfect`, `test_auroc_ties_half`, `test_auroc_single_class_none`, `test_test_split_requires_final`, `test_test_split_refuses_repeat` (tmp log).
- [ ] **Step 2:** Run; expect FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4:** Run; expect PASS.
- [ ] **Step 5: Validation run** on `gemma3-1b-zeroshot,gemma3-1b-fewshot,gemma3-1b-lora-n207,qwen2.5-1.5b-lora-n207` (all 40 items; uses `predictions.jsonl`). Read the report. If AUROC is poor, iterate question wording in `questions.py` here (validation only), then freeze by committing with message `freeze: jev question wording`.
- [ ] **Step 6: Commit** `feat(jev_rl): agreement and ranking analysis`

### Task 5: Exploit suite

**Files:**
- Create: `jev_rl/scripts/exploit.py`
- Test: `jev_rl/tests/test_exploit.py`

**Interfaces:**
- Consumes: `reward_for`, `load_split`.
- Produces: `corrupt(gold: Record, kind: str) -> str` returning a raw JSON string, for `kind` in `"gold"`, `"swap"` (wrong incident_type), `"hedge"` (all enum fields `unknown`), `"copy_road"` (road set to the first capitalized span of the text, wrong or right as it happens), `"fluent_wrong"` (a plausible but different label set). CLI writes `jev_rl/results/exploit_<split>.md` with mean composite reward per kind for B1 and B2 (expect B1 to ignore hedging and echo, since it never sees the candidate; B2 is where they can bite); a good reward ranks `gold` highest and every corruption lower.

- [ ] **Step 1: Write failing tests:** `test_gold_roundtrips_through_parse_report`, `test_swap_changes_incident_type`, `test_hedge_sets_unknown`.
- [ ] **Step 2:** Run; expect FAIL.
- [ ] **Step 3: Implement** and run on validation. Note any corruption that scores at or above gold.
- [ ] **Step 4:** Run tests; expect PASS.
- [ ] **Step 5: Commit** `feat(jev_rl): exploit suite`

### Task 6: Test pass and findings

**Files:**
- Create: `jev_rl/docs/findings.md`
- Output: `jev_rl/results/test_agreement.md`, `jev_rl/results/exploit_test.md`

- [ ] **Step 1:** Check Jev's OpenRouter price per call; estimate cost of 176 items x runs (cached road calls included) and tell Cole before running.
- [ ] **Step 2:** Run `analyze.py --split test --final --runs <declared runs>` once; run the exploit suite on test.
- [ ] **Step 3:** Write `findings.md`: answer the research question (agreement, ranking, exploitability, label-audit list of confident disagreements), then limits (small n, synthetic, one seed, null-road convention, Jev used as classifier not verifier of the candidate).
- [ ] **Step 4: Commit** `docs(jev_rl): findings`

---

## Self-review notes

- Both reward designs (B1, B2) flow through Tasks 2 to 6; the findings must state which design tracks gold better and which is easier to exploit.
- Spec coverage: agreement (T4), ranking (T4), exploitability (T5), label audit (T6 findings list), freeze rule and test-once (T4, T6), caching and key hygiene (T1).
- Task 3's road-null line is a decision, not a placeholder: null predicted road gives reward 0.0, documented as a limit.
- The shape of `choice` answers is assumed from the pasted example and is verified live in Task 1 step 5 before later tasks depend on it.
