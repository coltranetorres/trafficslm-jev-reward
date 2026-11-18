"""Dataset loading."""
from __future__ import annotations

from pathlib import Path

from .schema import Record

__all__ = ["load_split"]

DEFAULT_ROOT = Path("data/processed")


def load_split(name: str, root: Path = DEFAULT_ROOT) -> list[Record]:
    with open(Path(root) / f"{name}.jsonl", encoding="utf-8") as f:
        return [Record.model_validate_json(line) for line in f if line.strip()]
