"""Unified LLM calling interface for Gemini and Groq."""

from __future__ import annotations

import os
import json
import logging
from typing import Any

from config import GEMINI_API_KEY, GROQ_API_KEY

logger = logging.getLogger("arthsetu.llm")


def format_user_persona(profile: dict[str, Any]) -> str:
    """Format user profile details into a readable string for the LLM prompt."""
    if not profile:
        return "User Persona: Not available."

    details = []
    if profile.get("occupation"):
        details.append(f"- Occupation/Job: {profile['occupation']}")
    if profile.get("monthly_income_inr") is not None:
        details.append(f"- Monthly Income: Rs. {profile['monthly_income_inr']}")
    if profile.get("monthly_expenses_inr") is not None:
        details.append(f"- Monthly Expenses: Rs. {profile['monthly_expenses_inr']}")
    if profile.get("monthly_debt_emi_inr") is not None:
        details.append(f"- Monthly Debt EMI: Rs. {profile['monthly_debt_emi_inr']}")
    if profile.get("emergency_fund_inr") is not None:
        details.append(f"- Emergency Fund: Rs. {profile['emergency_fund_inr']}")
    if profile.get("savings_rate_pct") is not None:
        details.append(f"- Savings Rate: {profile['savings_rate_pct']}%")

    # Financial indicators
    indicators = []
    if profile.get("has_bank_account") is not None:
        indicators.append(f"Has bank account: {profile['has_bank_account']}")
    if profile.get("has_informal_debt") is not None:
        indicators.append(f"Has informal debt: {profile['has_informal_debt']}")
    if profile.get("land_ownership") is not None:
        indicators.append(f"Owns land: {profile['land_ownership']}")
    if profile.get("has_disability") is not None:
        indicators.append(f"Has disability: {profile['has_disability']}")
    if profile.get("has_daughter_below_10") is not None:
        indicators.append(f"Has daughter below 10: {profile['has_daughter_below_10']}")
    if profile.get("has_child") is not None:
        indicators.append(f"Has child: {profile['has_child']}")
    if profile.get("not_epf_member") is not None:
        indicators.append(f"Not an EPF member: {profile['not_epf_member']}")
    if profile.get("age") is not None:
        indicators.append(f"Age: {profile['age']}")

    if indicators:
        details.append("- Additional Indicators:\n    " + "\n    ".join(indicators))

    return "User Persona & Financial Situation:\n" + "\n".join(details)


def call_llm(
    prompt: str,
    system_prompt: str | None = None,
    response_format: str = "text",
    model: str | None = None,
) -> str | None:
    """Call Gemini 2.5 Flash via high-performance REST API with local fallback."""
    if GEMINI_API_KEY:
        try:
            import json
            import urllib.request

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [{"text": f"System context:\n{system_prompt}"}]})
                contents.append({"role": "model", "parts": [{"text": "Understood. I will act accordingly."}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})

            payload: dict[str, Any] = {"contents": contents}
            if response_format == "json":
                payload["generationConfig"] = {"responseMimeType": "application/json"}

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:
            logger.error(f"Gemini REST call failed: {exc}")

    if GROQ_API_KEY:
        try:
            return _call_groq(prompt, system_prompt, response_format, "llama-3.1-8b-instant")
        except Exception as exc:
            logger.error(f"Groq fallback failed: {exc}")

    return None


def _call_groq(
    prompt: str,
    system_prompt: str | None = None,
    response_format: str = "text",
    model: str = "llama-3.1-8b-instant"
) -> str | None:
    """Helper to perform Groq API completion."""
    from groq import Groq
    try:
        client = Groq(api_key=GROQ_API_KEY)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
        }
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        res = client.chat.completions.create(**kwargs)
        return res.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        raise e


def extract_profile_from_text(text: str) -> dict[str, Any]:
    """Extract user profile fields mentioned in a plain-language message.

    Uses a fast LLM call to pull structured financial details (income,
    expenses, occupation, age, etc.) that the user states conversationally.
    Returns only the keys that were actually found — never overwrites with
    None / 0 values for things the user did not mention.
    """
    system_prompt = """You are a profile extraction assistant for ArthSetu, an Indian financial guidance app.
Read the user message carefully and extract ONLY financial/personal details that are explicitly mentioned.

Extract these fields if present:
- occupation (string: their job/work type, e.g. "content_creator", "farmer", "gig_worker", "salaried", "daily_wage", "self_employed", "street_vendor")
- monthly_income_inr (number in rupees — convert "30k" → 30000, "1 lakh" → 100000)
- monthly_expenses_inr (number in rupees)
- monthly_debt_emi_inr (number in rupees)
- emergency_fund_inr (number in rupees)
- age (integer)
- has_bank_account (boolean)
- has_informal_debt (boolean)
- land_ownership (boolean)
- savings_rate_pct (number 0-100)

Rules:
- ONLY include fields that are clearly mentioned. Do NOT guess or infer.
- Return an empty JSON object {{}} if nothing is mentioned.
- Return only valid JSON with the extracted keys and their values.
- Do not include keys with null/None values.
"""
    try:
        response_text = call_llm(
            prompt=text,
            system_prompt=system_prompt,
            response_format="json",
            model="llama-3.1-8b-instant",  # fast, small model — just extraction
        )
        if not response_text:
            return {}
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(
                l for i, l in enumerate(lines)
                if not (i == 0 and l.startswith("```")) and not (i == len(lines) - 1 and l.startswith("```"))
            ).strip()
        extracted = json.loads(cleaned)
        # Safety: strip any null/zero/empty values that shouldn't overwrite existing data
        return {k: v for k, v in extracted.items() if v is not None and v != "" and v != 0}
    except Exception as e:
        logger.warning(f"Profile extraction failed (non-critical): {e}")
        return {}

