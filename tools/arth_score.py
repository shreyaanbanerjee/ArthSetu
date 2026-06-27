"""Arth Score calculation."""

from __future__ import annotations

from typing import Any


def calculate_arth_score(profile: dict[str, Any], latest_state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Calculate a five-dimension financial resilience score out of 100."""
    income = _float(profile.get("monthly_income_inr"), 0.0)
    expenses = _float(profile.get("monthly_expenses_inr"), 0.0)
    emergency = _float(profile.get("emergency_fund_inr"), 0.0)
    debt_emi = _float(profile.get("monthly_debt_emi_inr"), 0.0)
    savings_rate = _float(profile.get("savings_rate_pct"), ((income - expenses) / income * 100) if income else 0)
    has_bank = bool(profile.get("has_bank_account", True))
    has_informal_debt = bool(profile.get("has_informal_debt", False))
    scam_detected = bool((latest_state or {}).get("scam_detected", False))
    scheme_count = len((latest_state or {}).get("scheme_matches", []))

    stability = min(20, max(0, 10 + (savings_rate / 5)))
    protection = min(20, (emergency / max(expenses, 1)) * 6.7 + (5 if has_bank else 0))
    debt_health = max(0, 20 - ((debt_emi / max(income, 1)) * 50) - (6 if has_informal_debt else 0))
    awareness = max(0, 20 - (8 if scam_detected else 0) + min(4, scheme_count))
    progress = min(20, max(0, savings_rate / 2 + (4 if emergency > 0 else 0)))

    dimensions = {
        "cashflow_stability": round(stability, 1),
        "risk_protection": round(protection, 1),
        "debt_health": round(debt_health, 1),
        "financial_awareness": round(awareness, 1),
        "habit_progress": round(progress, 1),
    }
    score = round(sum(dimensions.values()), 1)
    return {
        "score": min(100, score),
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
