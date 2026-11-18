from unittest.mock import MagicMock, patch

import pytest
import requests

import jev_client

STATE = ["Traffic report: baha sa EDSA"]
QUESTIONS = {"q": {"type": "noul", "instructions": "x"}}


def resp(status, answers=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = {"answers": answers or {}}
    if status >= 400:
        r.raise_for_status.side_effect = requests.HTTPError(str(status))
    return r


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(jev_client.time, "sleep", lambda s: None)


def test_cache_hit_skips_network(tmp_path):
    with patch("jev_client.requests.post", return_value=resp(200, {"q": 1})) as p:
        a = jev_client.query_jev(STATE, QUESTIONS, tmp_path)
        b = jev_client.query_jev(STATE, QUESTIONS, tmp_path)
    assert a == b == {"q": 1}
    assert p.call_count == 1


def test_error_not_cached(tmp_path):
    with patch("jev_client.requests.post", side_effect=[resp(500), resp(200, {"q": 2})]):
        out = jev_client.query_jev(STATE, QUESTIONS, tmp_path)
    assert out == {"q": 2}
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_retries_on_429(tmp_path):
    with patch("jev_client.requests.post", side_effect=[resp(429), resp(429), resp(200, {"q": 3})]) as p:
        out = jev_client.query_jev(STATE, QUESTIONS, tmp_path)
    assert out == {"q": 3}
    assert p.call_count == 3


def test_client_error_raises_without_retry(tmp_path):
    with patch("jev_client.requests.post", return_value=resp(400)) as p:
        with pytest.raises(requests.HTTPError):
            jev_client.query_jev(STATE, QUESTIONS, tmp_path)
    assert p.call_count == 1


def test_key_not_in_cache_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "key-one")
    k1 = jev_client.cache_key("m", STATE, QUESTIONS)
    monkeypatch.setenv("OPENROUTER_API_KEY", "key-two")
    k2 = jev_client.cache_key("m", STATE, QUESTIONS)
    assert k1 == k2
    assert "key-one" not in k1
