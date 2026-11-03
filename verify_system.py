import eligibility
import json
import sarvam_client
from user_profile import UserProfile

schemes = eligibility.load_schemes()
print(f"Loaded {len(schemes)} schemes successfully.")

test_profile = {
    "age": 35,
    "occupation": "farmer",
    "annual_income": 120000,
    "state": "Uttar Pradesh",
    "rural_urban": "rural",
    "land_ownership": True,
    "is_income_tax_payer": False,
    "is_government_employee": False
}

results = eligibility.check_eligibility(test_profile, schemes)
eligible = [r for r in results if r["eligible"]]
print(f"Eligible schemes found: {len(eligible)}")
for e in eligible:
    print(f" - {e['scheme_name']}: {e['benefits']}")

formatted = eligibility.format_results_for_llm(results)
print("\nSample formatted output snippet:")
print(formatted[:300])

client = sarvam_client.SarvamClient()
print("\nSarvamClient initialized successfully.")

# Test language detection with actual Sarvam API
detected = client.detect_language("नमस्ते, मुझे सरकारी योजनाओं के बारे में जानना है")
print(f"Language detection test: {detected}")
