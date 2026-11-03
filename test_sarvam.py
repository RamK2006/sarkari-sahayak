import os
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])

response = client.chat.completions(
    messages=[{"role": "user", "content": "Hello, tell me one interesting fact about India."}],
    model="sarvam-105b-conversations",
)

print(response.choices[0].message.content)
