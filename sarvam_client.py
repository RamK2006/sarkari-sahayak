"""Sarvam AI client wrapper for Sarkari Sahayak."""

from __future__ import annotations

import os
import io
from typing import List, Dict, Optional, Any

from dotenv import load_dotenv
from sarvamai import SarvamAI


# Language code to TTS speaker mapping (good default voices)
_DEFAULT_SPEAKERS = {
    "hi-IN": "ritu_hi_conversation",
    "bn-IN": "roopa_bn_conversational",
    "ta-IN": "gokul_ta_narration",
    "te-IN": "kavitha_te_conversation",
    "mr-IN": "ishita_mr_conversational",
    "kn-IN": "chaitra_kn_conversation",
    "gu-IN": "pooja_gu_conversational",
    "pa-IN": "anand_pa_conversation",
    "en-IN": "simran_en_conversation",
    "od-IN": "anushka",
    "ml-IN": "anushka",
}


class SarvamClient:
    """Thin wrapper around the Sarvam AI SDK."""

    def __init__(self):
        load_dotenv()
        api_key = os.environ.get("SARVAM_API_KEY")
        if not api_key:
            raise RuntimeError(
                "SARVAM_API_KEY not found in environment. "
                "Please set it in your .env file."
            )
        self.client = SarvamAI(api_subscription_key=api_key)

    # ── Chat ──────────────────────────────────────────────────────────
    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Any] = None,
    ):
        """Send a chat completion request to Sarvam 105B Conversations."""
        kwargs: Dict[str, Any] = {
            "messages": messages,
            "model": "sarvam-105b-conversations",
        }
        if tools:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
        return self.client.chat.completions(**kwargs)

    # ── Translation ───────────────────────────────────────────────────
    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "hi-IN",
    ) -> str:
        """Translate text between Indian languages using Mayura."""
        resp = self.client.text.translate(
            input=text,
            source_language_code=source_lang,
            target_language_code=target_lang,
            model="mayura:v1",
        )
        return resp.translated_text

    # ── Language Detection ────────────────────────────────────────────
    def detect_language(self, text: str) -> str:
        """Detect the language of the input text. Returns language code like 'hi-IN'."""
        resp = self.client.text.identify_language(input=text)
        return resp.language_code

    # ── Speech-to-Text ────────────────────────────────────────────────
    def speech_to_text(self, audio_bytes: bytes, language_code: str = "unknown", filename: str = "audio.wav") -> str:
        """Transcribe audio to text using Saaras v4."""
        resp = self.client.speech_to_text.transcribe(
            file=(filename, audio_bytes, "audio/wav"),
            model="saaras:v4",
            language_code=language_code,
        )
        return resp.transcript

    # ── Text-to-Speech ────────────────────────────────────────────────
    def text_to_speech(
        self,
        text: str,
        language_code: str = "hi-IN",
        speaker: Optional[str] = None,
    ) -> bytes:
        """Convert text to speech using Bulbul v4 Flash. Returns audio bytes."""
        if speaker is None:
            speaker = _DEFAULT_SPEAKERS.get(language_code, "anushka")
        chunks = self.client.text_to_speech.convert_stream(
            text=text,
            language_code=language_code,
            model="bulbul:v4-flash",
            speaker=speaker,
        )
        return b"".join(chunks)

    # ── Document AI ───────────────────────────────────────────────────
    def parse_document(self, file_bytes: bytes, filename: str = "document.pdf") -> str:
        """Parse a document using Doc AI and return extracted text."""
        import time

        mime = "application/pdf"
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            mime = "image/jpeg"

        # Start parse job
        resp = self.client.doc_ai.parse(
            file=[(filename, file_bytes, mime)],
        )
        job_id = resp.job_id

        # Poll for completion (max 60 seconds)
        for _ in range(30):
            status = self.client.doc_ai.get_status(job_id)
            if status.status == "completed":
                break
            time.sleep(2)
        else:
            raise TimeoutError(f"Document parsing timed out for job {job_id}")

        # Get results
        results = self.client.doc_ai.get_results(job_id, format="md")
        return results.result if hasattr(results, "result") else str(results)
