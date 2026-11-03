"""Application configuration, read from the environment (and .env in development)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

# Language catalogue. `bcp47` is the code Sarvam APIs expect.
LANGUAGES: list[dict[str, str]] = [
    {"code": "en", "bcp47": "en-IN", "name": "English"},
    {"code": "hi", "bcp47": "hi-IN", "name": "हिन्दी"},
    {"code": "bn", "bcp47": "bn-IN", "name": "বাংলা"},
    {"code": "te", "bcp47": "te-IN", "name": "తెలుగు"},
    {"code": "mr", "bcp47": "mr-IN", "name": "मराठी"},
    {"code": "ta", "bcp47": "ta-IN", "name": "தமிழ்"},
    {"code": "gu", "bcp47": "gu-IN", "name": "ગુજરાતી"},
    {"code": "kn", "bcp47": "kn-IN", "name": "ಕನ್ನಡ"},
    {"code": "ml", "bcp47": "ml-IN", "name": "മലയാളം"},
    {"code": "pa", "bcp47": "pa-IN", "name": "ਪੰਜਾਬੀ"},
    {"code": "od", "bcp47": "od-IN", "name": "ଓଡ଼ିଆ"},
]
LANGUAGE_BY_CODE = {l["code"]: l for l in LANGUAGES}
# English names used when instructing the language model.
LANGUAGE_ENGLISH_NAMES = {
    "en": "English", "hi": "Hindi", "bn": "Bengali", "te": "Telugu", "mr": "Marathi",
    "ta": "Tamil", "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam",
    "pa": "Punjabi", "od": "Odia",
}


class Settings:
    SARVAM_API_KEY: str = os.environ.get("SARVAM_API_KEY", "")
    CORS_ORIGINS: list[str] = [
        o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()
    ]
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

    DATA_DIR: Path = Path(__file__).resolve().parent / "data"
    SCHEMES_PATH: Path = DATA_DIR / "schemes.json"
    TRANSLATIONS_DIR: Path = DATA_DIR / "translations"

    CHAT_MODEL: str = "sarvam-105b-conversations"
    TRANSLATE_MODEL: str = "sarvam-translate:v1"
    STT_MODEL: str = "saaras:v4"
    TTS_MODEL: str = "bulbul:v4-flash"

    MAX_AUDIO_BYTES: int = 10 * 1024 * 1024
    MAX_TTS_CHARS: int = 1500


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def bcp47(code: str) -> str:
    return LANGUAGE_BY_CODE.get(code, LANGUAGE_BY_CODE["en"])["bcp47"]
