from sarvam_client import SarvamClient

client = SarvamClient()

with open("test_audio.wav", "rb") as f:
    audio_bytes = f.read()

print("Testing speech-to-text with generated audio...")
try:
    # Try with tuple (filename, bytes)
    transcript = client.client.speech_to_text.transcribe(
        file=("audio.wav", audio_bytes, "audio/wav"),
        model="saaras:v4",
        language_code="hi-IN"
    )
    print("STT Transcript:", transcript.transcript)
except Exception as e:
    print("STT Error:", type(e), e)
