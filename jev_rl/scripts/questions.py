"""Jev question definitions for field prediction (B1) and verification (B2)."""
from __future__ import annotations

from trafficslm.schema import INCIDENT_TYPES, OBSTRUCTIONS, SEVERITIES

FIELDS = ("incident_type", "severity", "road_obstruction", "road")

_INCIDENT_DESC = {
    "vehicle_breakdown": "Stalled, broken-down, flat-tire, or overheated vehicle.",
    "road_accident": "Collision, crash, or a vehicle hitting a person or object.",
    "road_hazard": "Debris, fallen tree/post/cables, potholes, open manhole, or spills.",
    "flooding": "Flooded road, of any depth.",
    "road_closure": "Road or lane closed on purpose or by works, events, rallies, or repairs.",
    "heavy_traffic": "Congestion with no confirmed cause.",
    "other": "A clear cause not listed (broken traffic light, checkpoint, convoy, brownout).",
    "unknown": "Not enough information to tell.",
}
_SEVERITY_DESC = {
    "high": "Road impassable or fully blocked, injuries reported, standstill, or a delay of about 1 hour or more.",
    "medium": "Partial obstruction, slow-moving or heavy traffic, or a moderate delay.",
    "low": "Reported as minor, no obstruction, or already cleared or moved aside.",
    "unknown": "The report says nothing about impact.",
}
_OBSTRUCTION_DESC = {
    "full": "All lanes or the whole road blocked or impassable.",
    "partial": "Some lanes blocked, or open to some vehicles only.",
    "none": "Stated or clearly implied that nothing blocks the road (pure congestion, vehicle moved aside).",
    "unknown": "Not stated; 'nakaharang' or 'sa gitna' alone is unknown.",
}

for _labels, _desc in ((INCIDENT_TYPES, _INCIDENT_DESC), (SEVERITIES, _SEVERITY_DESC),
                       (OBSTRUCTIONS, _OBSTRUCTION_DESC)):
    assert set(_labels) == set(_desc)


def state_for(text: str) -> list:
    return [f"Traffic report: {text}"]


def field_questions() -> dict:
    """B1: one choice question per categorical field."""
    return {
        "incident_type": {
            "type": "choice",
            "instructions": "Pick the incident type the traffic report states. If it names both a cause and traffic, choose the cause. Use unknown if the report does not say.",
            "criteria": dict(_INCIDENT_DESC),
        },
        "severity": {
            "type": "choice",
            "instructions": "Pick the severity based only on the impact the report states. An accident is not automatically high.",
            "criteria": dict(_SEVERITY_DESC),
        },
        "road_obstruction": {
            "type": "choice",
            "instructions": "Pick how much of the road is obstructed, based only on what the report states.",
            "criteria": dict(_OBSTRUCTION_DESC),
        },
    }


def road_question(road: str) -> dict:
    """B1: noul question asking whether the report is about the given road."""
    return {
        "road_match": {
            "type": "noul",
            "instructions": f"Does the traffic report say the incident is on {road}? Aliases and spellings of the road name count.",
            "criteria": {
                "true": f"The report names {road} (or an alias or spelling of it) as the road of the incident.",
                "false": f"The report names a different road, or does not name {road}.",
            },
        }
    }


def choice_probs(answers: dict, field: str) -> dict[str, float]:
    return {k: float(v) for k, v in answers[field]["probabilities"].items()}


def _verify(field: str, what: str) -> dict:
    return {
        "type": "noul",
        "instructions": f"The state contains a traffic report and a candidate JSON extraction. Judge whether the candidate's {what} is correct for the report. Label only what the report says; do not assume.",
        "criteria": {
            "true": f"The candidate's {field} is correct given the report.",
            "false": f"The candidate's {field} is wrong given the report.",
        },
    }


def verify_questions() -> dict:
    """B2: one noul question per field, judging a candidate extraction."""
    return {
        "incident_type": _verify("incident_type", "incident_type"),
        "severity": _verify("severity", "severity (based on reported impact only)"),
        "road_obstruction": _verify("road_obstruction", "road_obstruction"),
        "road": _verify("road", "location.road (canonical road name, null if not stated)"),
    }


def state_for_verify(text: str, raw: str) -> list:
    return [f"Traffic report: {text}", f"Candidate JSON: {raw}"]
