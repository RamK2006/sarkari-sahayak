"""
Sarkari Sahayak — Simplified Citizen Welfare Assistant
Designed for ordinary citizens with limited digital and literacy skills.

Powered by Sarvam AI:
- Sarvam 105B Conversations (Conversational Reasoning & Tool Calling)
- Saaras v4 (Speech-to-Text in Indian Languages)
- Bulbul v4 Flash (Native Text-to-Speech)
- Sarvam Doc AI (Document Information Extraction)
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Any
import streamlit as st

from sarvam_client import SarvamClient
from eligibility import check_eligibility, load_schemes, format_results_for_llm
from prompts import SYSTEM_PROMPT, ELIGIBILITY_TOOL


# ── Page Config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sarkari Sahayak | सरकारी सहायक",
    page_icon="🇮🇳",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Clean, High-Contrast Accessible Styling ───────────────────────────
st.markdown("""
<style>
    /* Clean accessible typography */
    .main-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a365d;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        font-size: 1.1rem;
        color: #4a5568;
        margin-bottom: 1.5rem;
    }
    .voice-box {
        background-color: #f7fafc;
        border: 2px solid #cbd5e0;
        border-radius: 16px;
        padding: 1.2rem;
        text-align: center;
        margin: 1.5rem 0;
    }
    .voice-instruction {
        font-size: 1.15rem;
        font-weight: 600;
        color: #2b6cb0;
        margin-bottom: 0.6rem;
    }
    .context-card {
        background-color: #ebf8ff;
        border-left: 5px solid #3182ce;
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
        margin: 1rem 0;
        font-size: 0.95rem;
    }
    .scheme-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)

