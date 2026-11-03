"""Government scheme assistant API."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.routes import assistant, meta, schemes
from backend.services.sarvam_client import SarvamUnavailable

settings = get_settings()
logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI(title="Scheme Assistant API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Per-client sliding-window limit on the endpoints that call Sarvam.
_LIMITED = ("/api/chat", "/api/translate", "/api/voice/", "/api/documents/", "/api/guide/")
_WINDOW, _MAX_CALLS = 60.0, 60
_hits: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.startswith(_LIMITED):
        forwarded = request.headers.get("x-forwarded-for")
        client = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        now = time.monotonic()
        q = _hits[client]
        while q and now - q[0] > _WINDOW:
            q.popleft()
        if len(q) >= _MAX_CALLS:
            return JSONResponse(status_code=429, content={"detail": {"code": "rate_limited"}})
        q.append(now)
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, __: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": {"code": "invalid_value"}})


@app.exception_handler(SarvamUnavailable)
async def sarvam_error(_: Request, __: SarvamUnavailable):
    return JSONResponse(status_code=503, content={"detail": {"code": "service_unavailable"}})


app.include_router(meta.router)
app.include_router(schemes.router)
app.include_router(assistant.router)
