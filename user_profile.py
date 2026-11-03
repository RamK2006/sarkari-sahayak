"""User profile data model for Sarkari Sahayak."""

from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """Structured representation of a citizen's profile for scheme eligibility matching."""

    age: Optional[int] = Field(None, description="Age in years")
    gender: Optional[str] = Field(None, description="male / female / other")
    state: Optional[str] = Field(None, description="Indian state of residence")
    rural_urban: Optional[str] = Field(None, description="rural / urban")
    caste_category: Optional[str] = Field(None, description="general / obc / sc / st")
    annual_income: Optional[int] = Field(None, description="Approximate annual family income in INR")
    occupation: Optional[str] = Field(None, description="farmer / student / labourer / self_employed / salaried / unemployed / homemaker")
    is_bpl: Optional[bool] = Field(None, description="Whether the family holds a BPL card")
    land_ownership: Optional[bool] = Field(None, description="Whether they own agricultural land")
    land_hectares: Optional[float] = Field(None, description="Area of land owned in hectares")
    marital_status: Optional[str] = Field(None, description="single / married / widowed / divorced")
    has_children: Optional[bool] = Field(None, description="Whether the user has children")
    num_children: Optional[int] = Field(None, description="Total number of children")
    num_daughters: Optional[int] = Field(None, description="Number of daughters")
    daughter_ages: Optional[List[int]] = Field(None, description="Ages of daughters")
    is_pregnant: Optional[bool] = Field(None, description="Whether the user or spouse is pregnant")
    is_disabled: Optional[bool] = Field(None, description="Whether the user has a disability")
    disability_percentage: Optional[int] = Field(None, description="Disability percentage if applicable")
    is_widow: Optional[bool] = Field(None, description="Whether the user is a widow")
    is_senior_citizen: Optional[bool] = Field(None, description="Whether age >= 60")
    is_student: Optional[bool] = Field(None, description="Whether the user is a student")
    education_level: Optional[str] = Field(None, description="primary / secondary / higher_secondary / graduate / postgraduate / none")
    has_bank_account: Optional[bool] = Field(None, description="Whether the user has a bank account")
    has_aadhaar: Optional[bool] = Field(None, description="Whether the user has Aadhaar")
    has_ration_card: Optional[bool] = Field(None, description="Whether the user has a ration card")
    is_income_tax_payer: Optional[bool] = Field(None, description="Whether the user files income tax")
    is_government_employee: Optional[bool] = Field(None, description="Whether the user is a government employee")
    is_street_vendor: Optional[bool] = Field(None, description="Whether the user is a street vendor")
    is_artisan: Optional[bool] = Field(None, description="Whether the user is a traditional artisan/craftworker")
    artisan_trade: Optional[str] = Field(None, description="Specific artisan trade if applicable")
    has_lpg_connection: Optional[bool] = Field(None, description="Whether the household has an LPG connection")
    has_pucca_house: Optional[bool] = Field(None, description="Whether the user lives in a pucca house")
    language: Optional[str] = Field(None, description="User's preferred language code (e.g. hi-IN)")

    def completeness_score(self) -> float:
        """Return fraction of key fields that are filled (0.0 - 1.0)."""
        key_fields = [
            "age", "gender", "state", "rural_urban", "annual_income", "occupation",
        ]
        filled = sum(1 for f in key_fields if getattr(self, f) is not None)
        return filled / len(key_fields)

    def summary(self) -> str:
        """Human-readable summary of filled profile fields."""
        lines = []
        for field_name, field_info in self.model_fields.items():
            val = getattr(self, field_name)
            if val is not None:
                label = field_info.description or field_name
                lines.append(f"- {label}: {val}")
        return "\n".join(lines) if lines else "No information collected yet."
