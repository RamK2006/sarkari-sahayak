"""Retrieval, document review and vault matching (no network)."""

from datetime import date

from backend.services import documents, rag


def test_search_ranks_relevant_scheme_first():
    hits = rag.search("farmer income support")
    assert hits and hits[0]["scheme"]["id"] == "pm-kisan"


def test_filters_drop_ruled_out_schemes():
    ids = {h["scheme"]["id"] for h in rag.search("", filters={"gender": "male", "age": 30})}
    assert "ujjwala" not in ids and "nsap-ignwps" not in ids


def test_state_filter_keeps_central_schemes():
    assert rag.search("pension", state="Kerala")


def test_review_states():
    today = date(2026, 1, 1)
    assert documents.review(None, today)["state"] == "no_expiry"
    assert documents.review("2025-12-31", today)["state"] == "expired"
    assert documents.review("2026-01-20", today)["state"] == "expiring_soon"
    assert documents.review("2026-03-01", today)["state"] == "upcoming"
    assert documents.review("2027-01-01", today)["state"] == "valid"


def test_age_from_dob():
    assert documents.age_from("2000-06-15", date(2026, 6, 14)) == 25
    assert documents.age_from("2000-06-15", date(2026, 6, 15)) == 26


def test_vault_matching():
    reqs = ["Aadhaar card", "Passport-size photograph", "Ration card (PHH or AAY)", "Income certificate"]
    vault = [{"id": "a", "doc_type": "aadhaar", "expiry_date": None}, {"id": "i", "doc_type": "income_certificate", "expiry_date": "2000-01-01"}]
    got = [m["status"] for m in documents.match_vault(reqs, vault)]
    assert got == ["have", "unrecognised", "missing", "expired"]


def test_search_only_records_are_not_assessed():
    from backend.services.eligibility import evaluate_scheme

    record = {"id": "x", "name": "X", "criteria": []}
    assert evaluate_scheme({"age": 30}, set(), record)["status"] == "not_assessed"
