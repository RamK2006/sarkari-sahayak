"""Progressive information gathering.

The questions are a registry. After the core fields are resolved, the next question is chosen from
the fields that schemes still in contention are waiting on, so a citizen is only asked what actually
changes the outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.services.eligibility import evaluate_all


@dataclass(frozen=True)
class Field:
    name: str
    kind: str  # number | choice | boolean
    options: tuple[str, ...] = ()
    minimum: int | None = None
    maximum: int | None = None
    core: bool = False
    description: str = ""


FIELDS: dict[str, Field] = {f.name: f for f in [
    Field("age", "number", minimum=0, maximum=120, core=True, description="Age in years"),
    Field("gender", "choice", ("female", "male", "other"), core=True, description="Gender"),
    Field("area", "choice", ("rural", "urban"), core=True,
          description="Whether the household lives in a rural or urban area"),
    Field("occupation", "choice",
          ("farmer", "student", "labourer", "self_employed", "salaried", "unemployed", "homemaker",
           "street_vendor", "artisan", "other"), core=True, description="Main occupation"),
    Field("annual_income", "number", minimum=0, maximum=1_000_000_000, core=True,
          description="Approximate annual household income in Indian rupees"),
    Field("category", "choice", ("general", "obc", "sc", "st"), description="Social category"),
    Field("priority_household", "boolean",
          description="Household holds a BPL, Antyodaya (AAY) or priority-household ration card"),
    Field("owns_farmland", "boolean", description="Owns agricultural land"),
    Field("owns_pucca_house", "boolean", description="Household owns a pucca (permanent) house"),
    Field("has_lpg", "boolean", description="Household already has an LPG gas connection"),
    Field("pays_income_tax", "boolean", description="Pays income tax"),
    Field("govt_employee", "boolean", description="Is a government employee"),
    Field("is_widow", "boolean", description="Is a widow"),
    Field("pregnant_or_lactating", "boolean", description="Is pregnant or breastfeeding"),
    Field("daughters_under_10", "number", minimum=0, maximum=10,
          description="Number of daughters below 10 years of age"),
    Field("post_matric_student", "boolean", description="Studying in Class 11 or above"),
]}
CORE_ORDER = [f.name for f in FIELDS.values() if f.core]
_ORDER = list(FIELDS)


def coerce(field_name: str, value: Any) -> Any:
    """Validate and normalise a value for a field. Raises ValueError when invalid."""
    f = FIELDS.get(field_name)
    if f is None:
        raise ValueError(f"unknown field {field_name}")
    if f.kind == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in {"true", "yes", "false", "no"}:
            return value.strip().lower() in {"true", "yes"}
        raise ValueError("expected a boolean")
    if f.kind == "number":
        if isinstance(value, bool):
            raise ValueError("expected a number")
        try:
            n = int(float(str(value).replace(",", "").strip()))
        except (TypeError, ValueError) as exc:
            raise ValueError("expected a number") from exc
        if (f.minimum is not None and n < f.minimum) or (f.maximum is not None and n > f.maximum):
            raise ValueError("out of range")
        return n
    if value in f.options:
        return value
    raise ValueError("not an allowed option")


def question_spec(name: str) -> dict:
    f = FIELDS[name]
    spec: dict[str, Any] = {"field": f.name, "kind": f.kind, "skippable": True}
    if f.options:
        spec["options"] = list(f.options)
    if f.minimum is not None:
        spec["min"] = f.minimum
    if f.maximum is not None:
        spec["max"] = f.maximum
    return spec


def core_resolved(profile: dict, skipped: set[str]) -> bool:
    return all(n in profile or n in skipped for n in CORE_ORDER)


def next_question(profile: dict, skipped: set[str], schemes: list[dict]) -> dict | None:
    for name in CORE_ORDER:
        if name not in profile and name not in skipped:
            return question_spec(name)
    counts: dict[str, int] = {}
    for r in evaluate_all(profile, skipped, schemes):
        if r["status"] == "not_eligible":
            continue
        for name in r["missing_fields"]:
            if name not in skipped and name in FIELDS:
                counts[name] = counts.get(name, 0) + 1
    if not counts:
        return None
    best = sorted(counts, key=lambda n: (-counts[n], _ORDER.index(n)))[0]
    return question_spec(best)


def clean_profile(raw: dict | None) -> dict:
    """Drop unknown keys and invalid values from a client-supplied profile."""
    out: dict[str, Any] = {}
    for k, v in (raw or {}).items():
        if k in FIELDS and v is not None:
            try:
                out[k] = coerce(k, v)
            except ValueError:
                continue
    return out


def clean_skipped(raw: list[str] | None) -> set[str]:
    return {s for s in (raw or []) if s in FIELDS}
