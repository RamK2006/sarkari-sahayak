from sarvam_client import SarvamClient
from prompts import ELIGIBILITY_TOOL

client = SarvamClient()

sample_extracted_text = """
GOVERNMENT OF INDIA
Name: Ramesh Kumar
Age: 42 Years, Gender: Male
Address: Varanasi, Uttar Pradesh (Rural)
Occupation: Farmer, Land: 1.2 Hectare
Annual Family Income: Rs. 95,000
BPL Card No: UP-BPL-2023-88912
"""

prompt = (
    "User uploaded an official government document. Extracted text:\n"
    f"\"\"\"\n{sample_extracted_text}\n\"\"\"\n\n"
    "1. Acknowledge and state what profile details were successfully extracted from the document.\n"
    "2. Call check_eligibility tool to evaluate real government welfare schemes based on these details.\n"
    "3. Elaborate on which schemes the user qualifies for, the benefits, and the next steps to apply."
)

res = client.chat(
    messages=[
        {"role": "system", "content": "You are Sarkari Sahayak. Evaluate schemes when user uploads a document."},
        {"role": "user", "content": prompt}
    ],
    tools=[ELIGIBILITY_TOOL],
    tool_choice="auto"
)

msg = res.choices[0].message
print("Tool calls triggered:", [tc.function.name for tc in (msg.tool_calls or [])])
print("Content:", msg.content)
