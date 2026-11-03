from fastapi import APIRouter

from backend.config import get_settings
from backend.services.catalog import get_catalog

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@router.get("/readyz")
def readyz() -> dict:
    configured = bool(get_settings().SARVAM_API_KEY)
    return {"status": "ok" if configured else "degraded", "sarvam_configured": configured}


@router.get("/api/meta")
def meta() -> dict:
    return {"scheme_count": len(get_catalog().all())}
