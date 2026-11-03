"""Request models. Validation lives here; business rules live in services."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.config import LANGUAGE_BY_CODE


class VaultItem(BaseModel):
    id: str = Field(max_length=40)
    doc_type: str = Field(max_length=40)
    expiry_date: str | None = Field(None, max_length=10)


class Citizen(BaseModel):
    """Client-held state. The backend is stateless; nothing is stored server-side."""

    language: str = Field("en", max_length=5)
    profile: dict[str, Any] = Field(default_factory=dict)
    skipped: list[str] = Field(default_factory=list, max_length=40)
    vault: list[VaultItem] = Field(default_factory=list, max_length=60)


class AnswerRequest(Citizen):
    field: str = Field(max_length=40)
    value: Any = None  # null means the citizen skipped this question


class ChatTurn(BaseModel):
    role: str = Field(max_length=12)
    content: str = Field(max_length=2000)


class ChatRequest(Citizen):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)


class TranslateRequest(BaseModel):
    language: str = Field(max_length=5)
    source: str = Field("auto", max_length=5)  # "en" for interface strings, "auto" for free text
    texts: list[str] = Field(max_length=80)


class SpeakRequest(BaseModel):
    language: str = Field(max_length=5)
    text: str = Field(min_length=1, max_length=4000)


class SearchRequest(BaseModel):
    language: str = Field("en", max_length=5)
    query: str = Field("", max_length=200)
    state: str | None = Field(None, max_length=60)
    filters: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(20, ge=1, le=50)


class GuidePlanRequest(BaseModel):
    language: str = Field("en", max_length=5)
    goal: str = Field("", max_length=300)
    scheme_id: str | None = Field(None, max_length=60)
    citizen_data: dict[str, Any] = Field(default_factory=dict)


class GuideClassifyRequest(BaseModel):
    language: str = Field("en", max_length=5)
    text: str = Field(min_length=1, max_length=300)


def valid_language(code: str) -> str:
    return code if code in LANGUAGE_BY_CODE else "en"
