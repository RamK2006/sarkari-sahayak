from sarvam_client import SarvamClient
import time

client = SarvamClient()

# Create a sample text file or minimal PDF to test Doc AI
sample_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000117 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n212\n%%EOF"

print("Testing Doc AI parse endpoint...")
try:
    resp = client.client.doc_ai.parse(
        file=[("sample.pdf", sample_content, "application/pdf")]
    )
    print("Job initiated. Response:", resp)
    print("Job ID:", getattr(resp, 'job_id', None))
except Exception as e:
    print("Doc AI test error:", type(e), e)
