from trafficslm.schema import INCIDENT_TYPES, OBSTRUCTIONS, SEVERITIES

import questions as q


def test_criteria_match_label_sets():
    fq = q.field_questions()
    assert set(fq) == {"incident_type", "severity", "road_obstruction"}
    assert set(fq["incident_type"]["criteria"]) == set(INCIDENT_TYPES)
    assert set(fq["severity"]["criteria"]) == set(SEVERITIES)
    assert set(fq["road_obstruction"]["criteria"]) == set(OBSTRUCTIONS)
    for spec in fq.values():
        assert spec["type"] == "choice" and spec["instructions"]


def test_road_question_mentions_road():
    rq = q.road_question("EDSA")
    assert set(rq) == {"road_match"}
    assert rq["road_match"]["type"] == "noul"
    assert "EDSA" in str(rq["road_match"])


def test_choice_probs_reads_probabilities():
    answers = {"severity": {"type": "choice", "choice": "high",
                            "probabilities": {"high": 0.7, "low": 0.3},
                            "confidence": 0.7}}
    assert q.choice_probs(answers, "severity") == {"high": 0.7, "low": 0.3}


def test_verify_questions_cover_all_fields():
    vq = q.verify_questions()
    assert set(vq) == set(q.FIELDS)
    for spec in vq.values():
        assert spec["type"] == "noul"
        assert spec["instructions"]
        assert set(spec["criteria"]) == {"true", "false"}


def test_verify_state_contains_candidate():
    state = q.state_for_verify("Stalled jeep sa EDSA", '{"severity": "low"}')
    joined = " ".join(state)
    assert "Stalled jeep sa EDSA" in joined and '{"severity": "low"}' in joined
    assert q.state_for("hi") == ["Traffic report: hi"]
