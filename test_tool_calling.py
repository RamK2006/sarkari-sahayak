from sarvam_client import SarvamClient

client = SarvamClient()
msgs = [
    {"role": "user", "content": "Hi, I am looking for welfare schemes."},
    {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "call_12345",
                "type": "function",
                "function": {
                    "name": "check_eligibility",
                    "arguments": '{"age": 30, "state": "Bihar", "occupation": "farmer", "annual_income": 90000}'
                }
            }
        ]
    },
    {
        "role": "tool",
        "tool_call_id": "call_12345",
        "content": "=== ELIGIBLE SCHEMES ===\n1. PM-KISAN: ₹6,000/yr"
    }
]

from prompts import ELIGIBILITY_TOOL

try:
    res = client.chat(messages=msgs, tools=[ELIGIBILITY_TOOL])
    print("SUCCESS: Tool message supported!")
    print("Response:", res.choices[0].message.content)
except Exception as e:
    print("ERROR:", type(e), e)
