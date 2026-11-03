"""Scheme catalog access.

`SchemeSource` is the integration boundary: swap `JsonSchemeSource` for an implementation backed by
an authoritative registry (a ministry feed or a database) without touching callers.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from backend.config import get_settings


class SchemeSource(Protocol):
    def all(self) -> list[dict]: ...

    def get(self, scheme_id: str) -> dict | None: ...


class JsonSchemeSource:
    def __init__(self, path) -> None:
        with open(path, encoding="utf-8") as fh:
            self._schemes: list[dict] = json.load(fh)
        extra = Path(path).with_name("schemes_extra.json")
        if extra.exists():
            known = {s["id"] for s in self._schemes}
            self._schemes += [s for s in json.loads(extra.read_text(encoding="utf-8")) if s["id"] not in known]
        self._by_id = {s["id"]: s for s in self._schemes}

    def all(self) -> list[dict]:
        return self._schemes

    def get(self, scheme_id: str) -> dict | None:
        return self._by_id.get(scheme_id)


@lru_cache(maxsize=1)
def get_catalog() -> SchemeSource:
    return JsonSchemeSource(get_settings().SCHEMES_PATH)
