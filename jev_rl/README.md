# jev_rl

Mini research sprint: how closely can a Jev-based reward reproduce gold-label supervision on SFT data, and where does
it break? Jev is `typesafe/jev-1.14` (OpenRouter `/api/alpha/decisions`). The traffic-report data in the parent repo is
the case study. Results and limits: `docs/findings.md`.

- `docs/design.md`: research question, approaches, plan (historical; approach B was chosen).
- `docs/findings.md`: findings and limits.
- `scripts/`: `jev_client.py` (cached client), `questions.py`, `reward.py`, `analyze.py`, `exploit.py`, `label_audit.py`.
- `results/`: markdown outputs, `test_runs.log`, `cost_estimate.md`. The API response cache is `results/cache/`, which is
  git-ignored and not in the repo.

Read-only inputs from the parent repo: `data/processed/*.jsonl`, `experiments/*/predictions*.jsonl`. Nothing outside
`jev_rl/` is modified by this work. The API key is read from `OPENROUTER_API_KEY` in `.env`.

## Commands (from the repo root)

    uv run --with pytest --with python-dotenv --with requests pytest jev_rl/tests -q
    uv run --with python-dotenv --with requests python jev_rl/scripts/analyze.py --split validation --runs gemma3-1b-zeroshot,gemma3-1b-fewshot,gemma3-1b-lora-n207,qwen2.5-1.5b-lora-n207
    uv run --with python-dotenv --with requests python jev_rl/scripts/exploit.py --split validation
    uv run --with python-dotenv --with requests python jev_rl/scripts/analyze.py --split test --final --runs <run>
    uv run --with python-dotenv --with requests python jev_rl/scripts/exploit.py --split test --final --limit 176

The default `--limit` of exploit.py is 40, so the test run needs `--limit 176`. A test rerun of an already logged run is
refused by design (`results/test_runs.log`). Without the cache, a rerun costs API calls and may not reproduce the same
answers.
