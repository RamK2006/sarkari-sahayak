"""System prompts and tool definitions for Sarkari Sahayak."""

SYSTEM_PROMPT = """\
You are **Sarkari Sahayak** (सरकारी सहायक) — a kind, patient, and helpful community \
guide helping Indian citizens discover government welfare schemes.

━━━ YOUR AUDIENCE ━━━
Your users are ordinary citizens, farmers, labourers, homemakers, and elderly persons \
who find official government portals difficult to use and understand.
• Speak in extremely simple, everyday, respectful language.
• NEVER use complex legal, administrative, or bureaucratic words.
• Instead of "प्रत्यक्ष लाभ अंतरण", say "सीधे आपके बैंक खाते में पैसे".
• Instead of "पात्रता मानदंड", say "यह योजना किसके लिए है".
• Instead of "संलग्नक/दस्तावेज़", say "ज़रूरी कागज़".

━━━ DOCUMENT CONTEXT RETENTION (CRITICAL) ━━━
If the user uploads a document (such as Aadhaar card, Ration card, BPL certificate, \
or land records), and details have been extracted:
• REMEMBER these details throughout the entire conversation.
• NEVER ask the user for information that is already visible in their document (like name, age, state, or address).
• Confirm what you found politely: "मुझे आपके कागज़ात से पता चला कि आपकी उम्र ... है और आप ... राज्य से हैं।"
• Immediately use these verified details to evaluate eligible welfare schemes.

━━━ CONVERSATION FLOW ━━━
1. Greet the citizen warmly in their language.
2. If they need to provide details, ask only 1 or 2 simple questions at a time in plain words.
3. Once you know basic details (age, occupation, state, approximate income):
   Call the **check_eligibility** tool immediately.
4. Explain the matched schemes in simple terms:
   • **योजना का नाम (Scheme Name)**
   • **आपको क्या फायदा मिलेगा (What you get - exact money or benefit in plain terms)**
   • **आपको क्यों मिल सकता है (Why you qualify)**
   • **कौन से कागज़ चाहिए (Simple papers needed)**
   • **आवेदन कहाँ करना है (Where to go: nearest CSC / जन सेवा केंद्र, बैंक, या डाकघर)**
5. Only share schemes that are officially verified from the tool. Never invent schemes.

━━━ LANGUAGE RULES ━━━
• Always reply in the exact language the user is speaking or has selected (Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Punjabi, Odia, Malayalam, English).
• Keep answers short, clear, and easy to understand when read aloud.
"""


ELIGIBILITY_TOOL = {
    "type": "function",
    "function": {
        "name": "check_eligibility",
        "description": (
            "Check which government welfare schemes the user is eligible for "
            "based on their profile information collected during the conversation. "
            "Call this once you have gathered enough details (at minimum: age, state, "
            "occupation, and approximate income)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "age": {
                    "type": "integer",
                    "description": "User's age in years",
                },
                "gender": {
                    "type": "string",
                    "enum": ["male", "female", "other"],
                    "description": "User's gender",
                },
                "state": {
                    "type": "string",
                    "description": "Indian state of residence (e.g. 'Maharashtra', 'Tamil Nadu')",
                },
                "rural_urban": {
                    "type": "string",
                    "enum": ["rural", "urban"],
                    "description": "Whether the user lives in a rural or urban area",
                },
                "caste_category": {
                    "type": "string",
                    "enum": ["general", "obc", "sc", "st"],
                    "description": "Caste category",
                },
                "annual_income": {
                    "type": "integer",
                    "description": "Approximate annual family income in INR",
                },
                "occupation": {
                    "type": "string",
                    "enum": [
                        "farmer",
                        "student",
                        "labourer",
                        "self_employed",
                        "salaried",
                        "unemployed",
                        "homemaker",
                        "street_vendor",
                        "artisan",
                    ],
                    "description": "Primary occupation",
                },
                "is_bpl": {
                    "type": "boolean",
                    "description": "Whether the family holds a BPL card",
                },
                "land_ownership": {
                    "type": "boolean",
                    "description": "Whether they own agricultural land",
                },
                "land_hectares": {
                    "type": "number",
                    "description": "Area of agricultural land in hectares",
                },
                "marital_status": {
                    "type": "string",
                    "enum": ["single", "married", "widowed", "divorced"],
                    "description": "Marital status",
                },
                "has_children": {
                    "type": "boolean",
                    "description": "Whether the user has children",
                },
                "num_daughters": {
                    "type": "integer",
                    "description": "Number of daughters",
                },
                "daughter_ages": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Ages of daughters",
                },
                "is_pregnant": {
                    "type": "boolean",
                    "description": "Whether the user or spouse is currently pregnant",
                },
                "is_disabled": {
                    "type": "boolean",
                    "description": "Whether the user has a disability",
                },
                "disability_percentage": {
                    "type": "integer",
                    "description": "Disability percentage (0-100)",
                },
                "is_widow": {
                    "type": "boolean",
                    "description": "Whether the user is a widow",
                },
                "is_student": {
                    "type": "boolean",
                    "description": "Whether the user is currently a student",
                },
                "education_level": {
                    "type": "string",
                    "enum": [
                        "none",
                        "primary",
                        "secondary",
                        "higher_secondary",
                        "graduate",
                        "postgraduate",
                    ],
                    "description": "Highest education level",
                },
                "is_income_tax_payer": {
                    "type": "boolean",
                    "description": "Whether the user files income tax returns",
                },
                "is_government_employee": {
                    "type": "boolean",
                    "description": "Whether the user is a government employee",
                },
                "is_street_vendor": {
                    "type": "boolean",
                    "description": "Whether the user is a street vendor with a certificate",
                },
                "is_artisan": {
                    "type": "boolean",
                    "description": "Whether the user is a traditional artisan/craftworker",
                },
                "has_lpg_connection": {
                    "type": "boolean",
                    "description": "Whether the household already has an LPG connection",
                },
                "has_pucca_house": {
                    "type": "boolean",
                    "description": "Whether the user owns a pucca (permanent) house",
                },
            },
            "required": ["age", "state", "occupation", "annual_income"],
        },
    },
}
