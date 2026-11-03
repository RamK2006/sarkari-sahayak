"""Retrieval over the scheme catalog (BM25), with structured filters.

Retrieval is lexical and runs locally over the official scheme records, so every hit is a real record with
its source link. Records ingested from larger registries (see scripts/ingest_schemes.py) are searchable the
same way; those without machine-readable criteria are reported as "not assessed" rather than eligible.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache

from backend.services.catalog import get_catalog
from backend.services.eligibility import evaluate_scheme

_WORD = re.compile(r"[a-z0-9]+")
_FIELD_WEIGHTS = (("name", 3), ("categories", 2), ("summary", 1), ("benefits", 1), ("ministry", 1), ("documents", 1))


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _doc_tokens(s: dict) -> list[str]:
    out: list[str] = []
    for field, weight in _FIELD_WEIGHTS:
        value = s.get(field, "")
        text = " ".join(value) if isinstance(value, list) else str(value)
        out += _tokens(text) * weight
    return out


class Index:
    def __init__(self, schemes: list[dict]) -> None:
        self.schemes = schemes
        self.docs = [Counter(_doc_tokens(s)) for s in schemes]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = (sum(self.lengths) / len(self.lengths)) if self.lengths else 1.0
        self.df: Counter[str] = Counter()
        for d in self.docs:
            self.df.update(d.keys())

    def score(self, query: str) -> list[float]:
        n, k1, b = len(self.schemes), 1.5, 0.75
        terms = _tokens(query)
        scores = []
        for d, length in zip(self.docs, self.lengths):
            s = 0.0
            for t in terms:
                f = d.get(t, 0)
                if not f:
                    continue
                idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * length / self.avg))
            scores.append(s)
        return scores


@lru_cache(maxsize=1)
def _index() -> Index:
    return Index(get_catalog().all())


def in_state(scheme: dict, state: str | None) -> bool:
    states = scheme.get("states") or ["central"]
    return not state or "central" in states or state in states


def search(query: str = "", *, filters: dict | None = None, state: str | None = None, limit: int = 20) -> list[dict]:
    """Return [{scheme, score, evaluation}] ranked by relevance. `filters` is a partial citizen profile;
    schemes it rules out are dropped."""
    idx = _index()
    scores = idx.score(query) if query.strip() else [0.0] * len(idx.schemes)
    hits = []
    for scheme, score in zip(idx.schemes, scores):
        if query.strip() and score <= 0:
            continue
        if not in_state(scheme, state):
            continue
        ev = evaluate_scheme(filters or {}, set(), scheme)
        if filters and ev["status"] == "not_eligible":
            continue
        hits.append({"scheme": scheme, "score": score, "evaluation": ev})
    hits.sort(key=lambda h: -h["score"])
    return hits[:limit]
