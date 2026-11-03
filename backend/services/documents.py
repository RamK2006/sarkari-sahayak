"""KYC document analysis: Sarvam Vision (Doc AI) reads the document, Sarvam chat extracts structured fields,
and plain date arithmetic reviews validity. Nothing is stored; the client keeps the result in its vault.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import date
from functools import lru_cache

from backend.config import get_settings
from backend.services.sarvam_client import SarvamUnavailable, get_sarvam

log = logging.getLogger(__name__)

_MIME = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


@lru_cache(maxsize=1)
def doc_types() -> list[dict]:
    return json.loads(get_settings().DOC_TYPES_PATH.read_text(encoding="utf-8"))


def mime_for(filename: str) -> str | None:
    return _MIME.get("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else None


def read_text(data: bytes, filename: str, mime: str) -> str:
    """OCR/parse through Sarvam Vision. Raises SarvamUnavailable when the job fails or times out."""
    client = get_sarvam()._client
    try:
        job = client.doc_ai.parse(file=[(filename, data, mime)])
        for _ in range(30):
            status = client.doc_ai.get_status(job.job_id).status
            if status in ("completed", "partially_completed"):
                break
            if status in ("failed", "rejected"):
                raise SarvamUnavailable("doc_ai")
            time.sleep(2)
        else:
            raise SarvamUnavailable("doc_ai_timeout")
        wrapper = client.doc_ai._raw_client._client_wrapper
        res = wrapper.httpx_client.request(
            f"doc-ai/v1/job/{job.job_id}/results", base_url=wrapper.get_environment().base, method="GET"
        )
        body = res.json()
    except SarvamUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001
        log.warning("Doc AI failed: %.200s", exc)
        raise SarvamUnavailable("doc_ai") from exc
    lines = [
        b.get("text", "").strip()
        for d in body.get("documents", [])
        for p in d.get("pages", [])
        for b in p.get("blocks", [])
        if b.get("text", "").strip()
    ]
    return "\n".join(lines)


_PROMPT = """You read OCR text of an Indian identity or certificate document and return JSON only.
Allowed doc_type values: {types}. Use "other" if unsure.
Return exactly these keys: doc_type, holder_name, date_of_birth, issue_date, expiry_date, issuer, id_last4, quality_issues.
Dates must be YYYY-MM-DD or null. Use null for anything not clearly present in the text. Never guess.
id_last4 is only the last four characters of the main ID number, or null. Never output a full ID number.
quality_issues is a list drawn from: unreadable, partial, no_name, no_dates (empty list if none).
OCR text:
{text}"""


def _json_object(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except ValueError:
        return {}


def _date(v) -> str | None:
    try:
        return date.fromisoformat(str(v)).isoformat()
    except (TypeError, ValueError):
        return None


def extract_fields(text: str) -> dict:
    ids = [d["id"] for d in doc_types() if d.get("vault", True)]
    msg = get_sarvam().chat([{"role": "user", "content": _PROMPT.format(types=", ".join(ids), text=text[:6000])}])
    raw = _json_object(msg.content or "")
    doc_type = raw.get("doc_type") if raw.get("doc_type") in ids else "other"
    last4 = re.sub(r"\W", "", str(raw.get("id_last4") or ""))[-4:] or None
    return {
        "doc_type": doc_type,
        "holder_name": (str(raw["holder_name"]).strip()[:80] if raw.get("holder_name") else None),
        "date_of_birth": _date(raw.get("date_of_birth")),
        "issue_date": _date(raw.get("issue_date")),
        "expiry_date": _date(raw.get("expiry_date")),
        "issuer": (str(raw["issuer"]).strip()[:80] if raw.get("issuer") else None),
        "id_last4": last4,
        "quality_issues": [q for q in raw.get("quality_issues", []) if q in {"unreadable", "partial", "no_name", "no_dates"}],
    }


def review(expiry: str | None, today: date | None = None) -> dict:
    """Validity review from the printed expiry date alone. The frontend renders localized advice per state."""
    today = today or date.today()
    s = get_settings()
    if not expiry:
        return {"state": "no_expiry", "days_left": None, "expiry_date": None}
    days = (date.fromisoformat(expiry) - today).days
    if days < 0:
        state = "expired"
    elif days <= s.EXPIRING_SOON_DAYS:
        state = "expiring_soon"
    elif days <= s.UPCOMING_DAYS:
        state = "upcoming"
    else:
        state = "valid"
    return {"state": state, "days_left": days, "expiry_date": expiry}


def age_from(dob: str | None, today: date | None = None) -> int | None:
    if not dob:
        return None
    today = today or date.today()
    d = date.fromisoformat(dob)
    age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
    return age if 0 <= age <= 120 else None


def analyze(data: bytes, filename: str, mime: str) -> dict:
    text = read_text(data, filename, mime)
    if not text.strip():
        return {"doc_type": "other", "readable": False, "fields": None, "review": review(None), "profile_hints": {}}
    fields = extract_fields(text)
    hints = {}
    age = age_from(fields["date_of_birth"])
    if age is not None:
        hints["age"] = age
    return {"doc_type": fields["doc_type"], "readable": True, "fields": fields, "review": review(fields["expiry_date"]), "profile_hints": hints}


def classify_requirement(text: str) -> str | None:
    """Map a free-text scheme document requirement onto a document type id (data-driven keyword match)."""
    low = text.lower()
    for dt in doc_types():
        if any(k in low for k in dt["keywords"]):
            return dt["id"]
    return None


def match_vault(requirements: list[str], vault: list[dict]) -> list[dict]:
    """For each required document: have / expired / missing / unrecognised, using the citizen's vault."""
    out = []
    for text in requirements:
        t = classify_requirement(text)
        if t is None or not next(d for d in doc_types() if d["id"] == t).get("vault", True):
            out.append({"status": "unrecognised", "vault_id": None})
            continue
        held = [v for v in vault if v.get("doc_type") == t]
        valid = [v for v in held if review(v.get("expiry_date"))["state"] != "expired"]
        if valid:
            out.append({"status": "have", "vault_id": valid[0].get("id")})
        elif held:
            out.append({"status": "expired", "vault_id": held[0].get("id")})
        else:
            out.append({"status": "missing", "vault_id": None})
    return out
