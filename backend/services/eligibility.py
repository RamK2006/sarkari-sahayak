"""Deterministic eligibility engine.

Each scheme in the catalog lists typed criteria. Every criterion is evaluated against the citizen's
profile and yields one of four outcomes:

  met      the profile satisfies the criterion
  unmet    the profile contradicts the criterion
  unknown  the profile does not yet contain the information needed (a `field` is reported)
  verify   cannot be decided from a self-reported profile; needs an official record or document

The scheme status is derived purely from those outcomes (no scores, no weighting):

  not_eligible          any criterion is unmet
  insufficient_info     none unmet, at least one unknown
  potentially_eligible  all decidable criteria met, at least one verify item remains
  eligible              every criterion met, nothing left to verify
"""

from __future__ import annotations

from typing import Any, Callable

Profile = dict[str, Any]
Result = tuple[str, dict[str, Any], str | None]  # (outcome, params, field)

STATUS_ORDER = ["eligible", "potentially_eligible", "insufficient_info", "not_eligible"]


def _bool_required(field: str, want: bool = True) -> Callable[[Profile, dict], Result]:
    def check(p: Profile, c: dict) -> Result:
        v = p.get(field)
        if v is None:
            return "unknown", {}, field
        return ("met" if v is want else "unmet"), {}, field

    return check


def _age_min(p: Profile, c: dict) -> Result:
    age = p.get("age")
    if age is None:
        return "unknown", {"min": c["value"]}, "age"
    return ("met" if age >= c["value"] else "unmet"), {"age": age, "min": c["value"]}, "age"


def _age_max(p: Profile, c: dict) -> Result:
    age = p.get("age")
    if age is None:
        return "unknown", {"max": c["value"]}, "age"
    return ("met" if age <= c["value"] else "unmet"), {"age": age, "max": c["value"]}, "age"


def _enum(field: str) -> Callable[[Profile, dict], Result]:
    def check(p: Profile, c: dict) -> Result:
        v = p.get(field)
        if v is None:
            return "unknown", {"value": c["value"]}, field
        return ("met" if v == c["value"] else "unmet"), {"value": c["value"], "actual": v}, field

    return check


def _enum_in(field: str) -> Callable[[Profile, dict], Result]:
    def check(p: Profile, c: dict) -> Result:
        v = p.get(field)
        values = c["values"]
        if v is None:
            return "unknown", {"values": values}, field
        return ("met" if v in values else "unmet"), {"values": values, "actual": v}, field

    return check


def _income_max(p: Profile, c: dict) -> Result:
    income = p.get("annual_income")
    if income is None:
        return "unknown", {"limit": c["value"]}, "annual_income"
    return ("met" if income <= c["value"] else "unmet"), {"income": income, "limit": c["value"]}, "annual_income"


def _income_max_by_category(p: Profile, c: dict) -> Result:
    limits: dict[str, int] = c["limits"]
    category, income = p.get("category"), p.get("annual_income")
    if category is None:
        return "unknown", {}, "category"
    if category not in limits:
        # Not decidable here; the category criterion reports the mismatch.
        return "met", {}, None
    limit = limits[category]
    if income is None:
        return "unknown", {"limit": limit, "category": category}, "annual_income"
    outcome = "met" if income <= limit else "unmet"
    return outcome, {"income": income, "limit": limit, "category": category}, "annual_income"


def _priority_household(p: Profile, c: dict) -> Result:
    v = p.get("priority_household")
    if v is None:
        return "unknown", {}, "priority_household"
    if v:
        return "met", {}, "priority_household"
    # Some schemes use official lists beyond ration cards, so "no card" is not a rejection for them.
    return ("unmet" if c.get("strict") else "verify"), {}, "priority_household"


def _daughters(p: Profile, c: dict) -> Result:
    n = p.get("daughters_under_10")
    if n is None:
        return "unknown", {}, "daughters_under_10"
    return ("met" if n > 0 else "unmet"), {"count": n}, "daughters_under_10"


def _verify(p: Profile, c: dict) -> Result:
    return "verify", {"code": c["code"]}, None


_CHECKS: dict[str, Callable[[Profile, dict], Result]] = {
    "age_min": _age_min,
    "age_max": _age_max,
    "gender": _enum("gender"),
    "area": _enum("area"),
    "occupation_in": _enum_in("occupation"),
    "category_in": _enum_in("category"),
    "owns_farmland": _bool_required("owns_farmland"),
    "no_pucca_house": _bool_required("owns_pucca_house", False),
    "no_lpg": _bool_required("has_lpg", False),
    "not_income_tax_payer": _bool_required("pays_income_tax", False),
    "not_govt_employee": _bool_required("govt_employee", False),
    "is_widow": _bool_required("is_widow"),
    "pregnant_or_lactating": _bool_required("pregnant_or_lactating"),
    "post_matric_student": _bool_required("post_matric_student"),
    "income_max": _income_max,
    "income_max_by_category": _income_max_by_category,
    "priority_household": _priority_household,
    "daughters_under_10": _daughters,
    "verify": _verify,
}


def evaluate_scheme(profile: Profile, skipped: set[str], scheme: dict) -> dict:
    items: list[dict] = []
    for criterion in scheme["criteria"]:
        outcome, params, field = _CHECKS[criterion["type"]](profile, criterion)
        item: dict[str, Any] = {"criterion": criterion["type"], "outcome": outcome, "params": params}
        if field:
            item["field"] = field
        if outcome == "unknown" and field in skipped:
            item["skipped"] = True
        items.append(item)

    outcomes = {i["outcome"] for i in items}
    if "unmet" in outcomes:
        status = "not_eligible"
    elif "unknown" in outcomes:
        status = "insufficient_info"
    elif "verify" in outcomes:
        status = "potentially_eligible"
    else:
        status = "eligible"

    missing = sorted({i["field"] for i in items if i["outcome"] == "unknown"})
    return {"scheme_id": scheme["id"], "status": status, "items": items, "missing_fields": missing}


def evaluate_all(profile: Profile, skipped: set[str], schemes: list[dict]) -> list[dict]:
    results = [evaluate_scheme(profile, skipped, s) for s in schemes]
    results.sort(key=lambda r: STATUS_ORDER.index(r["status"]))
    return results
