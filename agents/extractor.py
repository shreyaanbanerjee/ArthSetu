"""Extractor agent for dynamic profile updates."""

from __future__ import annotations

import json
from typing import Any

from config import SUTRADHAR_MODEL
from core.llm import call_llm


def extractor_node(state: dict[str, Any]) -> dict[str, Any]:
    """Extract profile updates from user messages using LLM."""
    raw = state.get("raw_input", "")
    profile = state.get("user_profile", {})
    
    # Fast heuristic: Only run LLM extraction if there are numbers or keywords indicating changes
    keywords = ["income", "salary", "expense", "debt", "loan", "emi", "cleared", "paid", "age", "fund", "emergency", "rupee", "k", "lakh"]
    if not any(k in raw.lower() for k in keywords):
        return state

    system_prompt = """You are a profile data extractor. Compare the user's message against their current profile and return a JSON object with ONLY the fields that have explicitly changed based on their message.
If no profile details changed, return an empty JSON object {}.

Profile fields:
- occupation: string
- monthly_income_inr: number
- monthly_expenses_inr: number
- emergency_fund_inr: number
- monthly_debt_emi_inr: number
- has_bank_account: boolean
- has_disability: boolean
- land_ownership: boolean
- age: number
- has_daughter_below_10: boolean
- not_epf_member: boolean

For example, if they say "I paid off my loan", return {"monthly_debt_emi_inr": 0}.
If they say "My salary is now 50k", return {"monthly_income_inr": 50000}.
Output purely JSON without any markdown formatting.
"""

    prompt = (
        f"Current Profile: {json.dumps(profile, ensure_ascii=False)}\n"
        f"User Message: {raw}"
    )

    try:
        response_text = call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="json",
            model="llama-3.1-8b-instant" # Fast model for latency
        )
        if not response_text:
            return state

        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            lines = cleaned_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        updates = json.loads(cleaned_text)
        if updates and isinstance(updates, dict):
            # Only keep valid keys
            valid_keys = [
                "occupation", "monthly_income_inr", "monthly_expenses_inr",
                "emergency_fund_inr", "monthly_debt_emi_inr", "has_bank_account",
                "has_disability", "land_ownership", "age", "has_daughter_below_10",
                "not_epf_member"
            ]
            valid_updates = {k: v for k, v in updates.items() if k in valid_keys}
            
            if valid_updates:
                from core.memory import upsert_user_profile
                new_profile = upsert_user_profile(state.get("user_id", "demo-user"), valid_updates)
                state["user_profile"] = new_profile
                state["profile_updated_dynamically"] = True
    except Exception as e:
        print(f"Extractor error: {e}")
        pass

    return state
