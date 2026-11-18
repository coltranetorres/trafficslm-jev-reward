"""Per-field Jev reward (B1 classifier-style, B2 verifier-style) and gold matching."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from jev_client import query_jev
from questions import (FIELDS, choice_probs, field_questions, road_question,
                       state_for, state_for_verify, verify_questions)
from trafficslm.metrics import normalize
from trafficslm.schema import Record, Report, parse_report

__all__ = ["FIELDS", "reward_for", "gold_match"]

_ENUM_FIELDS = ("incident_type", "severity", "road_obstruction")


def _finish(r: dict[str, float]) -> dict[str, float]:
    r["composite"] = sum(r[f] for f in FIELDS) / len(FIELDS)
    return r


def reward_for(rec_text: str, raw: str, cache_dir: Path,
               design: Literal["b1", "b2"]) -> dict[str, float]:
    report = parse_report(raw)
    if report is None:
        return _finish({f: 0.0 for f in FIELDS})
    if design == "b2":
        ans = query_jev(state_for_verify(rec_text, raw), verify_questions(), cache_dir)
        return _finish({f: float(ans[f]["noul"]) for f in FIELDS})
    if design != "b1":
        raise ValueError(f"unknown design {design!r}")
    ans = query_jev(state_for(rec_text), field_questions(), cache_dir)
    out = {f: choice_probs(ans, f).get(getattr(report, f), 0.0) for f in _ENUM_FIELDS}
    road = report.location.road
    if road is None:
        out["road"] = 0.0
    else:
        rans = query_jev(state_for(rec_text), road_question(road), cache_dir)
        out["road"] = float(rans["road_match"]["noul"])
    return _finish({f: out[f] for f in FIELDS})


def gold_match(gold: Record, report: Report | None) -> dict[str, bool]:
    if report is None:
        return {f: False for f in FIELDS}
    m = {f: getattr(gold, f) == getattr(report, f) for f in _ENUM_FIELDS}
    m["road"] = normalize(gold.location.road) == normalize(report.location.road)
    return {f: m[f] for f in FIELDS}
