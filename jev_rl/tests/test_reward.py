import json
from unittest.mock import patch

import reward
from trafficslm.schema import Location, Record, parse_report

RAW = json.dumps({"incident_type": "flooding", "location": {"road": "EDSA", "landmark": None, "direction": None},
                  "severity": "high", "road_obstruction": "full", "language": "english"})
RAW_NULL_ROAD = json.dumps({"incident_type": "flooding", "location": {"road": None},
                            "severity": "high", "road_obstruction": "full", "language": "english"})


def _choice(probs):
    return {"type": "choice", "choice": max(probs, key=probs.get), "probabilities": probs, "confidence": 0.9}


def test_reward_is_prob_of_predicted_label(tmp_path):
    ans = {"incident_type": _choice({"flooding": 0.7, "road_accident": 0.3}),
           "severity": _choice({"high": 0.6, "low": 0.4}),
           "road_obstruction": _choice({"partial": 1.0})}
    with patch.object(reward, "query_jev", side_effect=[ans, {"road_match": {"type": "noul", "noul": 0.8}}]) as q:
        r = reward.reward_for("text", RAW, tmp_path, "b1")
    assert r["incident_type"] == 0.7 and r["severity"] == 0.6
    assert r["road_obstruction"] == 0.0  # missing label key
    assert r["road"] == 0.8
    assert abs(r["composite"] - (0.7 + 0.6 + 0 + 0.8) / 4) < 1e-9
    assert q.call_count == 2


def test_b1_null_road_no_extra_call(tmp_path):
    ans = {"incident_type": _choice({"flooding": 1.0}), "severity": _choice({"high": 1.0}),
           "road_obstruction": _choice({"full": 1.0})}
    with patch.object(reward, "query_jev", return_value=ans) as q:
        r = reward.reward_for("t", RAW_NULL_ROAD, tmp_path, "b1")
    assert r["road"] == 0.0 and q.call_count == 1


def test_b2_reward_is_noul_per_field(tmp_path):
    ans = {f: {"type": "noul", "noul": v} for f, v in zip(reward.FIELDS, (0.9, 0.8, 0.7, 0.6))}
    with patch.object(reward, "query_jev", return_value=ans) as q:
        r = reward.reward_for("t", RAW, tmp_path, "b2")
    assert [r[f] for f in reward.FIELDS] == [0.9, 0.8, 0.7, 0.6]
    assert abs(r["composite"] - 0.75) < 1e-9 and q.call_count == 1


def test_unparseable_prediction_gives_zero_rewards(tmp_path):
    for d in ("b1", "b2"):
        with patch.object(reward, "query_jev") as q:
            r = reward.reward_for("t", "not json", tmp_path, d)
        assert r == {**{f: 0.0 for f in reward.FIELDS}, "composite": 0.0}
        q.assert_not_called()


def _gold(road):
    return Record(id="1", split="train", text="t", language="english", incident_type="flooding",
                  location=Location(road=road), severity="high", road_obstruction="full")


def test_null_road_pair_matches():
    rep = parse_report(RAW_NULL_ROAD)
    m = reward.gold_match(_gold(None), rep)
    assert m == {f: True for f in reward.FIELDS}


def test_null_vs_value_no_match():
    assert reward.gold_match(_gold("EDSA"), parse_report(RAW_NULL_ROAD))["road"] is False
    assert reward.gold_match(_gold(None), parse_report(RAW))["road"] is False
    assert not any(reward.gold_match(_gold("EDSA"), None).values())
