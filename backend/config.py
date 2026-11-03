"""Application configuration, read from the environment (and .env in development)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

# Language catalogue: the 22 scheduled languages plus English. `tts` marks languages Sarvam can speak;
# the rest are fully supported in text, translation and speech recognition.
_L = [
    ("en", "en-IN", "English", "English", True), ("hi", "hi-IN", "हिन्दी", "Hindi", True),
    ("bn", "bn-IN", "বাংলা", "Bengali", True), ("te", "te-IN", "తెలుగు", "Telugu", True),
    ("mr", "mr-IN", "मराठी", "Marathi", True), ("ta", "ta-IN", "தமிழ்", "Tamil", True),
    ("gu", "gu-IN", "ગુજરાતી", "Gujarati", True), ("kn", "kn-IN", "ಕನ್ನಡ", "Kannada", True),
    ("ml", "ml-IN", "മലയാളം", "Malayalam", True), ("pa", "pa-IN", "ਪੰਜਾਬੀ", "Punjabi", True),
    ("od", "od-IN", "ଓଡ଼ିଆ", "Odia", True), ("as", "as-IN", "অসমীয়া", "Assamese", False),
    ("ur", "ur-IN", "اردو", "Urdu", False), ("ne", "ne-IN", "नेपाली", "Nepali", False),
    ("kok", "kok-IN", "कोंकणी", "Konkani", False), ("mai", "mai-IN", "मैथिली", "Maithili", False),
    ("doi", "doi-IN", "डोगरी", "Dogri", False), ("sd", "sd-IN", "سنڌي", "Sindhi", False),
    ("ks", "ks-IN", "کٲشُر", "Kashmiri", False), ("sa", "sa-IN", "संस्कृतम्", "Sanskrit", False),
    ("sat", "sat-IN", "ᱥᱟᱱᱛᱟᱲᱤ", "Santali", False), ("mni", "mni-IN", "মৈতৈলোন্", "Manipuri", False),
    ("brx", "brx-IN", "बर'", "Bodo", False),
]
LANGUAGES: list[dict] = [
    {"code": c, "bcp47": b, "name": n, "english": e, "tts": t} for c, b, n, e, t in _L
]
LANGUAGE_BY_CODE = {l["code"]: l for l in LANGUAGES}
LANGUAGE_ENGLISH_NAMES = {l["code"]: l["english"] for l in LANGUAGES}


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

    DOC_TYPES_PATH: Path = DATA_DIR / "doc_types.json"
    STATES_PATH: Path = DATA_DIR / "states.json"
    EXPIRING_SOON_DAYS: int = int(os.environ.get("EXPIRING_SOON_DAYS", "30"))
    UPCOMING_DAYS: int = int(os.environ.get("UPCOMING_DAYS", "90"))
    MAX_DOC_BYTES: int = 8 * 1024 * 1024
    MAX_AUDIO_BYTES: int = 10 * 1024 * 1024
    MAX_TTS_CHARS: int = 1500


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def bcp47(code: str) -> str:
    return LANGUAGE_BY_CODE.get(code, LANGUAGE_BY_CODE["en"])["bcp47"]