# ── Supported Languages ───────────────────────────────────────────────
LANGUAGES = {
    "hi-IN": {"name": "हिन्दी (Hindi)", "short": "Hindi", "greeting": "नमस्ते! मैं आपका सरकारी सहायक हूँ। आप बोलकर या लिखकर अपनी स्थिति बता सकते हैं, या अपना कोई कागज़ (जैसे आधार कार्ड, राशन कार्ड) दिखा सकते हैं। मैं आपको बताऊंगा कि आपको सरकार से क्या सहायता मिल सकती है।"},
    "en-IN": {"name": "English", "short": "English", "greeting": "Hello! I am your Sarkari Sahayak. You can speak or type your situation, or upload an official document (like Aadhaar or Ration card). I will help you find the government welfare schemes you qualify for."},
    "bn-IN": {"name": "বাংলা (Bengali)", "short": "Bengali", "greeting": "নমস্কার! আমি আপনার সরকারি সহায়ক। আপনি মুখে বলে বা লিখে আপনার পরিস্থিতি জানাতে পারেন, অথবা আপনার আধার বা রেশন কার্ড আপলোড করতে পারেন।"},
    "ta-IN": {"name": "தமிழ் (Tamil)", "short": "Tamil", "greeting": "வணக்கம்! நான் உங்கள் அரசு உதவியாளர். நீங்கள் பேசியோ அல்லது எழுதியோ உங்கள் தேவையைத் தெரிவிக்கலாம் அல்லது உங்கள் ஆவணத்தைப் பதிவேற்றலாம்."},
    "te-IN": {"name": "తెలుగు (Telugu)", "short": "Telugu", "greeting": "నమస్కారం! నేను మీ సర్కారీ సహాయక్‌ని. మీరు మాట్లాడి లేదా టైప్ చేసి మీ వివరాలు చెప్పవచ్చు, లేదా మీ ఆధార్ లేదా రేషన్ కార్డును అప్‌లోడ్ చేయవచ్చు."},
    "mr-IN": {"name": "मराठी (Marathi)", "short": "Marathi", "greeting": "नमस्कार! मी तुमचा सरकारी सहाय्यक आहे. तुम्ही बोलून किंवा लिहून तुमची परिस्थिती सांगू शकता, किंवा आधार/रेशन कार्ड अपलोड करू शकता."},
    "gu-IN": {"name": "ગુજરાતી (Gujarati)", "short": "Gujarati", "greeting": "નમસ્તે! હું તમારો સરકારી સહાયક છું. તમે બોલીને કે લખીને તમારી માહિતી આપી શકો છો અથવા તમારા દસ્તાવેજ અપલોડ કરી શકો છો."},
    "kn-IN": {"name": "ಕನ್ನಡ (Kannada)", "short": "Kannada", "greeting": "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಸರ್ಕಾರಿ ಸಹಾಯಕ. ನೀವು ಮಾತನಾಡಿ ಅಥವಾ ಬರೆದು ನಿಮ್ಮ ವಿವರ ತಿಳಿಸಬಹುದು ಅಥವಾ ದಾಖಲೆಗಳನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಬಹುದು."},
    "pa-IN": {"name": "ਪੰਜਾਬੀ (Punjabi)", "short": "Punjabi", "greeting": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ ਸਰਕਾਰੀ ਸਹਾਇਕ ਹਾਂ। ਤੁਸੀਂ ਬੋਲ ਕੇ ਜਾਂ ਲਿਖ ਕੇ ਆਪਣੀ ਸਥਿਤੀ ਦੱਸ ਸਕਦੇ ਹੋ ਜਾਂ ਕੋਈ ਦਸਤਾਵੇਜ਼ ਅਪਲੋਡ ਕਰ ਸਕਦੇ ਹੋ।"},
    "od-IN": {"name": "ଓଡ଼ିଆ (Odia)", "short": "Odia", "greeting": "ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କର ସରକାରୀ ସହାୟକ। ଆପଣ କହି କିମ୍ବା ଲେଖି ଆପଣଙ୍କ ବିଷୟରେ ଜଣାଇପାରିବେ କିମ୍ବା କାଗଜପତ୍ର ଅପଲୋଡ଼ କରିପାରିବେ।"},
    "ml-IN": {"name": "മലയാളം (Malayalam)", "short": "Malayalam", "greeting": "നമസ്കാരം! ഞാൻ നിങ്ങളുടെ സർക്കാർ സഹായകനാണ്. നിങ്ങൾക്ക് സംസാരിച്ചോ ടൈപ്പ് ചെയ്തോ വിവരങ്ങൾ നൽകാം അല്ലെങ്കിൽ രേഖകൾ അപ്‌ലോഡ് ചെയ്യാം."},
}


# ── Session State Management ──────────────────────────────────────────
def init_session():
    if "selected_lang" not in st.session_state:
        st.session_state.selected_lang = "hi-IN"
    if "detected_lang" not in st.session_state:
        st.session_state.detected_lang = "hi-IN"
    if "schemes" not in st.session_state:
        st.session_state.schemes = load_schemes()
    if "client" not in st.session_state:
        try:
            st.session_state.client = SarvamClient()
        except Exception as e:
            st.error(f"Failed to connect to Sarvam AI: {e}")
            st.stop()

    # Citizen context extracted from uploaded documents
    if "citizen_context" not in st.session_state:
        st.session_state.citizen_context = {}  # e.g. {"name": "Ramesh", "age": 42, "state": "UP"}
    if "extracted_doc_text" not in st.session_state:
        st.session_state.extracted_doc_text = ""
    if "last_doc_name" not in st.session_state:
        st.session_state.last_doc_name = ""

    # Message history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": LANGUAGES[st.session_state.selected_lang]["greeting"]}
        ]
    if "api_messages" not in st.session_state:
        st.session_state.api_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": LANGUAGES[st.session_state.selected_lang]["greeting"]}
        ]
    if "processed_audio_hashes" not in st.session_state:
        st.session_state.processed_audio_hashes = set()
    if "processed_doc_hashes" not in st.session_state:
        st.session_state.processed_doc_hashes = set()


init_session()
client: SarvamClient = st.session_state.client


# ── Clean Top Navigation: Language Selection & Reset ──────────────────
col_top1, col_top2 = st.columns([3, 1])

with col_top1:
    selected_code = st.selectbox(
        "अपनी भाषा चुनें / Select Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda code: LANGUAGES[code]["name"],
        index=list(LANGUAGES.keys()).index(st.session_state.selected_lang),
        key="lang_select",
        label_visibility="collapsed",
    )
    if selected_code != st.session_state.selected_lang:
        st.session_state.selected_lang = selected_code
        st.session_state.detected_lang = selected_code
        greeting = LANGUAGES[selected_code]["greeting"]
        st.session_state.messages = [{"role": "assistant", "content": greeting}]
        st.session_state.api_messages = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nIMPORTANT: Respond in {LANGUAGES[selected_code]['short']}."},
            {"role": "assistant", "content": greeting}
        ]
        st.rerun()

