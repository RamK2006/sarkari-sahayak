"""
Sarkari Sahayak — Government Welfare Scheme Discovery Assistant
Main Streamlit application.

Run with: streamlit run app.py
"""

from __future__ import annotations

import json
import re
import streamlit as st

from sarvam_client import SarvamClient
from eligibility import check_eligibility, load_schemes, format_results_for_llm
from prompts import SYSTEM_PROMPT, ELIGIBILITY_TOOL


# ── Page Config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sarkari Sahayak | सरकारी सहायक",
    page_icon="🏛️",
    layout="centered",
)

INITIAL_GREETING = (
    "नमस्ते! मैं आपका **सरकारी सहायक** हूँ। 🙏\n\n"
    "मैं आपको और आपके परिवार को केंद्र एवं राज्य सरकार की कल्याणकारी योजनाओं (जैसे पीएम-किसान, "
    "आयुष्मान भारत, आवास योजना, छात्रवृत्ति, पेंशन आदि) की पात्रता जांचने और आवेदन में मदद करता हूँ।\n\n"
    "कृपया अपनी स्थिति बताएं — जैसे आपकी **उम्र**, **कार्य (पेशा)**, **राज्य**, और **पारिवारिक आय**। "
    "आप बोलकर या लिखकर किसी भी भारतीय भाषा में बात कर सकते हैं।"
)


# ── Session State Init ────────────────────────────────────────────────
def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": INITIAL_GREETING}
        ]
    if "api_messages" not in st.session_state:
        st.session_state.api_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": INITIAL_GREETING}
        ]
    if "client" not in st.session_state:
        try:
            st.session_state.client = SarvamClient()
        except RuntimeError as e:
            st.error(str(e))
            st.stop()
    if "schemes" not in st.session_state:
        st.session_state.schemes = load_schemes()
    if "detected_lang" not in st.session_state:
        st.session_state.detected_lang = "hi-IN"
    if "processed_audio_hashes" not in st.session_state:
        st.session_state.processed_audio_hashes = set()
    if "processed_docs" not in st.session_state:
        st.session_state.processed_docs = set()


init_session()
client: SarvamClient = st.session_state.client


# ── Header ────────────────────────────────────────────────────────────
st.title("🏛️ Sarkari Sahayak")
st.caption("सरकारी सहायक — Citizen Welfare Scheme Discovery (Powered by Sarvam AI)")


# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🎙️ Voice Assistant")
    st.caption("अपनी मातृभाषा में बोलें (Speak in Hindi, Tamil, Telugu, Marathi, etc.)")
    audio_input = st.audio_input("Record voice query", key="audio_recorder")

    st.divider()

    st.header("📄 Document Verification")
    st.caption("Upload document for automatic detail extraction (Aadhaar, BPL, etc.)")
    uploaded_doc = st.file_uploader(
        "Upload document (PDF / Image)",
        type=["pdf", "jpg", "jpeg", "png"],
        key="doc_uploader",
    )

    st.divider()

    st.header("ℹ️ About Sarkari Sahayak")
    st.markdown(
        "- 🛡️ **Verified Data:** Schemes verified against official guidelines\n"
        "- ⚖️ **Rule-Based:** No LLM-invented schemes or eligibility criteria\n"
        "- 🗣️ **Indian Languages:** Powered by Sarvam 105B & Mayura\n"
        "- 🔊 **Voice Support:** Saaras v4 (STT) + Bulbul v4 Flash (TTS)\n"
        "- 📄 **Doc AI:** Document extraction for quick verification"
    )

    if st.button("🔄 Start New Conversation", use_container_width=True):
        st.session_state.messages = [{"role": "assistant", "content": INITIAL_GREETING}]
        st.session_state.api_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": INITIAL_GREETING}
        ]
        st.session_state.detected_lang = "hi-IN"
        st.session_state.processed_audio_hashes = set()
        st.session_state.processed_docs = set()
        st.rerun()


# ── Helper: TTS Generation ───────────────────────────────────────────
def generate_speech(text: str) -> bytes | None:
    """Generate speech audio for the response using Bulbul v4 Flash."""
    try:
        # Strip markdown syntax and URLs for clean speech
        tts_text = re.sub(r'[*#_`\[\]()]', '', text)
        tts_text = re.sub(r'https?://\S+', '', tts_text)
        tts_text = re.sub(r'===+.*?===+', '', tts_text)
        # Keep speech concise for quick playback
        tts_text = tts_text.strip()
        if not tts_text:
            return None
        if len(tts_text) > 400:
            # Speak the first 2-3 sentences
            sentences = re.split(r'[\n।.\?!]', tts_text)
            tts_text = "। ".join([s.strip() for s in sentences[:3] if s.strip()]) + "।"

        lang = st.session_state.detected_lang
        supported = ["hi-IN", "bn-IN", "ta-IN", "te-IN", "mr-IN", "kn-IN",
                     "gu-IN", "pa-IN", "en-IN", "od-IN", "ml-IN"]
        if lang not in supported:
            lang = "hi-IN"

        return client.text_to_speech(tts_text, language_code=lang)
    except Exception:
        return None


