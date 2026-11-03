"""Intake progress, eligibility results and scheme detail."""

from __future__ import annotations

from fastapi import APIRouter

from backend.errors import api_error
from backend.schemas import AnswerRequest, Citizen, valid_language
from backend.services import intake
from backend.services.catalog import get_catalog
from backend.services.eligibility import evaluate_all, evaluate_scheme
from backend.services.translation import localize_scheme

router = APIRouter(prefix="/api", tags=["schemes"])


def intake_state_for(profile: dict, skipped: set[str]) -> dict:
    return {
        "profile": profile,
        "skipped": sorted(skipped),
        "next_question": intake.next_question(profile, skipped, get_catalog().all()),
        "ready": intake.core_resolved(profile, skipped),
    }


@router.get("/intake/question/{field}")
def intake_question(field: str) -> dict:
    if field not in intake.FIELDS:
        raise api_error(404, "not_found")
    return intake.question_spec(field)


@router.post("/intake/state")
def intake_state(body: Citizen) -> dict:
    return intake_state_for(intake.clean_profile(body.profile), intake.clean_skipped(body.skipped))


@router.post("/intake/answer")
def intake_answer(body: AnswerRequest) -> dict:
    if body.field not in intake.FIELDS:
        raise api_error(422, "invalid_value")
    profile = intake.clean_profile(body.profile)
    skipped = intake.clean_skipped(body.skipped)
    if body.value is None:
        profile.pop(body.field, None)
        skipped.add(body.field)
    else:
        try:
            profile[body.field] = intake.coerce(body.field, body.value)
        except ValueError:
            raise api_error(422, "invalid_value") from None
        skipped.discard(body.field)
    return intake_state_for(profile, skipped)


@router.post("/eligibility")
def eligibility(body: Citizen) -> dict:
    """Personalised results, withheld until the core questions are answered or skipped."""
    profile = intake.clean_profile(body.profile)
    skipped = intake.clean_skipped(body.skipped)
    if not intake.core_resolved(profile, skipped):
        return {"ready": False, "results": [], "translated": True}
    lang = valid_language(body.language)
    catalog = get_catalog()
    results = evaluate_all(profile, skipped, catalog.all())
    all_ok = True
    for r in results:
        view, ok = localize_scheme(catalog.get(r["scheme_id"]), lang)
        r["scheme"] = view
        all_ok = all_ok and ok
    return {"ready": True, "results": results, "translated": all_ok}


@router.post("/schemes/{scheme_id}")
def scheme_detail(scheme_id: str, body: Citizen) -> dict:
    scheme = get_catalog().get(scheme_id)
    if scheme is None:
        raise api_error(404, "not_found")
    profile = intake.clean_profile(body.profile)
    skipped = intake.clean_skipped(body.skipped)
    view, ok = localize_scheme(scheme, valid_language(body.language), detail=True)
    return {
        "scheme": view,
        "evaluation": evaluate_scheme(profile, skipped, scheme),
        "translated": ok,
        "ready": intake.core_resolved(profile, skipped),
    }