with col_top2:
    if st.button("नया शुरू करें / Reset", use_container_width=True):
        greeting = LANGUAGES[st.session_state.selected_lang]["greeting"]
        st.session_state.messages = [{"role": "assistant", "content": greeting}]
        st.session_state.api_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": greeting}
        ]
        st.session_state.citizen_context = {}
        st.session_state.extracted_doc_text = ""
        st.session_state.last_doc_name = ""
        st.session_state.processed_audio_hashes = set()
        st.session_state.processed_doc_hashes = set()
        st.rerun()


# ── Header ────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">सरकारी सहायक (Sarkari Sahayak)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">सरकारी कल्याणकारी योजनाओं की सीधी और आसान जानकारी</div>', unsafe_allow_html=True)


# ── Document Context Display (If Available) ───────────────────────────
if st.session_state.citizen_context or st.session_state.extracted_doc_text:
    with st.container():
        doc_label = st.session_state.last_doc_name or "कागज़ात"
        context_items = []
        for k, v in st.session_state.citizen_context.items():
            context_items.append(f"**{k}:** {v}")
        summary_str = " • ".join(context_items) if context_items else "विवरण सुरक्षित हैं।"

        st.markdown(
            f'<div class="context-card">'
            f'<strong>आपके कागज़ात ({doc_label}) से सुरक्षित जानकारी:</strong><br>'
            f'{summary_str}'
            f'</div>',
            unsafe_allow_html=True
        )


# ── Helper: TTS Speech Generator (Bulbul v4 Flash) ────────────────────
def generate_speech(text: str) -> bytes | None:
    """Generate audio bytes using Bulbul v4 Flash."""
    try:
        lang = st.session_state.selected_lang or "hi-IN"
        clean = re.sub(r'[*#_`\[\]()]', '', text)
        clean = re.sub(r'https?://\S+', '', clean)
        clean = re.sub(r'===+.*?===+', '', clean)
        clean = clean.strip()
        if not clean:
            return None
        if len(clean) > 350:
            parts = re.split(r'[\n।.\?!]', clean)
            clean = "। ".join([p.strip() for p in parts[:3] if p.strip()]) + "।"
        return client.text_to_speech(clean, language_code=lang)
    except Exception:
        return None


# ── Helper: LLM Response with Tool Calling & Context Retention ───────
def get_llm_response(user_text: str) -> str:
    """Send user message to Sarvam 105B with document context preserved."""

    # Inject persistent document context if available
    context_prefix = ""
    if st.session_state.citizen_context:
        context_prefix = f"[PERSISTENT CITIZEN PROFILE: {json.dumps(st.session_state.citizen_context, ensure_ascii=False)}]\n\n"

    effective_message = f"{context_prefix}{user_text}" if context_prefix and not user_text.startswith("[PERSISTENT") else user_text
    st.session_state.api_messages.append({"role": "user", "content": effective_message})

    # Try language identification
    if len(user_text.strip()) > 8:
        try:
            detected = client.detect_language(user_text)
            if detected and detected in LANGUAGES:
                st.session_state.detected_lang = detected
        except Exception:
            pass

    # Call Sarvam 105B
    response = client.chat(
        messages=st.session_state.api_messages,
        tools=[ELIGIBILITY_TOOL],
        tool_choice="auto",
    )

    message = response.choices[0].message

    if message.tool_calls:
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

        for tool_call in message.tool_calls:
            if tool_call.function.name == "check_eligibility":
                try:
                    profile = json.loads(tool_call.function.arguments)
                except Exception:
                    profile = {}

                # Merge persistent context into profile
                for k, v in st.session_state.citizen_context.items():
                    if k not in profile:
                        profile[k] = v

                results = check_eligibility(profile, st.session_state.schemes)
                results_text = format_results_for_llm(results)

                st.session_state.api_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": results_text,
                })

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
        assistant_text = message.content or ""
        st.session_state.api_messages.append({
            "role": "assistant",
            "content": assistant_text,
        })
        return assistant_text


