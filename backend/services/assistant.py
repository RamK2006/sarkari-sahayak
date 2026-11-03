"""Counselor-style assistant on Sarvam chat.

The citizen can say anything: ask about a scheme, how to get or verify a document, what their documents allow,
or ask for help filling a form. The model routes through tools (profile facts, scheme retrieval, eligibility),
and never decides eligibility itself: that always comes from the deterministic engine.
"""

from __future__ import annotations

import json
import re
from typing import Any

from backend.config import LANGUAGE_ENGLISH_NAMES
from backend.services import rag
from backend.services.catalog import get_catalog
from backend.services.eligibility import evaluate_scheme
from backend.services.intake import FIELDS, coerce
from backend.services.sarvam_client import get_sarvam

MOODS = ("neutral", "happy", "empathetic", "serious", "thinking")
GESTURES = ("none", "namaste", "open", "point")

_SYSTEM = """You are a warm, patient counselor helping Indian citizens with government schemes and paperwork.
Reply only in {language}, in short plain sentences suitable for being read aloud. No emojis, markdown or bullet symbols.

Begin every reply with two tags on one line: [mood: X] [gesture: Y]
X is one of {moods} (match the feeling: empathetic for hardship, serious for deadlines or risks, happy for good news).
Y is one of {gestures} (namaste only for a greeting, open to offer help, point to direct attention, otherwise none).

How to help:
1. Answer what the person asked first. Do not interrogate them. Only ask for a personal detail at the moment it is needed to answer, and ask one thing at a time.
2. For questions about schemes or benefits, call search_schemes (write the query in English) and answer only from the records returned. For "am I eligible", call check_eligibility; explain the result and ask for any missing detail conversationally. Never state eligibility yourself.
3. When the person states facts about themselves, call record_profile with exactly what they said. Never guess. Income is rupees per year.
4. For how-to questions about documents or services (getting or verifying Aadhaar, opening a bank account, passport, licence, certificates), give practical general guidance in a few steps and say it is general guidance to confirm with the official office or portal. Mention a website only if you are certain of it. Then end with [guide: <the task in English>] so the app can offer a step-by-step form guide.
5. If a document would help, end with [upload: <document type id>] using one of: {doc_types}.
6. Use the citizen's documents (listed below) to say what they can use and what is missing or expiring.
7. Never invent schemes, amounts, dates, links or office names. If you do not know, say so.
{known}{vault}"""

_TAG = re.compile(r"\[(mood|gesture|guide|upload):\s*([^\]]*)\]", re.I)


def _tools() -> list[dict]:
    props: dict[str, Any] = {}
    for f in FIELDS.values():
        if f.kind == "boolean":
            props[f.name] = {"type": "boolean", "description": f.description}
        elif f.kind == "number":
            props[f.name] = {"type": "integer", "description": f.description}
        else:
            props[f.name] = {"type": "string", "enum": list(f.options), "description": f.description}
    fn = lambda name, desc, params: {"type": "function", "function": {"name": name, "description": desc, "parameters": params}}  # noqa: E731
    return [
        fn("record_profile", "Record facts the user explicitly stated about themselves or their household.", {"type": "object", "properties": props}),
        fn("search_schemes", "Search the official scheme catalog. Returns scheme records with ids.",
           {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}),
        fn("check_eligibility", "Check the user's eligibility for one scheme using known profile facts.",
           {"type": "object", "properties": {"scheme_id": {"type": "string"}}, "required": ["scheme_id"]}),
    ]


def _for_model(s: dict) -> dict:
    return {
        "id": s["id"], "name": s["name"], "ministry": s["ministry"], "summary": s["summary"], "benefits": s["benefits"],
        "documents": s["documents"], "notes": s.get("notes", []),
        "apply": s["apply"].get("url") or s["apply"].get("channel"), "source": s.get("source_url"),
    }


