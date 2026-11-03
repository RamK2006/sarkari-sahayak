# 🏛️ Sarkari Sahayak (सरकारी सहायक)

An AI-powered citizen welfare scheme discovery and application assistant designed for Indian citizens with varying digital and language proficiencies.

Powered by **Sarvam AI**:
- 🎙️ **Saaras v4**: Speech-to-Text for 22+ Indian languages (Hindi, Tamil, Telugu, Bengali, Marathi, etc.)
- 🧠 **Sarvam 105B Conversations**: Multilingual reasoning engine with structured tool calling
- 🔊 **Bulbul v4 Flash**: Fast and expressive Text-to-Speech playback in native accents
- 📄 **Sarvam Doc AI**: Document parser for extracting data from Aadhaar, BPL cards, income certificates
- 🌐 **Mayura v1**: Translation across official Indian languages

---

## 🌟 Key Innovations

1. **Deterministic Rule Engine (No Hallucinations)**:
   - Does not invent or guess schemes. Matches citizen profiles against official government guidelines.
   - Explains exactly **why** a citizen qualifies or does not qualify.
2. **Missing Document & Information Identification**:
   - Detects if an essential parameter (e.g., Khasra land record, BPL certificate, girl child age) is missing and prompts gently.
3. **Multilingual Voice-First Interface**:
   - Citizens who cannot read or write English can speak naturally in their regional language and hear answers read aloud.

---

## 🚀 Quickstart

### 1. Ensure Dependencies are Installed
```bash
pip install -r requirements.txt
```

### 2. Verify `.env` File
Ensure your `.env` contains:
```env
SARVAM_API_KEY=your_sarvam_api_key_here
```

### 3. Launch the Application
Run:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📁 Project Structure

| File | Description |
|---|---|
| [`app.py`](file:///c:/..sarvam/app.py) | Full Streamlit application with chat, voice recording, TTS playback, and document upload |
| [`sarvam_client.py`](file:///c:/..sarvam/sarvam_client.py) | Production client wrapper for all Sarvam AI APIs (STT, TTS, Chat, Translation, Doc AI) |
| [`eligibility.py`](file:///c:/..sarvam/eligibility.py) | Deterministic rule matching engine against official eligibility criteria |
| [`schemes_db.json`](file:///c:/..sarvam/schemes_db.json) | Verified repository of 15 high-impact Central Government schemes |
| [`prompts.py`](file:///c:/..sarvam/prompts.py) | System prompt, persona guidelines, and tool schemas for Sarvam 105B |
| [`user_profile.py`](file:///c:/..sarvam/user_profile.py) | Pydantic data model for citizen attributes |