# ── Helper to extract profile attributes from document text ──────────
def extract_context_from_text(doc_text: str):
    """Simple parser to extract key citizen attributes from document text."""
    ctx = st.session_state.citizen_context

    # Age pattern
    age_match = re.search(r'(?:age|उम्र|आयु)\s*[:=-]?\s*(\d{1,2})', doc_text, re.IGNORECASE)
    if age_match:
        ctx["age"] = int(age_match.group(1))

    # Gender pattern
    if re.search(r'\b(female|महिला|स्त्री)\b', doc_text, re.IGNORECASE):
        ctx["gender"] = "female"
    elif re.search(r'\b(male|पुरुष)\b', doc_text, re.IGNORECASE):
        ctx["gender"] = "male"

    # State pattern
    for st_name in ["Uttar Pradesh", "Bihar", "Madhya Pradesh", "Rajasthan", "Maharashtra", "Tamil Nadu", "West Bengal", "Punjab", "Haryana", "Karnataka", "Gujarat", "Odisha", "Jharkhand", "Chhattisgarh"]:
        if st_name.lower() in doc_text.lower():
            ctx["state"] = st_name
            break

    # Occupation / Land
    if re.search(r'\b(farmer|किसान|कृषक|कृषि|खेती)\b', doc_text, re.IGNORECASE):
        ctx["occupation"] = "farmer"
        ctx["land_ownership"] = True
    elif re.search(r'\b(student|छात्र|विद्यार्थी)\b', doc_text, re.IGNORECASE):
        ctx["occupation"] = "student"
        ctx["is_student"] = True
    elif re.search(r'\b(artisan|कारीगर|शिल्पकार)\b', doc_text, re.IGNORECASE):
        ctx["occupation"] = "artisan"
        ctx["is_artisan"] = True
    elif re.search(r'\b(vendor|विक्रेता|रेहड़ी|पटरी)\b', doc_text, re.IGNORECASE):
        ctx["occupation"] = "street_vendor"
        ctx["is_street_vendor"] = True

    # BPL / Ration
    if re.search(r'\b(bpl|बीपीएल|antyodaya|अंत्योदय|phh)\b', doc_text, re.IGNORECASE):
        ctx["is_bpl"] = True

    st.session_state.citizen_context = ctx


# ═══════════════════════════════════════════════════════════════════════
# CENTRAL ACTION AREA: SPEECH IN THE MIDDLE + DOCUMENT UPLOAD
# ═══════════════════════════════════════════════════════════════════════
st.markdown('<div class="voice-box">', unsafe_allow_html=True)
st.markdown('<div class="voice-instruction">माइक बटन दबाएं और अपनी बात बोलें (Tap and Speak)</div>', unsafe_allow_html=True)

# Central speech button
audio_input = st.audio_input(
    "माइक से बोलें",
    key="central_mic_button",
    label_visibility="collapsed"
)

# Right below microphone: document upload
col_doc_input, col_doc_info = st.columns([2, 1])
with col_doc_input:
    uploaded_doc = st.file_uploader(
        "कागज़ात का फोटो या PDF अपलोड करें (आधार कार्ड, राशन कार्ड, खतौनी)",
        type=["jpg", "jpeg", "png", "pdf"],
        key="central_doc_uploader",
    )
with col_doc_info:
    st.caption("कागज़ात से आपकी उम्र, पता और स्थिति अपने आप समझ ली जाएगी।")

st.markdown('</div>', unsafe_allow_html=True)


