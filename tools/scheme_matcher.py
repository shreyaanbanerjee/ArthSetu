"""Government welfare scheme matching for ArthSetu users."""

from __future__ import annotations

from typing import Any


SCHEMES: list[dict[str, Any]] = [
    {
        "id": "PM_KISAN",
        "name": "PM-KISAN Samman Nidhi",
        "category": "farmer_income_support",
        "benefit": "Income support of Rs 6,000 per year for eligible farmer families.",
        "eligibility": {"occupation": ["farmer"], "land_ownership": True},
        "documents": ["Aadhaar", "Land record", "Bank account"],
        "apply_url": "https://pmkisan.gov.in",
        "state": "ALL",
    },
    {
        "id": "PMFBY",
        "name": "Pradhan Mantri Fasal Bima Yojana",
        "category": "crop_insurance",
        "benefit": "Crop insurance against notified natural risks and yield loss.",
        "eligibility": {"occupation": ["farmer"]},
        "documents": ["Aadhaar", "Land/crop record", "Bank account"],
        "apply_url": "https://pmfby.gov.in",
        "state": "ALL",
    },
    {
        "id": "KCC",
        "name": "Kisan Credit Card",
        "category": "agriculture_credit",
        "benefit": "Formal short-term credit for crop and allied activities.",
        "eligibility": {"occupation": ["farmer"], "land_ownership": True},
        "documents": ["Aadhaar", "Land records", "Bank account", "Photograph"],
        "apply_url": "https://www.nabard.org",
        "state": "ALL",
    },
    {
        "id": "E_SHRAM",
        "name": "e-Shram Card",
        "category": "unorganised_worker",
        "benefit": "National database registration and access path for social security schemes.",
        "eligibility": {"occupation": ["gig_worker", "daily_wage", "farmer", "self_employed"], "not_epf_member": True},
        "documents": ["Aadhaar", "Bank account", "Mobile number"],
        "apply_url": "https://eshram.gov.in",
        "state": "ALL",
    },
    {
        "id": "APY",
        "name": "Atal Pension Yojana",
        "category": "pension",
        "benefit": "Defined pension from age 60 for eligible subscribers.",
        "eligibility": {"age_min": 18, "age_max": 40, "has_bank_account": True, "not_income_taxpayer": True},
        "documents": ["Aadhaar", "Bank account", "Mobile number"],
        "apply_url": "https://www.npscra.nsdl.co.in",
        "state": "ALL",
    },
    {
        "id": "PMJJBY",
        "name": "Pradhan Mantri Jeevan Jyoti Bima Yojana",
        "category": "life_insurance",
        "benefit": "Low-cost life insurance cover for eligible bank account holders.",
        "eligibility": {"age_min": 18, "age_max": 50, "has_bank_account": True},
        "documents": ["Bank account", "Aadhaar", "Consent form"],
        "apply_url": "https://jansuraksha.gov.in",
        "state": "ALL",
    },
    {
        "id": "PMSBY",
        "name": "Pradhan Mantri Suraksha Bima Yojana",
        "category": "accident_insurance",
        "benefit": "Low-cost accident insurance cover for eligible bank account holders.",
        "eligibility": {"age_min": 18, "age_max": 70, "has_bank_account": True},
        "documents": ["Bank account", "Aadhaar", "Consent form"],
        "apply_url": "https://jansuraksha.gov.in",
        "state": "ALL",
    },
    {
        "id": "SUKANYA",
        "name": "Sukanya Samriddhi Yojana",
        "category": "girl_child_savings",
        "benefit": "Small savings scheme for a girl child below 10 years.",
        "eligibility": {"has_daughter_below_10": True},
        "documents": ["Birth certificate", "Guardian KYC", "Initial deposit"],
        "apply_url": "https://www.indiapost.gov.in",
        "state": "ALL",
    },
    {
        "id": "NPS_VATSALYA",
        "name": "NPS Vatsalya",
        "category": "child_pension_savings",
        "benefit": "Parent/guardian-led pension savings account for minors.",
        "eligibility": {"has_child": True},
        "documents": ["Child proof of age", "Guardian KYC", "Bank account"],
        "apply_url": "https://enps.nsdl.com",
        "state": "ALL",
    },
    {
        "id": "UDID",
        "name": "Unique Disability ID",
        "category": "disability_identity",
        "benefit": "Disability certificate and ID for accessing disability benefits.",
        "eligibility": {"has_disability": True},
        "documents": ["Aadhaar", "Medical records", "Photo"],
        "apply_url": "https://www.swavlambancard.gov.in",
        "state": "ALL",
    },
    {
        "id": "ADIP",
        "name": "ADIP Scheme",
        "category": "disability_aid",
        "benefit": "Assistive devices for eligible persons with disabilities.",
        "eligibility": {"has_disability": True, "income_max_inr": 240000},
        "documents": ["Disability certificate", "Income certificate", "Aadhaar"],
        "apply_url": "https://disabilityaffairs.gov.in",
        "state": "ALL",
    },
    {
        "id": "PM_SVANIDHI",
        "name": "PM SVANidhi",
        "category": "street_vendor_credit",
        "benefit": "Working capital loan pathway for eligible street vendors.",
        "eligibility": {"occupation": ["street_vendor", "self_employed"]},
        "documents": ["Certificate of vending or recommendation letter", "Aadhaar", "Bank account"],
        "apply_url": "https://pmsvanidhi.mohua.gov.in",
        "state": "ALL",
    },
]


