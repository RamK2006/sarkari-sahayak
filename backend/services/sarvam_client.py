"""Thin wrapper over the Sarvam SDK: chat, translation, speech-to-text and text-to-speech."""

from __future__ import annotations

import base64
import logging
import threading
import time
from functools import lru_cache
from typing import Any

from sarvamai import SarvamAI

from backend.config import bcp47, get_settings

log = logging.getLogger(__name__)

# At most this many translate calls at once; Sarvam rate-limits bursts.
_translate_slots = threading.Semaphore(3)

# Conversational speakers per language (Bulbul v4). Falls back to a language-neutral voice.
_SPEAKERS = {
    "en": "simran_en_conversation",
    "hi": "ritu_hi_conversation",
    "bn": "roopa_bn_conversational",
    "ta": "gokul_ta_narration",
    "te": "kavitha_te_conversation",
    "mr": "ishita_mr_conversational",
    "kn": "chaitra_kn_conversation",
    "gu": "pooja_gu_conversational",
    "pa": "anand_pa_conversation",
}
# Odia and Malayalam have no Bulbul v4-flash voices; they use Bulbul v3.
_V3_LANGUAGES = {"od", "ml"}
_V3_SPEAKER = "ritu"

_AUDIO_CODECS = {
    "audio/webm": "webm", "video/webm": "webm", "audio/ogg": "ogg", "audio/opus": "opus",
    "audio/wav": "wav", "audio/x-wav": "wav", "audio/wave": "wav", "audio/mpeg": "mp3",
    "audio/mp3": "mp3", "audio/mp4": "mp4", "audio/aac": "aac", "audio/flac": "flac",
}


class SarvamUnavailable(RuntimeError):
    """Raised when a Sarvam call fails; callers translate this into an honest error response."""


class SarvamClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.SARVAM_API_KEY:
            raise SarvamUnavailable("SARVAM_API_KEY is not configured")
        self._settings = settings
        self._client = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY, timeout=40)

    # ── Chat ────────────────────────────────────────────────────────────
    def chat(self, messages: list[dict[str, Any]], tools: list[dict] | None = None, tool_choice: str | None = None):
        kwargs: dict[str, Any] = {"messages": messages, "model": self._settings.CHAT_MODEL, "temperature": 0.3}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice or "auto"
        try:
            return self._client.chat.completions(**kwargs).choices[0].message
        except Exception as exc:  # noqa: BLE001 - SDK raises a variety of error types
            log.warning("Sarvam chat failed: %.200s", exc)
            raise SarvamUnavailable("chat") from exc

    # ── Translation ─────────────────────────────────────────────────────
    def translate(self, text: str, target: str, source: str = "en") -> str:
        """Translate text. `source="auto"` (language detection) is only supported by Mayura, so it routes there;
        everything else uses Sarvam-Translate. Rate-limit responses are retried with backoff."""
        if not text.strip() or target == source:
            return text
        model = "mayura:v1" if source == "auto" else self._settings.TRANSLATE_MODEL
        last: Exception | None = None
        for attempt in range(4):
            try:
                with _translate_slots:
                    resp = self._client.text.translate(
                        input=text,
                        source_language_code="auto" if source == "auto" else bcp47(source),
                        target_language_code=bcp47(target),
                        model=model,
                        mode="formal",
                    )
                return resp.translated_text
            except Exception as exc:  # noqa: BLE001
                last = exc
                if "429" not in str(exc) and "rate" not in str(exc).lower():
                    break
                time.sleep(1.5 * (2**attempt))
        log.warning("Sarvam translate failed (%s -> %s): %.200s", source, target, last)
        raise SarvamUnavailable("translate") from last

    # ── Speech ──────────────────────────────────────────────────────────
    def speech_to_text(self, audio: bytes, language: str, content_type: str = "audio/webm") -> str:
        codec = _AUDIO_CODECS.get(content_type.split(";")[0].strip().lower(), "webm")
        try:
            resp = self._client.speech_to_text.transcribe(
                file=("recording", audio, content_type.split(";")[0]),
                model=self._settings.STT_MODEL,
                mode="transcribe",
                language_code=bcp47(language),
                input_audio_codec=codec,
            )
            return (resp.transcript or "").strip()
        except Exception as exc:  # noqa: BLE001
            log.warning("Sarvam STT failed: %.200s", exc)
            raise SarvamUnavailable("stt") from exc

    def text_to_speech(self, text: str, language: str) -> bytes:
        if language in _V3_LANGUAGES:
            model, speaker = "bulbul:v3", _V3_SPEAKER
        else:
            model, speaker = self._settings.TTS_MODEL, _SPEAKERS.get(language, "simran_en_conversation")
        try:
            resp = self._client.text_to_speech.convert(
                text=text,
                language_code=bcp47(language),
                model=model,
                speaker=speaker,
                output_audio_codec="mp3",
            )
            return b"".join(base64.b64decode(a) for a in resp.audios)
        except Exception as exc:  # noqa: BLE001
            log.warning("Sarvam TTS failed: %.200s", exc)
            raise SarvamUnavailable("tts") from exc


@lru_cache(maxsize=1)
def get_sarvam() -> SarvamClient:
    return SarvamClient()
