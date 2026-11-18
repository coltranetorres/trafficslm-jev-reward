"""Cached client for Jev (typesafe/jev-1.14) via OpenRouter's decisions endpoint.

Request:  POST {"model", "state": [str, ...], "questions": {name: {...}}}
Response: {"answers": {name: answer}}. Answer shapes (verified live, see
jev_rl/results/shape_check.json): noul -> {"type": "noul", "noul": float};
choice -> {"choice": label, "probabilities": {label: float}}.

The API key is read from OPENROUTER_API_KEY and is never part of the cache key.
"""
import hashlib
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

URL = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "typesafe/jev-1.14"
MAX_ATTEMPTS = 4


def cache_key(model: str, state: list, questions: dict) -> str:
    blob = json.dumps({"model": model, "state": state, "questions": questions},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def query_jev(state: list, questions: dict, cache_dir: Path, model: str = DEFAULT_MODEL) -> dict:
    cache_dir = Path(cache_dir)
    path = cache_dir / f"{cache_key(model, state, questions)}.json"
    if path.exists():
        return json.loads(path.read_text())

    load_dotenv()
    headers = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
               "Content-Type": "application/json"}
    payload = {"model": model, "state": state, "questions": questions}
    for attempt in range(MAX_ATTEMPTS):
        r = requests.post(URL, headers=headers, json=payload, timeout=60)
        if r.status_code == 429 or r.status_code >= 500:
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(2 ** attempt)
                continue
        r.raise_for_status()
        answers = r.json()["answers"]
        cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(answers, ensure_ascii=False))
        return answers
