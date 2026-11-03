"""Conversational assistant on Sarvam's chat model.

The model has two jobs: extract profile facts from what the citizen says (typed or transcribed), and
answer questions about schemes using only catalog data returned by a tool. Eligibility decisions are
never made by the model; they come from the deterministic engine.
"""

from __future__ import annotations

import json
import re
from typing import Any

from backend.config import LANGUAGE_ENGLISH_NAMES
from backend.services.catalog import get_catalog
from backend.services.intake import FIELDS, coerce
from backend.services.sarvam_client import get_sarvam

_SYSTEM = """You are the assistant inside a government welfare scheme finder for Indian citizens.
Reply only in {language}. Use short, plain sentences. Do not use emojis, markdown, headings or bullet symbols.

Rules:
1. When the user states facts about themselves, call record_profile with exactly what they stated. Never guess or infer values they did not state. Convert income to rupees per year (for example 8000 rupees a month is 96000).
2. When the user asks about a scheme, benefit, document or how to apply, call search_schemes and answer only from its result. If nothing relevant is returned, say there is no verified information about it in the catalog. Never invent schemes, amounts, links or eligibility rules.
3. Never tell the user that they are or are not eligible. Eligibility is shown separately by the application from verified rules.
4. The application asks the intake questions itself. Do not ask for profile details unless an answer was unclear.
5. Be honest. If you cannot help with something, say so briefly.
{known}{asking}"""


def _tools() -> list[dict]:
    props: dict[str, Any] = {}
    for f in FIELDS.values():
        if f.kind == "boolean":
            props[f.name] = {"type": "boolean", "description": f.description}
        elif f.kind == "number":
            props[f.name] = {"type": "integer", "description": f.description}
        else:
            props[f.name] = {"type": "string", "enum": list(f.options), "description": f.description}
    return [
        {
            "type": "function",
            "function": {
                "name": "record_profile",
                "description": "Record facts the user explicitly stated about themselves or their household.",
                "parameters": {"type": "object", "properties": props},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_schemes",
                "description": "Search the verified scheme catalog by keyword. Returns scheme records.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Keywords, e.g. pension, housing, farmer"}},
                    "required": ["query"],
                },
            },
        },
    ]


def _search(query: str, limit: int = 4) -> list[dict]:
    terms = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]
    scored = []
    for s in get_catalog().all():
        hay = " ".join([s["name"], s["summary"], s["benefits"], s["ministry"], " ".join(s["categories"])]).lower()
        score = sum(hay.count(t) for t in terms)
        if score:
            scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    return [_for_model(s) for _, s in scored[:limit]]


def _for_model(s: dict) -> dict:
    return {
        "name": s["name"], "ministry": s["ministry"], "summary": s["summary"], "benefits": s["benefits"],
        "documents": s["documents"], "notes": s["notes"],
        "apply": s["apply"].get("url") or s["apply"].get("channel"), "source": s.get("source_url"),
    }


def _clean(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    text = re.sub(r"[*_#`]+", "", text)
    return text.strip()


def respond(language: str, message: str, profile: dict, history: list[dict], asking: str | None = None) -> dict:
    """Return {"reply": str, "applied": {field: value}}. Raises SarvamUnavailable on failure."""
    known = ""
    if profile:
        known = "\nAlready known about the user (do not ask again): " + json.dumps(profile, ensure_ascii=False)
    asked = ""
    if asking in FIELDS:
        asked = (
            f"\nThe application is currently asking the user for: {FIELDS[asking].description} (field {asking}). "
            "If the reply is a bare value or a short answer, record it for that field."
        )
    system = _SYSTEM.format(language=LANGUAGE_ENGLISH_NAMES.get(language, "English"), known=known, asking=asked)
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for h in history[-8:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": str(h["content"])[:1000]})
    messages.append({"role": "user", "content": message})

    client = get_sarvam()
    tools = _tools()
    msg = client.chat(messages, tools=tools)
    applied: dict[str, Any] = {}

    if not msg.tool_calls:
        return {"reply": _clean(msg.content), "applied": applied}

    messages.append({
        "role": "assistant",
        "content": msg.content or "",
        "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ],
    })
    searched = False
    for tc in msg.tool_calls:
        try:
            args = json.loads(tc.function.arguments or "{}")
        except ValueError:
            args = {}
        if tc.function.name == "record_profile":
            for k, v in args.items():
                try:
                    applied[k] = coerce(k, v)
                except ValueError:
                    continue
            content = json.dumps({"recorded": sorted(applied)})
        elif tc.function.name == "search_schemes":
            searched = True
            content = json.dumps(_search(str(args.get("query", ""))), ensure_ascii=False)
        else:
            content = "{}"
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": content})

    if not searched:
        # Only facts were recorded; the app proceeds with its next question.
        return {"reply": "", "applied": applied}
    final = client.chat(messages, tools=tools, tool_choice="none")
    return {"reply": _clean(final.content), "applied": applied}
