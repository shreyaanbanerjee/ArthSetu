"""Shilpi financial planning agent."""

from __future__ import annotations

import json
from typing import Any

from config import SHILPI_MODEL
from core.llm import call_llm, format_user_persona
from tools.scheme_matcher import match_schemes


def shilpi_node(state: dict[str, Any]) -> dict[str, Any]:
    """Build a conservative rupee-specific plan and scheme list."""
    raw = state.get("raw_input", "")
    profile = state.get("user_profile", {})
    language = state.get("language", "hi")
    
    schemes = match_schemes(profile)
    state["scheme_matches"] = schemes
    
    parsed = _plan_with_llm(raw, profile, schemes, language) or _plan_locally(raw, profile, schemes)
    state.setdefault("agent_outputs", {})["shilpi"] = parsed
    return state


def _plan_with_llm(raw: str, profile: dict[str, Any], schemes: list[dict[str, Any]], language: str) -> dict[str, Any] | None:
    """Use Gemini or Groq to build a customized, persona-tailored financial plan."""
    user_persona = format_user_persona(profile)
    
    schemes_context = ""
    if schemes:
        schemes_context = "Matched Government Schemes for user:\n" + "\n".join(
            f"- {s.get('name', 'Scheme')}: {s.get('description', '')} (Benefits: {s.get('benefits', '')})"
            for s in schemes[:8]
        )
    else:
        schemes_context = "No specific government welfare schemes matched for this profile."

    system_prompt = f"""You are Shilpi, ArthSetu's financial planning agent. Your task is to build a practical, conservative monthly budget plan, risk advice, and actionable next steps tailored to the user's job, income, and financial situation.
    
{user_persona}

{schemes_context}

Create a budget plan and action roadmap. Always respond in target language '{language}'. Avoid complex jargon.
CRITICAL INSTRUCTION: You MUST ONLY recommend welfare schemes that are explicitly listed in the 'Matched Government Schemes' context above. If the context says 'No specific government welfare schemes matched', you MUST leave the `schemes_to_apply` list completely empty. Do NOT invent, guess, or hallucinate schemes like PM Yojna unless they are in the match list.

You must output ONLY a valid JSON object matching this structure:
{{
    "monthly_plan": "A concise, reassuring summary of their monthly budget plan (e.g. keeping certain amount for essentials, emergency savings, and debt repayment) tailored specifically to their income/job.",
    "action_roadmap": [
        "Action item 1 for Week 1",
        "Action item 2 for Week 2",
        "Action item 3 for Week 3",
        "Action item 4 for Week 4"
    ],
    "income_type_detected": "regular" or "variable",
    "schemes_to_apply": [
        // Up to 3 relevant schemes from the matched list (each as a dict with 'name' and 'benefit_summary') or empty list if none fit
        {{"name": "scheme name", "benefit_summary": "brief summary of why it helps them"}}
    ],
    "risk_notes": [
        "Risk warning 1 specific to their situation",
        "Risk warning 2"
    ]
}}
Do not add any markdown formatting outside the JSON. Return only valid JSON."""

    try:
        response_text = call_llm(
            prompt=raw,
            system_prompt=system_prompt,
            response_format="json",
            model=SHILPI_MODEL
        )
        if not response_text:
            return None

        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            lines = cleaned_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        return json.loads(cleaned_text)
    except Exception:
        return None


def _plan_locally(raw: str, profile: dict[str, Any], schemes: list[dict[str, Any]]) -> dict[str, Any]:
    """Fallback local budget plan generator."""
    income = _float(profile.get("monthly_income_inr"), _infer_amount(raw, default=15000))
    expenses = _float(profile.get("monthly_expenses_inr"), income * 0.72)
    debt = _float(profile.get("monthly_debt_emi_inr"), 0.0)
    surplus = max(0.0, income - expenses - debt)
    emergency_save = max(100.0, min(surplus * 0.4, income * 0.1)) if income else 0.0
    debt_pay = max(0.0, min(surplus * 0.35, debt * 0.5 if debt else surplus * 0.2))
    learning = max(50.0, min(surplus * 0.1, 500.0)) if income else 0.0

    return {
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
