"""Chat, translation, voice, document and guide endpoints."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, Response, UploadFile

from backend.config import LANGUAGE_BY_CODE, get_settings
from backend.errors import api_error
from backend.schemas import (
    ChatRequest, GuideClassifyRequest, GuidePlanRequest, SpeakRequest, TranslateRequest, valid_language,
)
from backend.services import assistant, documents, guide, intake
from backend.services.catalog import get_catalog
from backend.services.eligibility import evaluate_scheme
from backend.services.sarvam_client import SarvamUnavailable, get_sarvam
from backend.services.translation import localize_scheme, translate_many_detailed

router = APIRouter(prefix="/api", tags=["assistant"])


@router.post("/chat")
def chat(body: ChatRequest) -> dict:
    profile = intake.clean_profile(body.profile)
    skipped = intake.clean_skipped(body.skipped)
    lang = valid_language(body.language)
    try:
        out = assistant.respond(
            lang, body.message, profile, skipped,
            [t.model_dump() for t in body.history], [v.model_dump() for v in body.vault],
        )
    except SarvamUnavailable:
        raise api_error(503, "service_unavailable") from None
    profile.update(out["applied"])
    skipped -= set(out["applied"])
    cards, translated = [], True
    for sid in out["schemes"][:4]:
        scheme = get_catalog().get(sid)
        if scheme:
            view, ok = localize_scheme(scheme, lang)
            translated = translated and ok
            cards.append({"scheme": view, "status": evaluate_scheme(profile, skipped, scheme)["status"]})
    return {
        "reply": out["reply"], "mood": out["mood"], "gesture": out["gesture"], "guide": out["guide"],
        "upload": out["upload"], "applied": out["applied"], "profile": profile, "skipped": sorted(skipped),
        "schemes": cards, "translated": translated,
    }


@router.post("/translate")
def translate(body: TranslateRequest) -> dict:
    """Per-string results: a partial failure still returns what was translated, flagged in `ok`."""
    source = body.source if body.source == "auto" or body.source in LANGUAGE_BY_CODE else "auto"
    texts, ok = translate_many_detailed(body.texts, valid_language(body.language), source)
    if body.texts and not any(ok):
        raise api_error(503, "service_unavailable")
    return {"texts": texts, "ok": ok}


@router.post("/voice/stt")
async def speech_to_text(audio: UploadFile = File(...), language: str = Form("en")) -> dict:
    limit = get_settings().MAX_AUDIO_BYTES
    data = await audio.read(limit + 1)
    if not data:
        raise api_error(422, "empty_audio")
    if len(data) > limit:
        raise api_error(413, "audio_too_large")
    try:
        transcript = get_sarvam().speech_to_text(data, valid_language(language), audio.content_type or "audio/webm")
    except SarvamUnavailable:
        raise api_error(503, "service_unavailable") from None
    return {"transcript": transcript}


@router.post("/voice/tts")
def text_to_speech(body: SpeakRequest) -> Response:
    lang = valid_language(body.language)
    if not LANGUAGE_BY_CODE[lang]["tts"]:
        raise api_error(422, "tts_unsupported")
    try:
        audio = get_sarvam().text_to_speech(body.text[: get_settings().MAX_TTS_CHARS], lang)
    except SarvamUnavailable:
        raise api_error(503, "service_unavailable") from None
    return Response(content=audio, media_type="audio/mpeg", headers={"Cache-Control": "no-store"})


@router.post("/documents/analyze")
async def analyze_document(file: UploadFile = File(...)) -> dict:
    mime = documents.mime_for(file.filename or "")
    if mime is None:
        raise api_error(415, "unsupported_file")
    limit = get_settings().MAX_DOC_BYTES
    data = await file.read(limit + 1)
    if not data:
        raise api_error(422, "empty_file")
    if len(data) > limit:
        raise api_error(413, "file_too_large")
    try:
        return documents.analyze(data, file.filename or "document", mime)
    except SarvamUnavailable:
        raise api_error(503, "service_unavailable") from None


@router.post("/guide/plan")
def guide_plan(body: GuidePlanRequest) -> dict:
    if not body.goal.strip() and not body.scheme_id:
        raise api_error(422, "invalid_value")
    try:
        return guide.plan(body.goal, valid_language(body.language), body.scheme_id, body.citizen_data)
    except SarvamUnavailable:
        raise api_error(503, "service_unavailable") from None


@router.post("/guide/classify")
def guide_classify(body: GuideClassifyRequest) -> dict:
    try:
        return {"intent": guide.classify(body.text, valid_language(body.language))}
    except SarvamUnavailable:
        raise api_error(503, "service_unavailable") from None
