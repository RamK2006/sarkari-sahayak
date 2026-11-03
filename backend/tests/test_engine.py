"""Unit tests for the eligibility engine and intake flow (no network)."""

from backend.services import intake
from backend.services.catalog import get_catalog
from backend.services.eligibility import evaluate_all, evaluate_scheme

SCHEMES = get_catalog().all()


def status(profile, scheme_id, skipped=()):
    scheme = get_catalog().get(scheme_id)
    return evaluate_scheme(profile, set(skipped), scheme)["status"]


def test_empty_profile_is_never_eligible():
    assert all(r["status"] in {"insufficient_info"} for r in evaluate_all({}, set(), SCHEMES)
               if r["status"] != "not_eligible")
    assert not any(r["status"] == "eligible" for r in evaluate_all({}, set(), SCHEMES))


def test_pm_kisan_confirmed():
    p = {"occupation": "farmer", "owns_farmland": True, "pays_income_tax": False, "govt_employee": False}
    assert status(p, "pm-kisan") == "eligible"


def test_pm_kisan_unmet_when_not_farmer():
    assert status({"occupation": "salaried"}, "pm-kisan") == "not_eligible"


def test_pm_kisan_missing_info():
    assert status({"occupation": "farmer"}, "pm-kisan") == "insufficient_info"


def test_verify_items_make_scheme_potential():
    p = {"occupation": "street_vendor"}
    assert status(p, "pm-svanidhi") == "potentially_eligible"


def test_strict_priority_household_unmet_and_lenient_verify():
    assert status({"priority_household": False, "age": 70, "govt_employee": False}, "nsap-ignoaps") == "not_eligible"
    r = evaluate_scheme({"priority_household": False, "pays_income_tax": False, "govt_employee": False},
                        set(), get_catalog().get("pmjay"))
    assert r["status"] == "potentially_eligible"


def test_income_limit_by_category():
    base = {"occupation": "student", "post_matric_student": True, "category": "obc"}
    assert status({**base, "annual_income": 90000}, "nsp-post-matric") == "eligible"
    assert status({**base, "annual_income": 150000}, "nsp-post-matric") == "not_eligible"
    assert status({**base, "category": "sc", "annual_income": 150000}, "nsp-post-matric") == "eligible"


def test_skipped_field_is_flagged():
    r = evaluate_scheme({}, {"age"}, get_catalog().get("atal-pension"))
    assert any(i.get("skipped") for i in r["items"] if i["field"] == "age")


def test_core_questions_come_first_and_in_order():
    profile, skipped, asked = {}, set(), []
    for _ in range(5):
        q = intake.next_question(profile, skipped, SCHEMES)
        asked.append(q["field"])
        profile[q["field"]] = intake.coerce(q["field"], {"number": 30, "choice": q.get("options", [""])[0], "boolean": False}[q["kind"]])
    assert asked == intake.CORE_ORDER
    assert intake.core_resolved(profile, skipped)


def test_adaptive_questions_skip_irrelevant_fields():
    profile = {"age": 30, "gender": "male", "area": "urban", "occupation": "salaried", "annual_income": 800000}
    q = intake.next_question(profile, set(), SCHEMES)
    asked = set()
    while q:
        asked.add(q["field"])
        profile[q["field"]] = {"number": 0, "choice": q.get("options", [None])[0], "boolean": False}[q["kind"]]
        q = intake.next_question(profile, set(), SCHEMES)
    assert "owns_farmland" not in asked  # a salaried person is already ruled out of PM-KISAN
    assert "is_widow" not in asked  # a man is ruled out of the widow pension


def test_validation():
    assert intake.coerce("age", "42") == 42
    for field, bad in [("age", 400), ("age", "abc"), ("gender", "robot"), ("is_widow", "maybe")]:
        try:
            intake.coerce(field, bad)
        except ValueError:
            continue
        raise AssertionError(f"{field}={bad} should be rejected")
