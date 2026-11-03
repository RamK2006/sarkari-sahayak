import os
from dotenv import load_dotenv
from sarvam_client import SarvamClient
from prompts import ELIGIBILITY_TOOL

load_dotenv()
client = SarvamClient()

# 1. Test Chat completion with tool definition
print("Testing Chat with tool support...")
messages = [
    {"role": "system", "content": "You are Sarkari Sahayak. When user provides their details, call check_eligibility."},
    {"role": "user", "content": "नमस्ते, मैं उत्तर प्रदेश का 35 वर्षीय किसान हूँ। मेरी वार्षिक आय 1 लाख रुपये है और मेरे पास कृषि भूमि है। मैं आयकर नहीं देता। क्या मुझे कोई सरकारी योजना मिल सकती है?"}
]

res = client.chat(messages=messages, tools=[ELIGIBILITY_TOOL], tool_choice="auto")
msg = res.choices[0].message
print("Model response received.")
if msg.tool_calls:
    print(f"Tool call triggered: {msg.tool_calls[0].function.name}")
    print(f"Arguments: {msg.tool_calls[0].function.arguments}")
else:
    print(f"Direct content: {msg.content}")

# 2. Test TTS (Bulbul v4 Flash)
print("\nTesting Text-to-Speech (Bulbul v4 Flash)...")
audio_data = client.text_to_speech(
    text="नमस्ते, आपकी पात्रता के अनुसार आप पीएम किसान सम्मान निधि योजना के लिए पात्र हैं।",
    language_code="hi-IN"
)
print(f"Generated audio bytes: {len(audio_data)} bytes")
with open("test_audio.wav", "wb") as f:
    f.write(audio_data)
print("Saved test_audio.wav successfully.")
