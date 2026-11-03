"""API tests that never touch Sarvam (English requests need no translation)."""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

CORE = [("age", 62), ("gender", "female"), ("area", "rural"), ("occupation", "homemaker"), ("annual_income", 90000)]


def answer(profile, skipped, field, value):
    r = client.post("/api/intake/answer", json={"profile": profile, "skipped": skipped, "field": field, "value": value})
    assert r.status_code == 200, r.text
    return r.json()


def test_health_and_meta():
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/api/meta").json()["scheme_count"] == 15


def test_no_results_before_core_questions_are_resolved():
    r = client.post("/api/eligibility", json={"language": "en", "profile": {"age": 30}, "skipped": []})
    assert r.json() == {"ready": False, "results": [], "translated": True}


def test_full_flow_then_results():
    profile, skipped = {}, []
    for field, value in CORE:
        state = answer(profile, skipped, field, value)
        profile, skipped = state["profile"], state["skipped"]
    assert state["ready"] and state["next_question"]["field"] == "priority_household"

    r = client.post("/api/eligibility", json={"language": "en", "profile": profile, "skipped": skipped}).json()
    assert r["ready"] and len(r["results"]) == 15
    by_id = {x["scheme_id"]: x for x in r["results"]}
    assert by_id["pm-kisan"]["status"] == "not_eligible"
    assert by_id["nsap-ignoaps"]["status"] == "insufficient_info"
    assert "priority_household" in by_id["nsap-ignoaps"]["missing_fields"]
    assert by_id["nsap-ignoaps"]["scheme"]["name"].startswith("Indira Gandhi")


def test_skipping_resolves_a_question_and_is_remembered():
    state = answer({}, [], "age", None)
    assert state["skipped"] == ["age"] and "age" not in state["profile"]
    assert state["next_question"]["field"] == "gender"


def test_invalid_values_are_rejected():
    for field, value in [("age", 500), ("gender", "robot"), ("nope", 1)]:
        r = client.post("/api/intake/answer", json={"profile": {}, "skipped": [], "field": field, "value": value})
        assert r.status_code == 422 and r.json()["detail"]["code"] == "invalid_value"


def test_client_supplied_profile_is_sanitised():
    r = client.post("/api/intake/state", json={"profile": {"age": 999, "evil": "x", "gender": "female"}, "skipped": ["zzz"]})
    assert r.json()["profile"] == {"gender": "female"} and r.json()["skipped"] == []


def test_scheme_detail_and_not_found():
    r = client.post("/api/schemes/pm-kisan", json={"language": "en", "profile": {}, "skipped": []})
    body = r.json()
    assert r.status_code == 200 and body["scheme"]["documents"] and body["ready"] is False
    missing = client.post("/api/schemes/does-not-exist", json={"language": "en"})
    assert missing.status_code == 404 and missing.json()["detail"]["code"] == "not_found"


def test_voice_rejects_empty_audio():
    r = client.post("/api/voice/stt", files={"audio": ("a.webm", b"", "audio/webm")}, data={"language": "en"})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "empty_audio"