def match_schemes(profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Return eligible welfare schemes with transparent matching reasons."""
    occupation = str(profile.get("occupation", "")).strip().lower()
    age = _as_int(profile.get("age"), 30)
    annual_income = _as_float(profile.get("monthly_income_inr"), 0.0) * 12
    has_bank = _as_bool(profile.get("has_bank_account"), True)
    has_disability = _as_bool(profile.get("has_disability"), False)
    land_ownership = _as_bool(profile.get("land_ownership"), False)
    has_daughter_below_10 = _as_bool(profile.get("has_daughter_below_10"), False)
    has_child = _as_bool(profile.get("has_child"), has_daughter_below_10)
    not_epf = _as_bool(profile.get("not_epf_member"), True)
    not_taxpayer = _as_bool(profile.get("not_income_taxpayer"), annual_income < 300000)

    facts = {
        "occupation": occupation,
        "age": age,
        "income_max_inr": annual_income,
        "has_bank_account": has_bank,
        "has_disability": has_disability,
        "land_ownership": land_ownership,
        "has_daughter_below_10": has_daughter_below_10,
        "has_child": has_child,
        "not_epf_member": not_epf,
        "not_income_taxpayer": not_taxpayer,
    }

    matches: list[dict[str, Any]] = []
    for scheme in SCHEMES:
        ok, reasons = _eligible(scheme["eligibility"], facts)
        if ok:
            matches.append(
                {
                    "scheme_id": scheme["id"],
                    "name": scheme["name"],
                    "category": scheme["category"],
                    "benefit": scheme["benefit"],
                    "documents": scheme["documents"],
                    "apply_url": scheme["apply_url"],
                    "state": scheme["state"],
                    "match_reasons": reasons,
                }
            )
    return matches


def _eligible(criteria: dict[str, Any], facts: dict[str, Any]) -> tuple[bool, list[str]]:
    """Evaluate one scheme's eligibility criteria."""
    reasons: list[str] = []
    for key, expected in criteria.items():
        if key == "occupation":
            if facts["occupation"] not in expected:
                return False, []
            reasons.append(f"occupation is {facts['occupation']}")
        elif key == "age_min":
            if facts["age"] < expected:
                return False, []
            reasons.append(f"age is at least {expected}")
        elif key == "age_max":
            if facts["age"] > expected:
                return False, []
            reasons.append(f"age is at most {expected}")
        elif key == "income_max_inr":
            if facts["income_max_inr"] > expected:
                return False, []
            reasons.append(f"annual income is within Rs {expected}")
        elif facts.get(key) != expected:
            return False, []
        else:
            reasons.append(key.replace("_", " "))
    return True, reasons


def _as_bool(value: Any, default: bool) -> bool:
    """Convert common truthy/falsy values."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "haan", "ha", "हो"}


def _as_int(value: Any, default: int) -> int:
    """Convert a value to int with a default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float) -> float:
    """Convert a value to float with a default."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
