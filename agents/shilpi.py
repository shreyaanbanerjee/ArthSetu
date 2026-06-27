"""Shilpi financial planning agent."""

from __future__ import annotations

from typing import Any

from tools.scheme_matcher import match_schemes


def shilpi_node(state: dict[str, Any]) -> dict[str, Any]:
    """Build a conservative rupee-specific plan and scheme list."""
    raw = state.get("raw_input", "")
    profile = state.get("user_profile", {})
    schemes = match_schemes(profile)
    income = _float(profile.get("monthly_income_inr"), _infer_amount(raw, default=15000))
    expenses = _float(profile.get("monthly_expenses_inr"), income * 0.72)
    debt = _float(profile.get("monthly_debt_emi_inr"), 0.0)
    surplus = max(0.0, income - expenses - debt)
    emergency_save = max(100.0, min(surplus * 0.4, income * 0.1)) if income else 0.0
    debt_pay = max(0.0, min(surplus * 0.35, debt * 0.5 if debt else surplus * 0.2))
    learning = max(50.0, min(surplus * 0.1, 500.0)) if income else 0.0

    state["scheme_matches"] = schemes
    state.setdefault("agent_outputs", {})["shilpi"] = {
        "monthly_plan": (
            f"Monthly plan: keep Rs {expenses:.0f} for essentials, Rs {emergency_save:.0f} for emergency savings, "
            f"Rs {debt_pay:.0f} toward extra debt repayment, and Rs {learning:.0f} for skill or learning needs."
        ),
        "action_roadmap": [
            "Week 1: Write income, expenses, and debt EMIs in one place.",
            "Week 2: Separate emergency savings immediately after income arrives.",
            "Week 3: Apply for the most relevant welfare scheme with documents ready.",
            "Week 4: Review spending leaks and adjust next month's plan.",
        ],
        "income_type_detected": "variable" if any(word in raw.lower() for word in ["gig", "daily", "farmer", "season", "irregular"]) else "regular",
        "schemes_to_apply": schemes[:5],
        "risk_notes": _risk_notes(income, expenses, debt),
    }
    return state


def _risk_notes(income: float, expenses: float, debt: float) -> list[str]:
    """Create conservative risk warnings."""
    notes = []
    if income and expenses / income > 0.85:
        notes.append("Expenses are high compared with income; avoid new EMIs this month.")
    if income and debt / income > 0.3:
        notes.append("Debt EMIs are above a comfortable level; prioritize costly informal debt.")
    if not notes:
        notes.append("Keep the plan flexible and review it after the next income cycle.")
    return notes


def _infer_amount(text: str, default: float) -> float:
    """Infer the first rupee amount from text."""
    import re

    match = re.search(r"(?:rs\.?|inr|₹)?\s*([1-9][0-9,]{3,})", text, flags=re.I)
    return float(match.group(1).replace(",", "")) if match else default


def _float(value: Any, default: float) -> float:
    """Convert to float with fallback."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
