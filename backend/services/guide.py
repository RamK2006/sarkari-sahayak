"""Step-by-step form guidance with field-level values drawn from the citizen's own documents.

The model drafts the steps in the citizen's language. A field value is kept only when it literally appears in
the data the citizen supplied (vault fields or profile); otherwise it is dropped, so nothing is invented.
"""

from __future__ import annotations

import json
import re

from backend.config import LANGUAGE_ENGLISH_NAMES
from backend.services.catalog import get_catalog
from backend.services.sarvam_client import get_sarvam

_PLAN = """You prepare a step-by-step guide that helps an Indian citizen complete a form or procedure.
Write every user-facing string in {language}. Return JSON only, in this shape:
{{"title": str, "steps": [{{"title": str, "detail": str, "fields": [{{"label": str, "value": str|null, "hint": str}}]}}]}}
Rules:
- 3 to 7 steps, each short and concrete. Put form fields one by one in "fields" where the step involves filling a form.
- "value" may be filled ONLY with text copied exactly from the CITIZEN DATA below; otherwise null.
- Do not invent fees, deadlines, office names or website addresses. If unsure, tell the citizen to confirm with the official office or portal.
{grounding}
CITIZEN DATA: {data}
GOAL: {goal}"""


def _json(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except ValueError:
        return {}


def plan(goal: str, language: str, scheme_id: str | None, citizen_data: dict) -> dict:
    scheme = get_catalog().get(scheme_id) if scheme_id else None
    grounding = ""
    if scheme:
        goal = f"Apply for {scheme['name']}"
        grounding = (
            "GROUNDED SCHEME RECORD (use only this for scheme facts): "
            + json.dumps({k: scheme[k] for k in ("name", "summary", "benefits", "documents", "apply", "notes")}, ensure_ascii=False)
        )
    data_text = json.dumps(citizen_data, ensure_ascii=False)
    msg = get_sarvam().chat([{"role": "user", "content": _PLAN.format(
        language=LANGUAGE_ENGLISH_NAMES.get(language, "English"), grounding=grounding, data=data_text, goal=goal[:300])}])
    raw = _json(msg.content or "")
    steps = []
    for s in raw.get("steps", [])[:8]:
        fields = []
        for f in s.get("fields", [])[:12]:
            value = f.get("value")
            if value is not None and str(value) not in data_text:
                value = None  # not present in the citizen's own data: drop rather than risk an invented value
            fields.append({"label": str(f.get("label", ""))[:80], "value": value, "hint": str(f.get("hint", ""))[:200]})
        steps.append({"title": str(s.get("title", ""))[:120], "detail": str(s.get("detail", ""))[:400], "fields": fields})
    return {"title": str(raw.get("title") or goal)[:140], "steps": steps, "grounded": scheme is not None,
            "apply_url": scheme["apply"].get("url") if scheme else None}


_CLASSIFY = """The citizen is being guided through a form, one field at a time, and was just asked to confirm a field.
Classify what they said (language: {language}) into exactly one intent: confirm, repeat, back, skip, question.
Return JSON only: {{"intent": "..."}}. If it is a question about the form, use "question".
They said: {text}"""


def classify(text: str, language: str) -> str:
    msg = get_sarvam().chat([{"role": "user", "content": _CLASSIFY.format(language=LANGUAGE_ENGLISH_NAMES.get(language, "English"), text=text[:300])}])
    intent = _json(msg.content or "").get("intent")
    return intent if intent in {"confirm", "repeat", "back", "skip", "question"} else "question"
