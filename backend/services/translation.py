"""Translation with a persistent cache, backed by Sarvam translation.

Scheme text is authored once (in English) and translated on demand. Results are cached in memory and
on disk (backend/data/translations/<lang>.json), so each string is translated once per language.
Failures are never hidden: callers receive `ok=False` and the untranslated source text.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor

from backend.config import LANGUAGE_BY_CODE, get_settings
from backend.services.sarvam_client import SarvamUnavailable, get_sarvam

log = logging.getLogger(__name__)

_MAX_CHARS = 900
_lock = threading.Lock()
_caches: dict[str, dict[str, str]] = {}


def _key(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _path(lang: str):
    return get_settings().TRANSLATIONS_DIR / f"{lang}.json"


def _cache(lang: str) -> dict[str, str]:
    with _lock:
        if lang not in _caches:
            try:
                _caches[lang] = json.loads(_path(lang).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                _caches[lang] = {}
        return _caches[lang]


def _persist(lang: str) -> None:
    try:
        with _lock:
            _path(lang).parent.mkdir(parents=True, exist_ok=True)
            _path(lang).write_text(
                json.dumps(_caches[lang], ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8"
            )
    except OSError as exc:  # read-only filesystems are fine; the in-memory cache still works
        log.info("Could not persist translation cache: %s", exc)


def _chunks(text: str) -> list[str]:
    if len(text) <= _MAX_CHARS:
        return [text]
    parts, current = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if current and len(current) + len(sentence) + 1 > _MAX_CHARS:
            parts.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        parts.append(current)
    return parts


def translate(text: str, lang: str, source: str = "en") -> tuple[str, bool]:
    """Translate `text` (English unless `source` says otherwise) into `lang`. Returns (text, ok)."""
    if (lang == "en" and source == "en") or not text.strip():
        return text, True
    if lang not in LANGUAGE_BY_CODE:
        return text, False
    cache = _cache(lang)
    k = _key(text)  # source language does not change the translation target text
    if k in cache:
        return cache[k], True
    try:
        client = get_sarvam()
        out = " ".join(client.translate(part, lang, source) for part in _chunks(text))
    except SarvamUnavailable:
        return text, False
    cache[k] = out
    _persist(lang)
    return out, True


def translate_many(texts: list[str], lang: str, source: str = "en") -> tuple[list[str], bool]:
    """Translate several strings concurrently. Returns (texts, all_ok)."""
    if not texts or (lang == "en" and source == "en"):
        return list(texts), True
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda t: translate(t, lang, source), texts))
    return [r[0] for r in results], all(r[1] for r in results)


def localize_scheme(scheme: dict, lang: str, detail: bool = False) -> tuple[dict, bool]:
    """Return a presentation copy of a scheme with its text translated into `lang`."""
    fields = [scheme["name"], scheme["ministry"], scheme["summary"], scheme["benefits"]]
    channel = scheme["apply"].get("channel")
    if channel:
        fields.append(channel)
    if detail:
        fields += scheme["documents"] + scheme["notes"]
    out, ok = translate_many(fields, lang)
    it = iter(out)
    view = {
        "id": scheme["id"],
        "name": next(it),
        "ministry": next(it),
        "summary": next(it),
        "benefits": next(it),
        "categories": scheme["categories"],
        "apply": {"url": scheme["apply"].get("url"), "channel": next(it) if channel else None},
        "source_url": scheme.get("source_url"),
    }
    if detail:
        view["documents"] = [next(it) for _ in scheme["documents"]]
        view["notes"] = [next(it) for _ in scheme["notes"]]
        view["last_verified"] = scheme.get("last_verified")
    return view, ok
