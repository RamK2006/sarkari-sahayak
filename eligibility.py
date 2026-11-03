"""Deterministic eligibility checker for government schemes.

This module matches a user profile against scheme eligibility rules.
NO LLM involvement — pure rule-based matching so results are verifiable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class MatchResult:
    """Result of matching one scheme against a user profile."""

    scheme_id: str
    scheme_name: str
    scheme_name_hi: str
    eligible: bool
    benefits: str
    reasons_qualified: list = field(default_factory=list)
    reasons_disqualified: list = field(default_factory=list)
    missing_info: list = field(default_factory=list)
    documents_required: list = field(default_factory=list)
    application_url: str = ""
    source_url: str = ""
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "scheme_id": self.scheme_id,
            "scheme_name": self.scheme_name,
            "scheme_name_hi": self.scheme_name_hi,
            "eligible": self.eligible,
            "benefits": self.benefits,
            "description": self.description,
            "reasons_qualified": self.reasons_qualified,
            "reasons_disqualified": self.reasons_disqualified,
            "missing_info": self.missing_info,
            "documents_required": self.documents_required,
            "application_url": self.application_url,
            "source_url": self.source_url,
        }


def load_schemes(path: Optional[str] = None) -> List[Dict]:
    """Load scheme database from JSON file."""
    if path is None:
        path = str(Path(__file__).parent / "schemes_db.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get(profile: Dict, key: str, default=None):
    """Safely get a value from the profile dict."""
    val = profile.get(key)
    if val is None:
        return default
    return val


def check_eligibility(profile: Dict[str, Any], schemes: Optional[List[Dict]] = None) -> List[Dict]:
    """
    Check which government schemes the user is eligible for.

    Args:
        profile: Dict of user profile fields (from the tool call).
        schemes: Optional list of scheme dicts. Loads from schemes_db.json if None.

    Returns:
        List of MatchResult dicts, sorted with eligible schemes first.
    """
    if schemes is None:
        schemes = load_schemes()

    results = []
    for scheme in schemes:
        result = _match_scheme(profile, scheme)
        results.append(result)

    # Sort: eligible first, then by number of qualifying reasons (desc)
    results.sort(key=lambda r: (-int(r.eligible), -len(r.reasons_qualified), len(r.missing_info)))

    return [r.to_dict() for r in results]


def _match_scheme(profile: Dict[str, Any], scheme: Dict) -> MatchResult:
    """Match a single scheme against the user profile."""
    rules = scheme.get("eligibility", {})
    result = MatchResult(
        scheme_id=scheme["id"],
        scheme_name=scheme["name"],
        scheme_name_hi=scheme.get("name_hi", scheme["name"]),
        eligible=True,  # will be set to False if disqualified or critical info is missing
        benefits=scheme.get("benefits", ""),
        description=scheme.get("description", ""),
        documents_required=scheme.get("documents_required", []),
        application_url=scheme.get("application_url", ""),
        source_url=scheme.get("source_url", ""),
    )

    age = _get(profile, "age")
    gender = _get(profile, "gender")
    if gender:
        gender = str(gender).lower()
    occupation = _get(profile, "occupation")
    if occupation:
        occupation = str(occupation).lower()
    annual_income = _get(profile, "annual_income")
    state = _get(profile, "state")
    rural_urban = _get(profile, "rural_urban")
    if rural_urban:
        rural_urban = str(rural_urban).lower()
    caste = _get(profile, "caste_category")
    if caste:
        caste = str(caste).lower()
    is_bpl = _get(profile, "is_bpl")
    land_ownership = _get(profile, "land_ownership")
    is_widow = _get(profile, "is_widow")
    is_pregnant = _get(profile, "is_pregnant")
    is_student = _get(profile, "is_student")
    if is_student is None and occupation == "student":
        is_student = True
    is_tax_payer = _get(profile, "is_income_tax_payer")
    is_govt_employee = _get(profile, "is_government_employee")
    is_street_vendor = _get(profile, "is_street_vendor")
    if is_street_vendor is None and occupation == "street_vendor":
        is_street_vendor = True
    is_artisan = _get(profile, "is_artisan")
    if is_artisan is None and occupation == "artisan":
        is_artisan = True
    has_lpg = _get(profile, "has_lpg_connection")
    has_pucca_house = _get(profile, "has_pucca_house")
    has_children = _get(profile, "has_children")
    num_daughters = _get(profile, "num_daughters")
    daughter_ages = _get(profile, "daughter_ages")
    marital_status = _get(profile, "marital_status")
    if marital_status:
        marital_status = str(marital_status).lower()

    # ── Exclusions First ──────────────────────────────────────────────
    if rules.get("excluded_income_tax_payer") and is_tax_payer is True:
        result.eligible = False
        result.reasons_disqualified.append("Income tax payers are excluded from this scheme")

    if rules.get("excluded_government_employee") and is_govt_employee is True:
        result.eligible = False
        result.reasons_disqualified.append("Government employees are excluded from this scheme")

    # ── Age checks ────────────────────────────────────────────────────
    min_age = rules.get("min_age")
    max_age = rules.get("max_age")
    if min_age is not None:
        if age is None:
            result.eligible = False
            result.missing_info.append(f"Age verification needed (minimum {min_age} years)")
        elif age < min_age:
            result.eligible = False
            result.reasons_disqualified.append(f"Minimum age is {min_age}, user is {age}")
        else:
            result.reasons_qualified.append(f"Age {age} meets minimum requirement ({min_age}+)")

    if max_age is not None:
        if age is None:
            result.eligible = False
            result.missing_info.append(f"Age verification needed (maximum {max_age} years)")
        elif age > max_age:
            result.eligible = False
            result.reasons_disqualified.append(f"Maximum age is {max_age}, user is {age}")
        else:
            result.reasons_qualified.append(f"Age {age} is within maximum limit (≤ {max_age})")

    # ── Occupation checks ─────────────────────────────────────────────
    required_occupations = rules.get("occupation")
    if required_occupations:
        if occupation is None:
            result.eligible = False
            result.missing_info.append(f"Occupation needed (scheme is for: {', '.join(required_occupations)})")
        elif occupation in required_occupations:
            result.reasons_qualified.append(f"Occupation '{occupation}' is directly eligible")
        else:
            result.eligible = False
            result.reasons_disqualified.append(
                f"Scheme requires occupation to be one of: {', '.join(required_occupations)}. Current occupation: {occupation}"
            )

    # ── Land ownership ────────────────────────────────────────────────
    if rules.get("land_ownership_required"):
        if land_ownership is None:
            result.eligible = False
            result.missing_info.append("Land ownership record (Khasra/Khatauni) is required")
        elif land_ownership:
            result.reasons_qualified.append("Owns cultivable agricultural land")
        else:
            result.eligible = False
            result.reasons_disqualified.append("Requires ownership of cultivable agricultural land")

    # ── Rural / Urban ─────────────────────────────────────────────────
    required_area = rules.get("rural_urban")
    if required_area:
        if rural_urban is None:
            result.missing_info.append(f"Location type ({required_area}) verification needed")
        elif rural_urban == required_area:
            result.reasons_qualified.append(f"Located in {required_area} area as required")
        else:
            result.eligible = False
            result.reasons_disqualified.append(
                f"Scheme is strictly for {required_area} areas (user is in {rural_urban})"
            )

    # ── BPL / Deprived ────────────────────────────────────────────────
    if rules.get("is_bpl_or_deprived"):
        if is_bpl is True:
            result.reasons_qualified.append("Holds valid BPL / Antyodaya / priority ration card")
        elif is_bpl is False:
            if annual_income is not None and annual_income <= 200000:
                result.reasons_qualified.append(f"Income ₹{annual_income:,} qualifies as low-income/economically weaker section")
            else:
                result.eligible = False
                result.reasons_disqualified.append("Requires BPL status or low-income threshold")
        else:
            # is_bpl is None
            if annual_income is not None and annual_income <= 200000:
                result.reasons_qualified.append(f"Income ₹{annual_income:,} qualifies as low-income section")
            else:
                result.missing_info.append("BPL card or proof of economically deprived background needed")

    # ── Income limits ─────────────────────────────────────────────────
    max_income = rules.get("max_annual_income")
    if max_income is not None:
        if annual_income is None:
            result.missing_info.append(f"Annual family income check needed (max ₹{max_income:,})")
        elif annual_income <= max_income:
            result.reasons_qualified.append(f"Annual income ₹{annual_income:,} is within ceiling of ₹{max_income:,}")
        else:
            result.eligible = False
            result.reasons_disqualified.append(f"Income ₹{annual_income:,} exceeds maximum ceiling of ₹{max_income:,}")

    # EWS / LIG income checks (PMAY-U)
    max_income_ews = rules.get("max_annual_income_ews")
    max_income_lig = rules.get("max_annual_income_lig")
    if max_income_ews or max_income_lig:
        if annual_income is None:
            result.missing_info.append("Income slab needed for EWS (≤ ₹3 Lakh) or LIG (≤ ₹6 Lakh)")
        elif max_income_ews and annual_income <= max_income_ews:
            result.reasons_qualified.append(f"Qualifies under EWS slab (income ₹{annual_income:,} ≤ ₹{max_income_ews:,})")
        elif max_income_lig and annual_income <= max_income_lig:
            result.reasons_qualified.append(f"Qualifies under LIG slab (income ₹{annual_income:,} ≤ ₹{max_income_lig:,})")
        elif max_income_lig and annual_income > max_income_lig:
            result.eligible = False
            result.reasons_disqualified.append(f"Income ₹{annual_income:,} exceeds LIG upper limit of ₹{max_income_lig:,}")

    # Scholarship income check
    max_income_sc_st = rules.get("max_annual_income_sc_st")
    max_income_obc = rules.get("max_annual_income_obc")
    if max_income_sc_st or max_income_obc:
        if caste in ("sc", "st") and max_income_sc_st:
            if annual_income is not None and annual_income <= max_income_sc_st:
                result.reasons_qualified.append(f"Income ₹{annual_income:,} within SC/ST ceiling (₹{max_income_sc_st:,})")
            elif annual_income is not None:
                result.eligible = False
                result.reasons_disqualified.append(f"Income ₹{annual_income:,} exceeds SC/ST ceiling (₹{max_income_sc_st:,})")
        elif caste == "obc" and max_income_obc:
            if annual_income is not None and annual_income <= max_income_obc:
                result.reasons_qualified.append(f"Income ₹{annual_income:,} within OBC ceiling (₹{max_income_obc:,})")
            elif annual_income is not None:
                result.eligible = False
                result.reasons_disqualified.append(f"Income ₹{annual_income:,} exceeds OBC ceiling (₹{max_income_obc:,})")

    # ── Gender preference / requirement ──────────────────────────────
    gender_pref = rules.get("gender_preference")
    if gender_pref:
        if gender is None:
            result.missing_info.append(f"Applicant is expected to be {gender_pref} or female head of family")
        elif gender == gender_pref:
            result.reasons_qualified.append(f"Applicant gender ({gender}) matches primary beneficiary focus")
        else:
            if rules.get("is_widow") or rules.get("is_pregnant_or_lactating"):
                result.eligible = False
                result.reasons_disqualified.append(f"Only {gender_pref} applicants qualify for this benefit")
            else:
                result.missing_info.append(f"Scheme is granted in name of female member of household")

    # ── Pucca house ───────────────────────────────────────────────────
    if rules.get("has_pucca_house") is False:
        if has_pucca_house is None:
            result.missing_info.append("Confirmation needed: do you currently own a pucca (brick/concrete) house?")
        elif has_pucca_house is True:
            result.eligible = False
            result.reasons_disqualified.append("Beneficiaries owning a pucca house are not eligible for housing assistance")
        else:
            result.reasons_qualified.append("Does not own a permanent pucca house")

    # ── LPG connection ────────────────────────────────────────────────
    if rules.get("has_lpg_connection") is False:
        if has_lpg is None:
            result.missing_info.append("Check if any LPG connection exists in household")
        elif has_lpg is True:
            result.eligible = False
            result.reasons_disqualified.append("Household already has an existing LPG connection")
        else:
            result.reasons_qualified.append("No existing LPG connection in household")

    # ── Target beneficiary flags ──────────────────────────────────────
    if rules.get("is_artisan"):
        if is_artisan is True:
            result.reasons_qualified.append("Works as a traditional artisan or craftsperson")
        elif is_artisan is False or (occupation and occupation not in ["artisan"]):
            result.eligible = False
            result.reasons_disqualified.append("Specifically reserved for traditional artisans and craftspersons")
        else:
            result.eligible = False
            result.missing_info.append("Requires being a traditional craftsperson/artisan (e.g. carpenter, blacksmith, potter, tailor)")

    if rules.get("is_street_vendor"):
        if is_street_vendor is True:
            result.reasons_qualified.append("Operates as a registered street vendor")
        elif is_street_vendor is False or (occupation and occupation not in ["street_vendor"]):
            result.eligible = False
            result.reasons_disqualified.append("Exclusively for urban/peri-urban street vendors")
        else:
            result.eligible = False
            result.missing_info.append("Requires operating as a street vendor / hawker")

    if rules.get("is_student"):
        if is_student is True:
            result.reasons_qualified.append("Currently enrolled student")
        elif is_student is False or (occupation and occupation not in ["student"]):
            result.eligible = False
            result.reasons_disqualified.append("Specifically for enrolled students")
        else:
            result.eligible = False
            result.missing_info.append("Requires active student enrollment in recognised institution")

    if rules.get("caste_categories"):
        required_castes = rules.get("caste_categories")
        if caste is None:
            result.eligible = False
            result.missing_info.append(f"Caste category required ({', '.join(c.upper() for c in required_castes)})")
        elif caste in required_castes:
            result.reasons_qualified.append(f"Category {caste.upper()} is eligible")
        else:
            result.eligible = False
            result.reasons_disqualified.append(f"Restricted to {', '.join(c.upper() for c in required_castes)} categories")

    if rules.get("is_widow"):
        if is_widow is True or marital_status == "widowed":
            result.reasons_qualified.append("Widowed citizen eligible for social security pension")
        elif is_widow is False or (marital_status and marital_status != "widowed") or gender == "male":
            result.eligible = False
            result.reasons_disqualified.append("Exclusively for widows")
        else:
            result.eligible = False
            result.missing_info.append("Requires widow status (husband's death certificate needed)")

    if rules.get("is_pregnant_or_lactating"):
        if is_pregnant is True:
            result.reasons_qualified.append("Pregnant woman / lactating mother")
        elif is_pregnant is False or gender == "male":
            result.eligible = False
            result.reasons_disqualified.append("Exclusively for pregnant women or lactating mothers")
        else:
            result.eligible = False
            result.missing_info.append("Applicable for pregnant women or lactating mothers")

    if rules.get("has_daughter"):
        max_daughter_age = rules.get("max_daughter_age", 10)
        if num_daughters is not None and num_daughters > 0:
            if daughter_ages:
                valid_daughters = [a for a in daughter_ages if a <= max_daughter_age]
                if valid_daughters:
                    result.reasons_qualified.append(f"Has daughter aged ≤ {max_daughter_age} years")
                else:
                    result.eligible = False
                    result.reasons_disqualified.append(f"Daughter must be 10 years or younger (current ages: {daughter_ages})")
            else:
                result.reasons_qualified.append(f"Has {num_daughters} daughter(s)")
        elif has_children is False or num_daughters == 0:
            result.eligible = False
            result.reasons_disqualified.append("Requires having a girl child aged 10 or younger")
        else:
            result.eligible = False
            result.missing_info.append("Requires having a girl child aged 10 or younger")

    return result


def format_results_for_llm(results: List[Dict]) -> str:
    """Format eligibility results as a string for the LLM to present to the user."""
    eligible = [r for r in results if r["eligible"]]
    maybe = [r for r in results if not r["eligible"] and r["missing_info"] and not r["reasons_disqualified"]]

    lines = []
    lines.append(f"=== VERIFIED GOVERNMENT SCHEME MATCHES ===\n")
    lines.append(f"CONFIRMED ELIGIBLE SCHEMES ({len(eligible)}):\n")

    if not eligible:
        lines.append("No schemes currently have all eligibility criteria confirmed.\n")

    for i, r in enumerate(eligible, 1):
        lines.append(f"\n--- {i}. {r['scheme_name']} ({r['scheme_name_hi']}) ---")
        lines.append(f"Benefits: {r['benefits']}")
        lines.append(f"Description: {r['description']}")
        lines.append(f"Why you qualify:")
        for reason in r["reasons_qualified"]:
            lines.append(f"  ✓ {reason}")
        if r["missing_info"]:
            lines.append(f"Additional notes / verification:")
            for info in r["missing_info"]:
                lines.append(f"  ℹ {info}")
        lines.append(f"Required Documents: {', '.join(r['documents_required'])}")
        lines.append(f"Official Application Portal: {r['application_url']}")
        lines.append(f"Official Guidelines: {r['source_url']}")

    if maybe:
        lines.append(f"\n\nPOTENTIALLY ELIGIBLE (Pending Information) — {len(maybe)} schemes:")
        for r in maybe:
            lines.append(f"\n• {r['scheme_name']} ({r['scheme_name_hi']})")
            lines.append(f"  Benefits: {r['benefits']}")
            lines.append(f"  Information needed to confirm:")
            for info in r["missing_info"]:
                lines.append(f"    ? {info}")

    return "\n".join(lines)
