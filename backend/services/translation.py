"""Translation with a persistent cache, backed by Sarvam translation.

Scheme and interface text is authored in English and translated on demand. Results are cached in memory and on
disk (backend/data/translations/<lang>.json). Strings are packed into batches (one Sarvam call per ~900
characters) to stay inside rate limits, with a per-string fallback if a batch comes back misaligned. Failures are
never hidden: callers receive per-string `ok` flags and the untranslated source text for failed items.
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
_MAX_BATCH_ITEMS = 12
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
            _path(lang).write_text(json.dumps(_caches[lang], ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    except OSError as exc:  # read-only filesystems are fine; the in-memory cache still works
        log.info("Could not persist translation cache: %s", exc)


def _split_long(text: str) -> list[str]:
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


def _translate_single(text: str, lang: str, source: str) -> str:
    client = get_sarvam()
    return " ".join(client.translate(part, lang, source) for part in _split_long(text))


def _translate_batch(batch: list[str], lang: str, source: str) -> list[str]:
    """One call for several short strings (newline separated); falls back to one call each if misaligned."""
    if len(batch) == 1 or any("\n" in t for t in batch):
        return [_translate_single(t, lang, source) for t in batch]
    out = get_sarvam().translate("\n".join(batch), lang, source).split("\n")
    if len(out) == len(batch) and all(o.strip() for o in out):
        return [o.strip() for o in out]
    return [_translate_single(t, lang, source) for t in batch]


def _batches(items: list[tuple[int, str]]) -> list[list[tuple[int, str]]]:
    batches, current, size = [], [], 0
    for idx, text in items:
        if current and (size + len(text) > _MAX_CHARS or len(current) >= _MAX_BATCH_ITEMS or len(text) > 400):
            batches.append(current)
            current, size = [], 0
        current.append((idx, text))
        size += len(text)
        if len(text) > 400:
            batches.append(current)
            current, size = [], 0
    if current:
        batches.append(current)
    return batches


def translate_many_detailed(texts: list[str], lang: str, source: str = "en") -> tuple[list[str], list[bool]]:
    """Translate several strings. Returns (texts, ok flags); failed items keep their source text."""
    n = len(texts)
    if n == 0 or lang == source:
        return list(texts), [True] * n
    if lang not in LANGUAGE_BY_CODE:
        return list(texts), [False] * n
    out, ok = list(texts), [False] * n
    cache = _cache(lang)
    todo: list[tuple[int, str]] = []
    for i, text in enumerate(texts):
        if not text.strip():
            ok[i] = True
        elif (k := _key(text)) in cache:
            out[i], ok[i] = cache[k], True
        else:
            todo.append((i, text))

    def run(batch: list[tuple[int, str]]) -> None:
        try:
            result = _translate_batch([t for _, t in batch], lang, source)
        except SarvamUnavailable:
            return
        for (i, text), tr in zip(batch, result):
            out[i], ok[i] = tr, True
            cache[_key(text)] = tr

    if todo:
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(run, _batches(todo)))
        _persist(lang)
    return out, ok


def translate_many(texts: list[str], lang: str, source: str = "en") -> tuple[list[str], bool]:
    out, ok = translate_many_detailed(texts, lang, source)
    return out, all(ok)


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