# ── Helper: Get LLM response with tool handling ──────────────────────
def get_response(user_text: str) -> str:
    """Send user message to Sarvam 105B, handle eligibility tool calls, return final response."""

    # Add user message to API messages
    st.session_state.api_messages.append({"role": "user", "content": user_text})

    # Detect language on text input
    if len(user_text.strip()) > 8:
        try:
            detected = client.detect_language(user_text)
            if detected:
                st.session_state.detected_lang = detected
        except Exception:
            pass

    # Call Sarvam 105B with eligibility tool definition
    response = client.chat(
        messages=st.session_state.api_messages,
        tools=[ELIGIBILITY_TOOL],
        tool_choice="auto",
    )

    choice = response.choices[0]
    message = choice.message

    # Check if model invoked check_eligibility tool
    if message.tool_calls:
        # Add assistant message with tool calls to history
        st.session_state.api_messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ],
        })

        # Process each tool call
        for tool_call in message.tool_calls:
            if tool_call.function.name == "check_eligibility":
                try:
                    profile = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    profile = {}

                # Execute deterministic eligibility evaluation
                results = check_eligibility(profile, st.session_state.schemes)
                results_text = format_results_for_llm(results)

                # Add tool result to message chain
                st.session_state.api_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": results_text,
                })

        # Get final reasoned response from Sarvam 105B (must pass tools parameter)
        final_response = client.chat(
            messages=st.session_state.api_messages,
            tools=[ELIGIBILITY_TOOL],
        )
        final_text = final_response.choices[0].message.content or ""

        st.session_state.api_messages.append({
            "role": "assistant",
            "content": final_text,
        })
        return final_text

    else:
        # Normal conversational response without tool execution
        assistant_text = message.content or ""
        st.session_state.api_messages.append({
            "role": "assistant",
            "content": assistant_text,
        })
        return assistant_text


# ── Chat History Display ──────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🏛️" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])
        if "audio" in msg and msg["audio"]:
            st.audio(msg["audio"], format="audio/wav")


# ── Process Audio Input (Saaras v4) ───────────────────────────────────
voice_text = None
if audio_input is not None:
    audio_bytes = audio_input.read()
    audio_hash = hash(audio_bytes)
    if audio_hash not in st.session_state.processed_audio_hashes:
        st.session_state.processed_audio_hashes.add(audio_hash)
        with st.spinner("🎙️ Transcribing speech with Saaras v4..."):
            try:
                voice_text = client.speech_to_text(audio_bytes, filename="voice.wav")
                st.sidebar.success("Transcribed successfully!")
            except Exception as e:
                st.sidebar.error(f"Speech transcription error: {e}")


# ── Process Document Upload (Doc AI) ──────────────────────────────────
if uploaded_doc is not None:
    doc_key = f"{uploaded_doc.name}_{uploaded_doc.size}"
    if doc_key not in st.session_state.processed_docs:
        st.session_state.processed_docs.add(doc_key)
        with st.spinner(f"📄 Analyzing {uploaded_doc.name} with Sarvam Doc AI..."):
            try:
                doc_bytes = uploaded_doc.read()
                doc_text = client.parse_document(doc_bytes, filename=uploaded_doc.name)
                doc_prompt = (
                    f"User uploaded an official document: '{uploaded_doc.name}'.\n"
                    f"Extracted document text:\n\"\"\"\n{doc_text}\n\"\"\"\n\n"
                    "Please extract any relevant eligibility parameters (identity, age, occupation, income, address) "
                    "from this document, acknowledge it warmly to the user, and check which welfare schemes apply."
                )
                voice_text = doc_prompt
                st.sidebar.success("Document analyzed!")
            except Exception as e:
                st.sidebar.error(f"Doc AI error: {e}")


# ── Handle Input & Response ───────────────────────────────────────────
chat_text = st.chat_input("अपनी स्थिति बताएं... / Type your situation or query here...")
active_input = voice_text or chat_text

if active_input:
    # Render user query in chat
    with st.chat_message("user", avatar="👤"):
        st.markdown(active_input)
    st.session_state.messages.append({"role": "user", "content": active_input})

    # Render assistant response
    with st.chat_message("assistant", avatar="🏛️"):
        with st.spinner("Evaluating eligibility against official rules..."):
            reply = get_response(active_input)
        st.markdown(reply)

        # Generate audio playback via Bulbul v4 Flash
        speech_bytes = generate_speech(reply)
        if speech_bytes:
            st.audio(speech_bytes, format="audio/wav")

    # Store in history
    msg_entry = {"role": "assistant", "content": reply}
    if speech_bytes:
        msg_entry["audio"] = speech_bytes
    st.session_state.messages.append(msg_entry)