def _parse_tags(text: str) -> tuple[str, dict[str, str]]:
    tags = {m.group(1).lower(): m.group(2).strip() for m in _TAG.finditer(text)}
    clean = _TAG.sub("", re.sub(r"<think>.*?</think>", "", text or "", flags=re.S))
    return re.sub(r"[*_#`]+", "", clean).strip(), tags


def respond(language: str, message: str, profile: dict, skipped: set[str], history: list[dict], vault: list[dict]) -> dict:
    """Returns reply, mood, gesture, guide, upload, schemes (ids) and applied profile facts."""
    from backend.services.documents import doc_types, review

    known = ("\nKnown about the user: " + json.dumps(profile, ensure_ascii=False)) if profile else ""
    vault_text = ""
    if vault:
        rows = [f"{v.get('doc_type')} ({review(v.get('expiry_date'))['state']}, expires {v.get('expiry_date') or 'no date'})" for v in vault]
        vault_text = "\nThe user's documents: " + "; ".join(rows)
    system = _SYSTEM.format(
        language=LANGUAGE_ENGLISH_NAMES.get(language, "English"), moods=", ".join(MOODS), gestures=", ".join(GESTURES),
        doc_types=", ".join(d["id"] for d in doc_types() if d.get("vault", True)), known=known, vault=vault_text,
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for h in history[-10:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": str(h["content"])[:1000]})
    messages.append({"role": "user", "content": message})

    client = get_sarvam()
    tools = _tools()
    applied: dict[str, Any] = {}
    scheme_ids: list[str] = []
    msg = client.chat(messages, tools=tools)

    for _ in range(2):  # at most two tool rounds
        if not msg.tool_calls:
            break
        messages.append({
            "role": "assistant", "content": msg.content or "",
            "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in msg.tool_calls],
        })
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except ValueError:
                args = {}
            name = tc.function.name
            if name == "record_profile":
                for k, v in args.items():
                    try:
                        applied[k] = coerce(k, v)
                    except ValueError:
                        continue
                out: Any = {"recorded": sorted(applied)}
            elif name == "search_schemes":
                hits = rag.search(str(args.get("query", "")), filters={**profile, **applied}, limit=4)
                scheme_ids += [h["scheme"]["id"] for h in hits if h["scheme"]["id"] not in scheme_ids]
                out = [{**_for_model(h["scheme"]), "status": h["evaluation"]["status"]} for h in hits]
            elif name == "check_eligibility":
                scheme = get_catalog().get(str(args.get("scheme_id", "")))
                if scheme:
                    ev = evaluate_scheme({**profile, **applied}, skipped, scheme)
                    if scheme["id"] not in scheme_ids:
                        scheme_ids.append(scheme["id"])
                    out = {"scheme": scheme["name"], "status": ev["status"], "unmet": [i["criterion"] for i in ev["items"] if i["outcome"] == "unmet"],
                           "missing": [FIELDS[f].description for f in ev["missing_fields"] if f in FIELDS],
                           "to_verify": [i["params"].get("code") for i in ev["items"] if i["outcome"] == "verify"]}
                else:
                    out = {"error": "unknown scheme_id"}
            else:
                out = {}
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(out, ensure_ascii=False)})
        msg = client.chat(messages, tools=tools, tool_choice="auto")

    reply, tags = _parse_tags(msg.content or "")
    if msg.tool_calls and not reply:  # tool rounds exhausted without prose: ask for the final answer
        reply, tags = _parse_tags(client.chat(messages, tools=tools, tool_choice="none").content or "")
    mood = tags.get("mood", "neutral").lower()
    gesture = tags.get("gesture", "none").lower()
    return {
        "reply": reply,
        "mood": mood if mood in MOODS else "neutral",
        "gesture": gesture if gesture in GESTURES else "none",
        "guide": tags.get("guide") or None,
        "upload": tags.get("upload") if tags.get("upload") in {d["id"] for d in doc_types()} else None,
        "schemes": scheme_ids,
        "applied": applied,
    }
