from sarvam_client import SarvamClient
import time
import json

client = SarvamClient()

# Create a small image with some text or a simple image using PIL
from PIL import Image, ImageDraw, ImageFont
import io

img = Image.new('RGB', (800, 400), color=(255, 255, 255))
d = ImageDraw.Draw(img)
d.text((50, 50), "GOVERNMENT OF INDIA", fill=(0, 0, 0))
d.text((50, 100), "Name: Ramesh Kumar", fill=(0, 0, 0))
d.text((50, 150), "Age: 42 Years, Gender: Male", fill=(0, 0, 0))
d.text((50, 200), "Address: Varanasi, Uttar Pradesh", fill=(0, 0, 0))
d.text((50, 250), "Occupation: Farmer, Land: 1.2 Hectare", fill=(0, 0, 0))

buf = io.BytesIO()
img.save(buf, format='JPEG')
img_bytes = buf.getvalue()

print(f"Uploading image ({len(img_bytes)} bytes) to Doc AI...")
resp = client.client.doc_ai.parse(
    file=[("aadhaar_sample.jpg", img_bytes, "image/jpeg")]
)
job_id = resp.job_id
print(f"Job started: {job_id}")

for i in range(20):
    status = client.client.doc_ai.get_status(job_id)
    print(f"Poll {i}: {status.status}")
    if status.status in ("completed", "failed", "SUCCESS"):
        break
    time.sleep(3)

# Fetch results JSON
raw_wrapper = client.client.doc_ai._raw_client._client_wrapper
res = raw_wrapper.httpx_client.request(
    f"doc-ai/v1/job/{job_id}/results",
    base_url=raw_wrapper.get_environment().base,
    method="GET",
)
data = res.json()
print("Result JSON keys:", data.keys())

extracted_texts = []
for doc in data.get("documents", []):
    for page in doc.get("pages", []):
        for block in page.get("blocks", []):
            # check block structure
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if "text" in span:
                        extracted_texts.append(span["text"])

print("Extracted Spans:")
print("\n".join(extracted_texts))
