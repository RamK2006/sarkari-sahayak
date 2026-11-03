from sarvam_client import SarvamClient
import time

client = SarvamClient()
job_id = "01a1a078-fda6-7cc7-bd0a-1b8310df3e06"

for i in range(15):
    status = client.client.doc_ai.get_status(job_id)
    print(f"Poll {i}: status={status.status}")
    if status.status in ("completed", "failed", "SUCCESS"):
        break
    time.sleep(2)

try:
    results = client.client.doc_ai.get_results(job_id)
    print("Get results returned type:", type(results))
    print("Results attributes:", dir(results))
    print("Results content:", results)
except Exception as e:
    print("Get results error:", type(e), e)
