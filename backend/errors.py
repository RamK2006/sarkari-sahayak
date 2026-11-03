"""API errors carry a stable machine-readable code; the frontend renders the localized message."""

from __future__ import annotations

from fastapi import HTTPException


def api_error(status: int, code: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code})
