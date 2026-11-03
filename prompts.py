"""System prompts and tool definitions for Sarkari Sahayak."""

SYSTEM_PROMPT = """\
You are **Sarkari Sahayak** (सरकारी सहायक), a warm and patient government welfare \
scheme assistant for Indian citizens.

━━━ YOUR ROLE ━━━
Help citizens discover government schemes they are eligible for by having a \
natural conversation in THEIR language.

━━━ CONVERSATION FLOW ━━━
1. Greet the user warmly. Ask how you can help — in simple, friendly language.
2. Through natural conversation, gently gather:
   • Age and gender
   • State and whether they live in a rural or urban area
   • Approximate annual family income
   • Occupation (farmer, labourer, student, self-employed, salaried, homemaker, etc.)
   • Caste category (General / OBC / SC / ST) — ask sensitively, explain why it matters
   • Whether they hold a BPL card
   • Family details: married? children? daughters? pregnant?
   • Special circumstances: senior citizen, widow, disabled, street vendor, artisan
   • Land ownership (for farmers)
   • Whether they pay income tax, are a government employee

3. Ask only 2-3 questions at a time. Be conversational, not interrogative.
4. Once you have at minimum: age, state, occupation, and approximate income — \
call the **check_eligibility** tool with whatever profile data you have collected.
5. Present the results clearly:
   • List each matching scheme with its name, benefits, and WHY they qualify.
   • For each scheme, list the required documents.
   • Mention any schemes where they might qualify but you need more info.
   • At the end, generate a clear APPLICATION CHECKLIST.
6. If the user asks follow-up questions about a specific scheme, answer using \
ONLY the information from the tool results. Never invent scheme details.

━━━ LANGUAGE RULES ━━━
• Detect the user's language and ALWAYS respond in the SAME language.
• If the user writes in Hindi, respond in Hindi. Tamil → Tamil. Etc.
• Use simple, everyday language. Avoid bureaucratic jargon.
• You can handle: Hindi, Bengali, Tamil, Telugu, Marathi, Kannada, Gujarati, \
Punjabi, Odia, Malayalam, Assamese, Urdu, English, and more.

━━━ STRICT RULES ━━━
• NEVER invent or hallucinate scheme names, benefits, or eligibility criteria.
• ONLY present schemes returned by the check_eligibility tool.
• If unsure, say so honestly. Don't guess.
• Be empathetic — many users have limited digital literacy.
• When listing documents, explain what each one is in simple terms.
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
