"""Request models. Validation lives here; business rules live in services."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.config import LANGUAGE_BY_CODE


class Citizen(BaseModel):
    """Client-held profile state. The backend is stateless; nothing is stored server-side."""

    language: str = Field("en", max_length=5)
    profile: dict[str, Any] = Field(default_factory=dict)
    skipped: list[str] = Field(default_factory=list, max_length=40)


class AnswerRequest(Citizen):
    field: str = Field(max_length=40)
    value: Any = None  # null means the citizen skipped this question


class ChatTurn(BaseModel):
    role: str = Field(max_length=12)
    content: str = Field(max_length=2000)


class ChatRequest(Citizen):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)
    asking: str | None = Field(None, max_length=40)  # field of the question currently on screen


class TranslateRequest(BaseModel):
    language: str = Field(max_length=5)
    texts: list[str] = Field(max_length=30)


class SpeakRequest(BaseModel):
    language: str = Field(max_length=5)
    text: str = Field(min_length=1, max_length=4000)


def valid_language(code: str) -> str:
    return code if code in LANGUAGE_BY_CODE else "en"