# ── Process Document Upload Immediately & Keep Context ────────────────
if uploaded_doc is not None:
    doc_hash = f"{uploaded_doc.name}_{uploaded_doc.size}"
    if doc_hash not in st.session_state.processed_doc_hashes:
        st.session_state.processed_doc_hashes.add(doc_hash)
        with st.spinner(f"कागज़ पढ़ा जा रहा है ({uploaded_doc.name})..."):
            try:
                raw_bytes = uploaded_doc.read()
                extracted_text = client.parse_document(raw_bytes, filename=uploaded_doc.name)
                st.session_state.extracted_doc_text = extracted_text
                st.session_state.last_doc_name = uploaded_doc.name
                extract_context_from_text(extracted_text)

                # Prompt model to elaborate warmly in simple words
                elaboration_prompt = (
                    f"User uploaded an official document '{uploaded_doc.name}'.\n"
                    f"Extracted document text:\n\"\"\"\n{extracted_text}\n\"\"\"\n\n"
                    "Instructions for the response:\n"
                    "1. In very simple and respectful words, tell the user what details were read from their document.\n"
                    "2. Automatically call check_eligibility to check applicable welfare schemes.\n"
                    "3. Explain the eligible schemes clearly: What they get (in simple rupees/benefits), why they qualify, what papers to keep, and where to go to apply.\n"
                    "4. Reassure them that these details are now remembered for the rest of the conversation."
                )
                with st.spinner("सरकारी योजनाओं की जांच की जा रही है..."):
                    reply_text = get_llm_response(elaboration_prompt)
                    reply_audio = generate_speech(reply_text)

                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"📄 **कागज़ात अपलोड किया गया:** `{uploaded_doc.name}`"
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": reply_text,
                        "audio": reply_audio
                    })
                st.rerun()
            except Exception as e:
                st.error(f"कागज़ पढ़ने में समस्या आई: {e}")


# ── Process Audio Input (Saaras v4) ───────────────────────────────────
voice_message = None
if audio_input is not None:
    audio_raw = audio_input.read()
    audio_hash = hash(audio_raw)
    if audio_hash not in st.session_state.processed_audio_hashes:
        st.session_state.processed_audio_hashes.add(audio_hash)
        with st.spinner("आपकी आवाज़ सुनी जा रही है (Saaras v4)..."):
            try:
                lang = st.session_state.selected_lang
                voice_message = client.speech_to_text(audio_raw, language_code=lang, filename="voice.wav")
            except Exception as e:
                st.error(f"आवाज़ समझने में समस्या आई: {e}")


# ── Chat & Voice Display Section ──────────────────────────────────────
st.markdown("### सहायता संवाद (Assistance Conversation)")

# Display conversation messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🏛️" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])
        if "audio" in msg and msg["audio"]:
            st.audio(msg["audio"], format="audio/wav")

# Text chat input as alternative for typing
chat_text = st.chat_input("यहाँ अपनी बात लिखें या सवाल पूछें...")
active_input = voice_message or chat_text

if active_input:
    with st.chat_message("user", avatar="👤"):
        st.markdown(active_input)
    st.session_state.messages.append({"role": "user", "content": active_input})

    with st.chat_message("assistant", avatar="🏛️"):
        with st.spinner("योजनाओं की जानकारी खोजी जा रही है..."):
            reply = get_llm_response(active_input)
        st.markdown(reply)

        audio_bytes = generate_speech(reply)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")

    msg_record = {"role": "assistant", "content": reply}
    if audio_bytes:
        msg_record["audio"] = audio_bytes
    st.session_state.messages.append(msg_record)


# ── Simple Document Checklist Helper ──────────────────────────────────
with st.expander("📋 आवश्यक कागज़ात की सूची (Document Checklist)"):
    st.markdown("""
    **अधिकांश सरकारी योजनाओं के लिए आमतौर पर इन कागज़ातों की आवश्यकता होती है:**
    - [x] **आधार कार्ड** (Aadhaar Card) — पहचान और पते का प्रमाण
    - [ ] **बैंक खाता पासबुक** (Bank Passbook) — सीधे खाते में पैसा आने के लिए
    - [ ] **राशन कार्ड / बीपीएल कार्ड** (Ration Card) — राशन और स्वास्थ्य योजना के लिए
    - [ ] **आय प्रमाण पत्र** (Income Certificate) — यदि आय सीमा लागू हो
    - [ ] **ज़मीन के कागज़ / खतौनी** (Land Records) — केवल किसान योजनाओं के लिए
    - [ ] **पासपोर्ट साइज फोटो** (Photographs)
    """)
    st.caption("आप इनमें से जो भी कागज़ तैयार कर लें, नज़दीकी जन सेवा केंद्र (CSC) या बैंक में ले जा सकते हैं।")
