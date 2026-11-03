import os
import httpx
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ["SARVAM_API_KEY"]
job_id = "01a1a078-fda6-7cc7-bd0a-1b8310df3e06"

# Fetch results via raw HTTP to bypass the SDK pydantic tagged-union bug
url = f"https://api.sarvam.ai/doc-ai/{job_id}/results"
headers = {"api-subscription-key": api_key}

r = httpx.get(url, headers=headers)
print("HTTP status:", r.status_code)
data = r.json()
print("Data keys:", data.keys())
print("Data type:", data.get("type"))
print("Data result preview:", str(data)[:500])
