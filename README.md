# trafficslm

Study of whether a small language model (Gemma 3 1B, Qwen2.5 1.5B), fine-tuned with LoRA, can extract structured
information (incident type, location, severity, road obstruction, language) from synthetic Filipino, English and
Taglish traffic reports, compared with zero-shot and few-shot prompting of the same models. Runs locally with MLX on
Apple silicon. One seed, synthetic data; see `research/findings.md` for results and limits.

## Setup

```
uv sync
uv run pytest -q
```

Models are downloaded from Hugging Face on first use (nothing is bundled). Model ids are in
`experiments/models.json`:

| key | Hugging Face id |
|---|---|
| gemma3-1b | `mlx-community/gemma-3-1b-it-bf16` |
| qwen2.5-1.5b | `mlx-community/Qwen2.5-1.5B-Instruct-bf16` |
| gemma3-1b-4bit | `mlx-community/gemma-3-1b-it-4bit` |

The revisions are not pinned, so a re-download may fetch a newer snapshot of a model repository.

## Data

`data/processed/{train,validation,test}.jsonl` (207 / 40 / 176 items, all synthetic) with sha256 checksums and class
counts in `data/processed/MANIFEST.json`. `trafficslm.data.verify_manifest()` checks them, and the test-split
path calls it. `data/aliases.json` is the road-name alias list used when scoring locations. Label rules are in
`docs/annotation-guidelines.md`; `data/annotations/` holds the annotation batch files.

## Reproduction order

All commands run from the repo root. Runs are written to `experiments/<run>/`.

1. Zero-shot and few-shot baselines on validation (merges model ids into `experiments/models.json`):
   `uv run python scripts/run_baselines.py`
2. LoRA runs, per run name in `scripts/run_lora.py` (`gemma3-1b-lora-n50`, `gemma3-1b-lora-n100`,
   `gemma3-1b-lora-n207`, `qwen2.5-1.5b-lora-n207`, `gemma3-1b-4bit-lora-n207`):
   `uv run python scripts/run_lora.py train <run>` then `uv run python scripts/run_lora.py eval <run>`;
   `uv run python scripts/run_lora.py table` writes `experiments/lora_validation.md`.
3. Model selection on validation only: `research/selection.md` (written before any test run).
4. Test predictions for the nine declared runs, one process each:
   `uv run python scripts/run_test.py all` (or `one <run>`).
5. Score each run on the test split, once, through the guard:
   `uv run python -m trafficslm.evaluate --run experiments/<run> --split test --final`
6. Reports and tables (read stored files only, no model is loaded):
   - `uv run python scripts/make_reports.py` regenerates `results/summary*.md|png` and `results/errors_<run>.md`.
   - `uv run python scripts/make_findings_tables.py [table ...]` prints the tables used in `research/findings.md`.
   - Post-hoc analyses (computed after scoring, not used for any selection):
     `uv run python scripts/alias_sensitivity.py`, `scripts/posthoc_metrics.py`, `scripts/check_leakage.py`
     (write `results/alias_sensitivity_test.md`, `results/posthoc_metrics_test.md`, `results/leakage_check.md`).

`scripts/smoke_infer.py OUT_DIR [model_id] [--few]` is a 3-item smoke check.

## Committed and ignored

Committed: code, data, predictions (`predictions*.jsonl`), `results*.json`, `meta*.json`, tables and write-ups.
Not committed (git-ignored): LoRA adapters (`experiments/*/adapters/`, about 15 MB per weights file, 31 MB per run
folder), `experiments/*/mlx_data/`, `experiments/*/train.log`. Retraining is needed to recreate adapters, and the
test-time inference scripts need them for the LoRA runs.

## Freeze rule and test guard

After `research/selection.md` was committed, no model, prompt, adapter or hyperparameter was changed. The test split
is scored once per declared run: `trafficslm.evaluate` refuses `--split test` without `--final`, and refuses a run
already listed in `experiments/test_runs.log`. Do not edit `data/processed/*`, `data/aliases.json`, stored
predictions, `results*.json` or `meta*.json`; post-hoc analyses go to new files under `results/`.

## Where to read more

- `research/findings.md`: results, limitations, next steps.
- `research/selection.md`: validation-based selection and the declared test plan.
- `docs/annotation-guidelines.md`: label definitions.
- `docs/superpowers/specs/2026-11-10-filipino-traffic-slm-design.md` and `docs/superpowers/plans/`: design and plan.
