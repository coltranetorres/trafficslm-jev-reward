"""Road-name normalization and bootstrap CI (pure stdlib)."""
from __future__ import annotations

import json
import random
import re
import unicodedata
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

ALIASES_PATH = Path(__file__).resolve().parents[2] / "data" / "aliases.json"
NAN = float("nan")
_ABBREV = {"ave": "avenue", "blvd": "boulevard", "hwy": "highway", "hway": "highway"}


def _base(s: str | None) -> str | None:
    if s is None:
        return None
    s = unicodedata.normalize("NFKD", s.strip().lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    if s in ("", "null"):
        return None
    s = s.replace(".", " ").replace(",", " ")
    toks = [_ABBREV.get(t, t) for t in s.split()]
    return " ".join(toks) or None


@lru_cache(maxsize=None)
def load_aliases(path: str | None = None) -> dict[str, str]:
    """Map normalized alias (and canonical) -> normalized canonical road."""
    p = Path(path) if path else ALIASES_PATH
    raw = json.loads(p.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for canon, aliases in raw.items():
        c = _base(canon)
        out[c] = c
        for a in aliases:
            out[_base(a)] = c
    return out


def normalize(s: str | None, aliases_path: str | None = None) -> str | None:
    b = _base(s)
    if b is None:
        return None
    return load_aliases(aliases_path).get(b, b)


def bootstrap_ci(metric_on_indices: Callable[[list[int]], float], n_items: int,
                 n_boot: int = 1000, seed: int = 0) -> tuple[float, float]:
    if n_items <= 0:
        return (NAN, NAN)
    rng = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        v = metric_on_indices([rng.randrange(n_items) for _ in range(n_items)])
        if v == v:
            vals.append(v)
    if not vals:
        return (NAN, NAN)
    vals.sort()
    n = len(vals)
    return (vals[min(n - 1, int(0.025 * n))], vals[min(n - 1, int(0.975 * n))])
