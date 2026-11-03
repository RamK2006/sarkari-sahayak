"""
Sarkari Sahayak — Government Welfare Scheme Discovery Assistant
Comprehensive Multi-Feature & Multilingual Application.

Powered by Sarvam AI:
- Sarvam 105B Conversations (Chat & Reasoning with Tool Calling)
- Saaras v4 (Speech-to-Text in 22+ Indian languages)
- Bulbul v4 Flash (Text-to-Speech with native regional voices)
- Mayura v1 (High-quality Indian Language Translation)
- Sarvam Doc AI (Document extraction & verification)
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional
import streamlit as st

from sarvam_client import SarvamClient
from eligibility import (
    check_eligibility,
    load_schemes,
    format_results_for_llm,
    get_all_categories,
    filter_schemes,
)
from prompts import SYSTEM_PROMPT, ELIGIBILITY_TOOL


# ── Page Config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sarkari Sahayak | सरकारी सहायक",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Supported Languages Configuration ─────────────────────────────────
LANGUAGES = {
    "hi-IN": {"name": "हिन्दी (Hindi)", "short": "Hindi", "greeting": "नमस्ते! मैं आपका सरकारी सहायक हूँ। अपनी स्थिति बताएं — जैसे आपकी उम्र, कार्य, राज्य, और वार्षिक आय।"},
    "en-IN": {"name": "English", "short": "English", "greeting": "Hello! I am your Sarkari Sahayak. Describe your situation — such as your age, occupation, state, and annual income."},
    "bn-IN": {"name": "বাংলা (Bengali)", "short": "Bengali", "greeting": "নমস্কার! আমি আপনার সরকারি সহায়ক। আপনার পরিস্থিতি বর্ণনা করুন — যেমন আপনার বয়স, পেশা, রাজ্য এবং বার্ষিক আয়।"},
    "ta-IN": {"name": "தமிழ் (Tamil)", "short": "Tamil", "greeting": "வணக்கம்! நான் உங்கள் அரசு உதவியாளர். உங்கள் சூழ்நிலையை விவரிக்கவும் — உங்கள் வயது, தொழில், மாநிலம் மற்றும் வருமானம்."},
    "te-IN": {"name": "తెలుగు (Telugu)", "short": "Telugu", "greeting": "నమస్కారం! నేను మీ సర్కారీ సహాయక్‌ని. మీ పరిస్థితిని వివరించండి — మీ వయస్సు, వృత్తి, రాష్ట్రం మరియు వార్షిక ఆదాయం."},
    "mr-IN": {"name": "मराठी (Marathi)", "short": "Marathi", "greeting": "नमस्कार! मी तुमचा सरकारी सहाय्यक आहे. तुमची परिस्थिती सांगा — जसे तुमचे वय, व्यवसाय, राज्य आणि वार्षिक उत्पन्न."},
    "gu-IN": {"name": "ગુજરાતી (Gujarati)", "short": "Gujarati", "greeting": "નમસ્તે! હું તમારો સરકારી સહાયક છું. તમારી પરિસ્થિતિ જણાવો — જેમ કે તમારી ઉંમર, વ્યવસાય, રાજ્ય અને વાર્ષિક આવક."},
    "kn-IN": {"name": "ಕನ್ನಡ (Kannada)", "short": "Kannada", "greeting": "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಸರ್ಕಾರಿ ಸಹಾಯಕ. ನಿಮ್ಮ ಪರಿಸ್ಥಿತಿಯನ್ನು ವಿವರಿಸಿ — ನಿಮ್ಮ ವಯಸ್ಸು, ಉದ್ಯೋಗ, ರಾಜ್ಯ ಮತ್ತು ವಾರ್ಷಿಕ ಆದಾಯ."},
    "pa-IN": {"name": "ਪੰਜਾਬੀ (Punjabi)", "short": "Punjabi", "greeting": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ ਸਰਕਾਰੀ ਸਹਾਇਕ ਹਾਂ। ਆਪਣੀ ਸਥਿਤੀ ਬਾਰੇ ਦੱਸੋ — ਜਿਵੇਂ ਕਿ ਤੁਹਾਡੀ ਉਮਰ, ਕੰਮ, ਰਾਜ ਅਤੇ ਸਾਲਾਨਾ ਆਮਦਨ।"},
    "od-IN": {"name": "ଓଡ଼ିଆ (Odia)", "short": "Odia", "greeting": "ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କର ସରକାରୀ ସହାୟକ। ଆପଣଙ୍କ ପରିସ୍ଥିତି ବିଷୟରେ ଜଣାନ୍ତୁ — ଯେପରିକି ଆପଣଙ୍କ ବୟସ, ବୃତ୍ତି, ରାଜ୍ୟ ଏବଂ ଆୟ।"},
    "ml-IN": {"name": "മലയാളം (Malayalam)", "short": "Malayalam", "greeting": "നമസ്കാരം! ഞാൻ നിങ്ങളുടെ സർക്കാർ സഹായകനാണ്. നിങ്ങളുടെ പ്രായം, ജോലി, സംസ്ഥാനം, വരുമാനം എന്നിവ അറിയിക്കുക."},
}

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Jammu and Kashmir", "Ladakh"
]


# ── Session State Init ────────────────────────────────────────────────
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
            st.error(f"Failed to initialize Sarvam AI Client: {e}")
            st.stop()
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": LANGUAGES[st.session_state.selected_lang]["greeting"]}
        ]
    if "api_messages" not in st.session_state:
        lang_name = LANGUAGES[st.session_state.selected_lang]["short"]
        custom_system = f"{SYSTEM_PROMPT}\n\nIMPORTANT: The user has selected {lang_name} as their preferred language. Respond in {lang_name} by default."
        st.session_state.api_messages = [
            {"role": "system", "content": custom_system},
            {"role": "assistant", "content": LANGUAGES[st.session_state.selected_lang]["greeting"]}
        ]
    if "latest_assessment_results" not in st.session_state:
        st.session_state.latest_assessment_results = None
    if "processed_audio_hashes" not in st.session_state:
        st.session_state.processed_audio_hashes = set()
    if "processed_docs" not in st.session_state:
        st.session_state.processed_docs = set()


init_session()
client: SarvamClient = st.session_state.client


# ── Sidebar Configuration & Language Switcher ─────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/government.png", width=64)
    st.title("Sarkari Sahayak")
    st.caption("सरकारी सहायक — Multi-Feature Citizen Portal")

    # Language Selector
    st.subheader("🌐 भाषा / Language")
    selected_code = st.selectbox(
        "Choose primary language",
        options=list(LANGUAGES.keys()),
        format_func=lambda code: LANGUAGES[code]["name"],
        index=list(LANGUAGES.keys()).index(st.session_state.selected_lang),
        key="lang_select",
    )

    if selected_code != st.session_state.selected_lang:
        st.session_state.selected_lang = selected_code
        st.session_state.detected_lang = selected_code
        greeting = LANGUAGES[selected_code]["greeting"]
        lang_name = LANGUAGES[selected_code]["short"]
        custom_system = f"{SYSTEM_PROMPT}\n\nIMPORTANT: The user has selected {lang_name} as their preferred language. Respond in {lang_name} by default."
        st.session_state.messages = [{"role": "assistant", "content": greeting}]
        st.session_state.api_messages = [
            {"role": "system", "content": custom_system},
            {"role": "assistant", "content": greeting}
        ]
        st.rerun()

    st.divider()

    # Voice Assistant Controls in Sidebar
    st.subheader("🎙️ Voice Assistant")
    st.caption(f"Speak in {LANGUAGES[st.session_state.selected_lang]['short']}")
    audio_input = st.audio_input("Record voice query", key="sidebar_audio_recorder")

    st.divider()

    # Quick Stats
    st.subheader("📊 Database Overview")
    total_schemes = len(st.session_state.schemes)
    st.metric("Verified Schemes", f"{total_schemes} Central Schemes")
    st.metric("Supported Languages", "11 Indian Languages")

    st.divider()

    if st.button("🔄 Reset Conversation", use_container_width=True):
        greeting = LANGUAGES[st.session_state.selected_lang]["greeting"]
        lang_name = LANGUAGES[st.session_state.selected_lang]["short"]
        st.session_state.messages = [{"role": "assistant", "content": greeting}]
        st.session_state.api_messages = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nIMPORTANT: Active language is {lang_name}."},
            {"role": "assistant", "content": greeting}
        ]
        st.session_state.processed_audio_hashes = set()
        st.session_state.processed_docs = set()
        st.session_state.latest_assessment_results = None
        st.rerun()


# ── Helper: TTS Speech Generator (Bulbul v4 Flash) ────────────────────
def generate_speech(text: str, lang_code: Optional[str] = None) -> bytes | None:
    """Generate audio bytes using Bulbul v4 Flash."""
    try:
        lang = lang_code or st.session_state.selected_lang or "hi-IN"
        # Clean text of markdown and links for natural TTS
        clean_text = re.sub(r'[*#_`\[\]()]', '', text)
        clean_text = re.sub(r'https?://\S+', '', clean_text)
        clean_text = re.sub(r'===+.*?===+', '', clean_text)
        clean_text = clean_text.strip()
        if not clean_text:
            return None

        # Truncate to first few sentences for snappy voice responses
        if len(clean_text) > 350:
            parts = re.split(r'[\n।.\?!]', clean_text)
            clean_text = "। ".join([p.strip() for p in parts[:3] if p.strip()]) + "।"

        return client.text_to_speech(clean_text, language_code=lang)
    except Exception:
        return None


# ── Helper: LLM Response with Tool Calling (Sarvam 105B) ──────────────
def get_llm_response(user_text: str) -> str:
    """Send message to Sarvam 105B Conversations with check_eligibility tool handling."""
    st.session_state.api_messages.append({"role": "user", "content": user_text})

    # Try language identification if input is substantial
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
        # Tool call triggered by 105B
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

                # Execute deterministic eligibility evaluation
                results = check_eligibility(profile, st.session_state.schemes)
                st.session_state.latest_assessment_results = results
                results_text = format_results_for_llm(results)

                st.session_state.api_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": results_text,
                })

        # Final reasoned response from 105B
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


# ═══════════════════════════════════════════════════════════════════════
# MAIN INTERFACE TABS
# ═══════════════════════════════════════════════════════════════════════
tab_chat, tab_calc, tab_dir, tab_ocr, tab_checklist = st.tabs([
    "💬 AI Voice & Chat Assistant",
    "🎯 Instant Eligibility Calculator",
    "📋 Verified Scheme Directory",
    "📄 Document Scanner (Doc AI)",
    "📑 Application Checklist",
])


# ─────────────────────────────────────────────────────────────────────
# TAB 1: AI VOICE & CHAT ASSISTANT
# ─────────────────────────────────────────────────────────────────────
with tab_chat:
    st.subheader("🗣️ Conversational Scheme Discovery")
    st.caption("Tell your story or describe your situation in your own language. The assistant checks real government eligibility rules.")

    # Quick prompt buttons for convenience
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        if st.button("🌾 किसान (Rural Farmer, ₹1L income)", use_container_width=True):
            quick_prompt = "नमस्ते, मैं उत्तर प्रदेश का 38 वर्षीय किसान हूँ। मेरी वार्षिक आय ₹1 लाख है और मेरे पास 1.5 हेक्टेयर कृषि भूमि है। मैं आयकर नहीं देता। मुझे किन योजनाओं का लाभ मिल सकता है?"
            st.session_state.messages.append({"role": "user", "content": quick_prompt})
            with st.spinner("Evaluating eligibility..."):
                reply = get_llm_response(quick_prompt)
                audio_b = generate_speech(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply, "audio": audio_b})
            st.rerun()

    with col_p2:
        if st.button("👩‍👧 माता व बालिका (Mother & Daughter under 10)", use_container_width=True):
            quick_prompt = "नमस्ते, मैं 29 वर्षीय गृहिणी हूँ, मेरी 5 वर्ष की एक बेटी है। परिवार की वार्षिक आय ₹1.8 लाख है। क्या बालिकाओं या महिलाओं के लिए कोई योजना है?"
            st.session_state.messages.append({"role": "user", "content": quick_prompt})
            with st.spinner("Evaluating eligibility..."):
                reply = get_llm_response(quick_prompt)
                audio_b = generate_speech(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply, "audio": audio_b})
            st.rerun()

    with col_p3:
        if st.button("🎓 SC/ST छात्र (College Student)", use_container_width=True):
            quick_prompt = "Hello, I am a 20-year-old student from Madhya Pradesh pursuing college education. I belong to SC category and family income is ₹1.5 Lakh. What scholarships am I eligible for?"
            st.session_state.messages.append({"role": "user", "content": quick_prompt})
            with st.spinner("Evaluating eligibility..."):
                reply = get_llm_response(quick_prompt)
                audio_b = generate_speech(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply, "audio": audio_b})
            st.rerun()

    # Instant Document Upload in Chat Tab
    with st.expander("📎 दस्तावेज़ अपलोड करें (Auto-Read Aadhaar / Ration Card / Income)", expanded=False):
        chat_doc = st.file_uploader(
            "Upload identity or eligibility document (PDF or Image)",
            type=["pdf", "png", "jpg", "jpeg"],
            key="chat_tab_uploader"
        )
        if chat_doc is not None:
            c_doc_id = f"{chat_doc.name}_{chat_doc.size}"
            if c_doc_id not in st.session_state.processed_docs:
                st.session_state.processed_docs.add(c_doc_id)
                with st.spinner(f"📄 Reading {chat_doc.name} with Sarvam Doc AI..."):
                    try:
                        raw_b = chat_doc.read()
                        extracted_t = client.parse_document(raw_b, filename=chat_doc.name)
                        st.success(f"✅ Read {chat_doc.name} successfully!")

                        with st.spinner("Analyzing profile details and checking welfare schemes..."):
                            prompt = (
                                f"User uploaded an official document '{chat_doc.name}'.\n"
                                f"Extracted text from Sarvam Doc AI:\n\"\"\"\n{extracted_t}\n\"\"\"\n\n"
                                "Instructions:\n"
                                "1. State what personal details were identified from the document (Name, Age, Gender, State, Occupation, Income, Land, etc.).\n"
                                "2. Call check_eligibility tool to evaluate welfare schemes based on these parameters.\n"
                                "3. Elaborate on which government welfare schemes apply, why they qualify, what benefits they will receive, and the next steps to apply."
                            )
                            doc_reply = get_llm_response(prompt)
                            doc_audio = generate_speech(doc_reply)
                            st.session_state.messages.append({
                                "role": "user",
                                "content": f"📄 **Uploaded Document:** `{chat_doc.name}`\n\n```\n{extracted_t}\n```"
                            })
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": doc_reply,
                                "audio": doc_audio
                            })
                        st.rerun()
                    except Exception as e:
                        st.error(f"Doc AI error: {e}")

    st.divider()

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🏛️" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
            if "audio" in msg and msg["audio"]:
                st.audio(msg["audio"], format="audio/wav")

    # Check for Audio Input from Sidebar (Saaras v4)
    voice_query = None
    if audio_input is not None:
        audio_raw = audio_input.read()
        audio_id = hash(audio_raw)
        if audio_id not in st.session_state.processed_audio_hashes:
            st.session_state.processed_audio_hashes.add(audio_id)
            with st.spinner("🎙️ Transcribing voice with Saaras v4..."):
                try:
                    lang = st.session_state.selected_lang
                    voice_query = client.speech_to_text(audio_raw, language_code=lang, filename="voice.wav")
                    st.success(f"📝 Heard ({LANGUAGES[lang]['short']}): {voice_query}")
                except Exception as e:
                    st.error(f"Speech transcription failed: {e}")

    # Chat Text Input
    chat_query = st.chat_input("अपनी स्थिति बताएं... / Type your query in any language...")
    active_query = voice_query or chat_query

    if active_query:
        with st.chat_message("user", avatar="👤"):
            st.markdown(active_query)
        st.session_state.messages.append({"role": "user", "content": active_query})

        with st.chat_message("assistant", avatar="🏛️"):
            with st.spinner("Checking verified government rules..."):
                ans = get_llm_response(active_query)
            st.markdown(ans)
            speech = generate_speech(ans)
            if speech:
                st.audio(speech, format="audio/wav")

        msg_obj = {"role": "assistant", "content": ans}
        if speech:
            msg_obj["audio"] = speech
        st.session_state.messages.append(msg_obj)


# ─────────────────────────────────────────────────────────────────────
# TAB 2: INSTANT ELIGIBILITY CALCULATOR
# ─────────────────────────────────────────────────────────────────────
with tab_calc:
    st.subheader("🎯 Direct Scheme Eligibility Assessment")
    st.caption("Common Service Center (CSC) operator or citizen direct evaluation form.")

    with st.form("eligibility_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            f_age = st.number_input("Age (उम्र)", min_value=1, max_value=120, value=35)
            f_gender = st.selectbox("Gender (लिंग)", ["male", "female", "other"], index=0)
            f_state = st.selectbox("State of Residence (राज्य)", INDIAN_STATES, index=INDIAN_STATES.index("Uttar Pradesh") if "Uttar Pradesh" in INDIAN_STATES else 0)
            f_area = st.selectbox("Area Type (क्षेत्र)", ["rural", "urban"])

        with col2:
            f_occ = st.selectbox(
                "Occupation (पेशा/व्यवसाय)",
                ["farmer", "student", "labourer", "artisan", "street_vendor", "self_employed", "salaried", "unemployed", "homemaker"]
            )
            f_income = st.number_input("Annual Family Income in ₹ (वार्षिक आय)", min_value=0, max_value=5000000, value=120000, step=10000)
            f_caste = st.selectbox("Caste Category (वर्ग)", ["general", "obc", "sc", "st"])
            f_bpl = st.checkbox("Holds BPL / Ration Card (बीपीएल कार्डधारक)", value=True)

        with col3:
            f_land = st.checkbox("Owns Agricultural Land (कृषि भूमि)", value=(f_occ == "farmer"))
            f_marital = st.selectbox("Marital Status", ["married", "single", "widowed", "divorced"])
            f_daughter = st.checkbox("Has Daughter aged ≤ 10 years", value=False)
            f_pregnant = st.checkbox("Pregnant or Lactating Mother", value=False)
            f_taxpayer = st.checkbox("Income Tax Payer (आयकर दाता)", value=False)
            f_govtemp = st.checkbox("Government Employee (सरकारी कर्मचारी)", value=False)
            f_pucca = st.checkbox("Already Owns a Pucca House", value=False)
            f_lpg = st.checkbox("Already has LPG Connection", value=False)

        submit_calc = st.form_submit_button("🔍 Check Scheme Eligibility Now", use_container_width=True)

    if submit_calc:
        profile_input = {
            "age": int(f_age),
            "gender": f_gender,
            "state": f_state,
            "rural_urban": f_area,
            "occupation": f_occ,
            "annual_income": int(f_income),
            "caste_category": f_caste,
            "is_bpl": f_bpl,
            "land_ownership": f_land,
            "marital_status": f_marital,
            "is_widow": (f_marital == "widowed"),
            "num_daughters": 1 if f_daughter else 0,
            "daughter_ages": [7] if f_daughter else [],
            "is_pregnant": f_pregnant,
            "is_income_tax_payer": f_taxpayer,
            "is_government_employee": f_govtemp,
            "has_pucca_house": f_pucca,
            "has_lpg_connection": f_lpg,
        }

        eval_results = check_eligibility(profile_input, st.session_state.schemes)
        st.session_state.latest_assessment_results = eval_results

        eligible_schemes = [r for r in eval_results if r["eligible"]]
        maybe_schemes = [r for r in eval_results if not r["eligible"] and r["missing_info"] and not r["reasons_disqualified"]]
        ineligible_schemes = [r for r in eval_results if not r["eligible"] and r["reasons_disqualified"]]

        st.success(f"🎉 **{len(eligible_schemes)} Eligible Schemes Found!**")

        st.markdown("### 🟢 Confirmed Eligible Schemes")
        for s in eligible_schemes:
            with st.expander(f"✅ {s['scheme_name']} ({s['scheme_name_hi']})", expanded=True):
                st.markdown(f"**Benefits:** {s['benefits']}")
                st.markdown(f"**Description:** {s['description']}")
                st.markdown("**Why You Qualify:**")
                for r in s["reasons_qualified"]:
                    st.markdown(f"- ✓ {r}")
                st.markdown(f"**Required Documents:** `{', '.join(s['documents_required'])}`")
                if s["application_url"]:
                    st.markdown(f"🔗 [Apply on Official Portal]({s['application_url']}) | [Official Guidelines]({s['source_url']})")

        if maybe_schemes:
            st.markdown("### 🟡 Potentially Eligible (Need Verification)")
            for s in maybe_schemes:
                with st.expander(f"⚠️ {s['scheme_name']} ({s['scheme_name_hi']})"):
                    st.markdown(f"**Benefits:** {s['benefits']}")
                    for m in s["missing_info"]:
                        st.markdown(f"- ℹ️ {m}")

        if ineligible_schemes:
            with st.expander("🔴 View Non-Eligible Schemes (Rule Transparency)"):
                for s in ineligible_schemes:
                    st.markdown(f"**{s['scheme_name']}:**")
                    for d in s["reasons_disqualified"]:
                        st.markdown(f"  • *Disqualified:* {d}")


# ─────────────────────────────────────────────────────────────────────
# TAB 3: VERIFIED SCHEME DIRECTORY
# ─────────────────────────────────────────────────────────────────────
with tab_dir:
    st.subheader("📚 Verified Government Schemes Directory")
    st.caption("Explore verified central schemes with authentic eligibility rules and application links.")

    all_cats = ["All"] + get_all_categories(st.session_state.schemes)
    col_cat, col_search = st.columns([1, 2])
    with col_cat:
        chosen_cat = st.selectbox("Filter by Category", all_cats, index=0)
    with col_search:
        search_query = st.text_input("Search schemes by name, keyword, or ministry", placeholder="e.g. Kisan, Awas, Loan, Pension, Student...")

    filtered = filter_schemes(st.session_state.schemes, category=chosen_cat if chosen_cat != "All" else None, query=search_query)

    st.write(f"Showing **{len(filtered)}** schemes:")
    for scheme in filtered:
        with st.container(border=True):
            col_left, col_right = st.columns([3, 1])
            with col_left:
                st.markdown(f"### {scheme['name']}")
                st.caption(f"{scheme.get('name_hi', '')} | 🏛️ {scheme.get('ministry', '')}")
                st.markdown(f"**Description:** {scheme.get('description', '')}")
                st.markdown(f"**💰 Benefits:** {scheme.get('benefits', '')}")
                st.markdown(f"**📑 Documents Required:** `{', '.join(scheme.get('documents_required', []))}`")
            with col_right:
                st.markdown("**Categories:**")
                for c in scheme.get("category", []):
                    st.badge(c)
                st.markdown("---")
                if scheme.get("application_url"):
                    st.link_button("🌐 Apply Now", scheme["application_url"], use_container_width=True)
                if scheme.get("source_url"):
                    st.link_button("📖 Guidelines", scheme["source_url"], use_container_width=True)


# ─────────────────────────────────────────────────────────────────────
# TAB 4: DOCUMENT SCANNER (SARVAM DOC AI)
# ─────────────────────────────────────────────────────────────────────
with tab_ocr:
    st.subheader("📄 Document Scanner & Auto-Extraction")
    st.caption("Upload Aadhaar, Ration Card, BPL Certificate, or Land Record. Sarvam Doc AI extracts text and maps eligibility.")

    doc_upload = st.file_uploader(
        "Upload identity or eligibility document",
        type=["pdf", "png", "jpg", "jpeg"],
        key="ocr_tab_uploader"
    )

    if doc_upload is not None:
        doc_key = f"{doc_upload.name}_{doc_upload.size}"
        if doc_key not in st.session_state.processed_docs:
            st.session_state.processed_docs.add(doc_key)
            with st.spinner(f"📄 Analyzing {doc_upload.name} with Sarvam Doc AI..."):
                try:
                    raw_bytes = doc_upload.read()
                    doc_text = client.parse_document(raw_bytes, filename=doc_upload.name)
                    st.session_state["last_ocr_text"] = doc_text
                    st.session_state["last_ocr_filename"] = doc_upload.name

                    with st.spinner("🤖 Elaborating on welfare scheme eligibility based on your document..."):
                        prompt = (
                            f"User uploaded document '{doc_upload.name}'.\n"
                            f"Extracted text from Sarvam Doc AI:\n\"\"\"\n{doc_text}\n\"\"\"\n\n"
                            "Instructions:\n"
                            "1. State what personal and demographic details were identified (Name, Age, Gender, State, Occupation, Income, Land, etc.).\n"
                            "2. Call check_eligibility tool to evaluate welfare schemes for this profile.\n"
                            "3. Elaborate in detail on all eligible government schemes, explaining why the citizen qualifies, the exact benefits, and next steps to apply."
                        )
                        elaboration_text = get_llm_response(prompt)
                        elaboration_speech = generate_speech(elaboration_text)
                        st.session_state["last_ocr_elaboration"] = elaboration_text
                        st.session_state["last_ocr_audio"] = elaboration_speech
                        st.session_state.messages.append({
                            "role": "user",
                            "content": f"📄 **Uploaded Document:** `{doc_upload.name}`\n\n```\n{doc_text}\n```"
                        })
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": elaboration_text,
                            "audio": elaboration_speech
                        })
                except Exception as e:
                    st.error(f"Doc AI error: {e}")

        # Display results if available
        if "last_ocr_text" in st.session_state and st.session_state["last_ocr_text"]:
            st.success(f"✅ Successfully read and analyzed `{st.session_state.get('last_ocr_filename', 'Document')}`")

            col_ocr1, col_ocr2 = st.columns([1, 1])
            with col_ocr1:
                st.markdown("### 📝 Extracted Document Text")
                st.text_area("Extracted Details", st.session_state["last_ocr_text"], height=220)

            with col_ocr2:
                st.markdown("### 🏛️ Scheme Eligibility & Elaboration")
                if "last_ocr_elaboration" in st.session_state:
                    st.markdown(st.session_state["last_ocr_elaboration"])
                    if st.session_state.get("last_ocr_audio"):
                        st.audio(st.session_state["last_ocr_audio"], format="audio/wav")


# ─────────────────────────────────────────────────────────────────────
# TAB 5: APPLICATION CHECKLIST GENERATOR
# ─────────────────────────────────────────────────────────────────────
with tab_checklist:
    st.subheader("📑 Personalized Application Checklist")
    st.caption("Consolidated list of documents needed for your eligible welfare schemes.")

    eval_results = st.session_state.latest_assessment_results
    if not eval_results:
        st.info("👉 Run an assessment first in **Tab 1 (Chat)** or **Tab 2 (Calculator)** to generate your custom checklist.")
    else:
        eligible = [r for r in eval_results if r["eligible"]]
        if not eligible:
            st.warning("No eligible schemes found in the latest assessment. Adjust criteria in Tab 2 to re-evaluate.")
        else:
            st.success(f"Checklist generated for **{len(eligible)} eligible schemes**.")

            # Collect unique documents across eligible schemes
            all_docs: Dict[str, List[str]] = {}
            for s in eligible:
                for doc in s["documents_required"]:
                    if doc not in all_docs:
                        all_docs[doc] = []
                    all_docs[doc].append(s["scheme_name"])

            st.markdown("### 📋 Required Documents")
            st.caption("Check off the documents you already possess:")

            checklist_markdown = "# 🏛️ Sarkari Sahayak — Personalized Application Checklist\n\n"
            checklist_markdown += f"**Eligible Schemes:** {', '.join([s['scheme_name'] for s in eligible])}\n\n"
            checklist_markdown += "## Required Documents:\n"

            for doc, schemes_needing in all_docs.items():
                checked = st.checkbox(f"**{doc}** — Needed for: *{', '.join(schemes_needing)}*", key=f"chk_{hash(doc)}")
                status = "[x]" if checked else "[ ]"
                checklist_markdown += f"- {status} {doc} (For: {', '.join(schemes_needing)})\n"

            checklist_markdown += "\n---\nGenerated by Sarkari Sahayak (Powered by Sarvam AI)\n"

            st.download_button(
                label="📥 Download Checklist as Text File",
                data=checklist_markdown,
                file_name="sarkari_sahayak_checklist.txt",
                mime="text/plain",
                use_container_width=True,
            )
