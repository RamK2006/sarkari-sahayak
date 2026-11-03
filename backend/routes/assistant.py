"""Chat, translation and voice endpoints."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, Response, UploadFile

from backend.config import get_settings
from backend.errors import api_error
from backend.routes.schemes import intake_state_for
from backend.schemas import ChatRequest, SpeakRequest, TranslateRequest, valid_language
from backend.services import assistant, intake
from backend.services.sarvam_client import SarvamUnavailable, get_sarvam
from backend.services.translation import translate_many

router = APIRouter(prefix="/api", tags=["assistant"])


@router.post("/chat")
def chat(body: ChatRequest) -> dict:
    profile = intake.clean_profile(body.profile)
    skipped = intake.clean_skipped(body.skipped)
    try:
        out = assistant.respond(
            valid_language(body.language), body.message, profile,
            [t.model_dump() for t in body.history], body.asking,
        )
    except SarvamUnavailable:
        raise api_error(503, "service_unavailable") from None
    profile.update(out["applied"])
    skipped -= set(out["applied"])
    return {"reply": out["reply"], "applied": out["applied"], **intake_state_for(profile, skipped)}


@router.post("/translate")
def translate(body: TranslateRequest) -> dict:
    texts, ok = translate_many(body.texts, valid_language(body.language), source="auto")
    if not ok:
        raise api_error(503, "service_unavailable")
    return {"texts": texts}


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
    text = body.text[: get_settings().MAX_TTS_CHARS]
    try:
        audio = get_sarvam().text_to_speech(text, valid_language(body.language))
    except SarvamUnavailable:
        raise api_error(503, "service_unavailable") from None
    return Response(content=audio, media_type="audio/mpeg", headers={"Cache-Control": "no-store"})
