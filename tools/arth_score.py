"""Arth Score calculation."""

from __future__ import annotations

from typing import Any


def calculate_arth_score(profile: dict[str, Any], latest_state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Calculate a five-dimension financial resilience score out of 100.
    
    Dynamically adjusts based on the user's conversational responses (profile completeness)
    and their actual financial health (income/expense/debt ratios).
    """
    income = _float(profile.get("monthly_income_inr"), 0.0)
    expenses = _float(profile.get("monthly_expenses_inr"), 0.0)
    emergency = _float(profile.get("emergency_fund_inr"), 0.0)
    debt_emi = _float(profile.get("monthly_debt_emi_inr"), 0.0)
    has_bank = bool(profile.get("has_bank_account", False))
    has_informal_debt = bool(profile.get("has_informal_debt", False))
    
    # 1. Cashflow Stability (0-20): Based on income vs expenses.
    if income == 0 and expenses == 0:
        stability = 5.0 # Unknown baseline
    else:
        savings_rate = ((income - expenses) / income * 100) if income > 0 else 0
        stability = min(20.0, max(0.0, 10.0 + (savings_rate / 5.0)))
        
    # 2. Risk Protection (0-20): Based on emergency fund ratio + banking
    if expenses > 0:
        months_saved = emergency / expenses
    else:
        months_saved = 0
    protection = min(20.0, (months_saved * 5.0) + (5.0 if has_bank else 0.0))
    if emergency == 0 and not has_bank:
        protection = 2.0 # Baseline

    # 3. Debt Health (0-20): Based on Debt-to-Income (DTI) ratio
    if income == 0 and debt_emi == 0:
        debt_health = 10.0 # Unknown baseline
    else:
        dti = (debt_emi / income) if income > 0 else 1.0 # 100% DTI if no income but has debt
        health_score = 20.0 - (dti * 40.0) # 50% DTI = 0 points
        debt_health = max(0.0, health_score - (5.0 if has_informal_debt else 0.0))
        
    # 4. Financial Awareness (0-20): Based on how much profile info they've shared in chat
    fields_to_check = ["monthly_income_inr", "monthly_expenses_inr", "emergency_fund_inr", 
                       "monthly_debt_emi_inr", "occupation", "has_bank_account", "age"]
    fields_filled = sum(1 for k in fields_to_check if k in profile)
    awareness = min(20.0, (fields_filled * 2.5) + 5.0) # Starts at 5, maxes at 20 as they chat
    
    # Scams reduce awareness temporarily
    scam_detected = bool((latest_state or {}).get("scam_detected", False))
    if scam_detected:
        awareness = max(0.0, awareness - 8.0)

    # 5. Habit Progress (0-20): Based on active scheme matches and positive actions
    scheme_count = len((latest_state or {}).get("scheme_matches", []))
    progress = min(20.0, 5.0 + (scheme_count * 3.0) + (5.0 if stability > 12.0 else 0.0))

    dimensions = {
        "cashflow_stability": round(stability, 1),
        "risk_protection": round(protection, 1),
        "debt_health": round(debt_health, 1),
        "financial_awareness": round(awareness, 1),
        "habit_progress": round(progress, 1),
    }
    score = round(sum(dimensions.values()), 1)
    
    return {
        "score": min(100.0, score),
        "dimensions": dimensions,
        "band": _band(score),
        "next_best_action": _next_action(dimensions),
    }


def _band(score: float) -> str:
    """Return a user-friendly score band."""
    if score >= 75:
        return "strong"
    if score >= 50:
        return "improving"
    if score >= 30:
        return "fragile"
    return "urgent_support"


def _next_action(dimensions: dict[str, float]) -> str:
    """Choose the lowest scoring dimension as the next action."""
    weakest = min(dimensions, key=dimensions.get)
    actions = {
        "cashflow_stability": "Track income and expenses for the next 7 days.",
        "risk_protection": "Build a starter emergency fund equal to one week of expenses.",
        "debt_health": "List every loan with EMI, lender, and interest before taking new credit.",
        "financial_awareness": "Verify suspicious messages before sharing OTP, PIN, or Aadhaar details.",
        "habit_progress": "Save a small amount immediately after income arrives.",
    }
    return actions[weakest]


def _float(value: Any, default: float) -> float:
    """Convert a value to float with fallback."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
