"""Prahari fraud sentinel agent."""

from __future__ import annotations

import json
from typing import Any

from config import PRAHARI_MODEL, SCAM_CONFIDENCE_THRESHOLD
from tools.scam_engine import compute_true_apr, extract_loan_terms, report_to_rbi_sachet, run_scam_detection
from core.llm import call_llm, format_user_persona


def prahari_node(state: dict[str, Any]) -> dict[str, Any]:
    """Run LLM and rule-based fraud checks, then store the verdict."""
    raw = state.get("raw_input", "")
    language = state.get("language", "hi")
    profile = state.get("user_profile", {})
    if len(raw.strip()) < 10:
        triage = {"scam_probability": 0.0, "scam_type": None, "red_flags": []}
        rule_result = {"confidence": 0.0, "matched_pattern": None, "flags": []}
    else:
        triage = _llm_triage(raw, profile) or {"scam_probability": 0.0, "scam_type": None, "red_flags": []}
        rule_result = run_scam_detection(raw)
        
    final_confidence = max(float(triage.get("scam_probability") or 0.0), float(rule_result.get("confidence") or 0.0))
    scam_detected = final_confidence >= SCAM_CONFIDENCE_THRESHOLD

    terms = extract_loan_terms(raw)
    principal = _number_or_none(triage.get("loan_amount_inr")) or terms.get("loan_amount_inr")
    repayment = _number_or_none(triage.get("repayment_stated")) or terms.get("repayment_stated")
    months = _int_or_none(triage.get("period_months")) or terms.get("period_months")
    apr_info = compute_true_apr(float(principal), float(repayment), int(months)) if principal and repayment and months else None

    sachet_reference = None
    if scam_detected:
        sachet_reference = report_to_rbi_sachet(
            scam_type=triage.get("scam_type") or rule_result.get("matched_pattern") or "Unknown",
            message_excerpt=raw[:500],
            confidence=final_confidence,
            language=language,
        )

    state["scam_detected"] = scam_detected
    state.setdefault("agent_outputs", {})["prahari"] = {
        "scam_detected": scam_detected,
        "confidence": round(final_confidence, 3),
        "scam_type": triage.get("scam_type") or rule_result.get("matched_pattern"),
        "red_flags": list(dict.fromkeys([*(triage.get("red_flags") or []), *rule_result.get("flags", [])])),
        "apr_info": apr_info,
        "sachet_reference": sachet_reference,
        "verdict": "SCAM" if scam_detected else "CLEAR",
    }
    return state


def _llm_triage(raw: str, profile: dict[str, Any]) -> dict[str, Any] | None:
    """Use Gemini or Groq for fraud triage."""
    user_persona = format_user_persona(profile)
    system_prompt = f"""You are Prahari, ArthSetu's fraud sentinel. Analyze the financial message for potential scams, fraud, or predatory terms.

{user_persona}

Consider how this potential scam might target someone in their financial situation (e.g. predatory loans targeting low-income workers, fake subsidies/welfare schemes, OTP/UPI frauds).

CRITICAL INSTRUCTION: Do NOT flag a message as a scam simply because it contains poor grammar, weird formatting, or is written in a regional Indian language (e.g. Marathi, Hindi, Bengali) or transliterated script. Audio transcriptions naturally have grammar errors or unusual vocabulary—this is normal and NOT a scam indicator. Only flag actual financial fraud hooks (e.g., asking for OTP, fake lotteries, urgent payment demands).

You must output ONLY a valid JSON object with the following structure:
{{
    "scam_probability": float (0.0 to 1.0),
    "scam_type": "The type of scam if detected (e.g. Predatory Loan, Lottery Scam, UPI Fraud, KYC Fraud, etc.) or null",
    "red_flags": ["list of red flags found"],
    "loan_amount_inr": float or null,
    "repayment_stated": float or null,
    "period_months": int or null
}}
Do not add any markdown formatting outside the JSON. Return only valid JSON."""

    try:
        response_text = call_llm(
            prompt=raw,
            system_prompt=system_prompt,
            response_format="json",
            model=PRAHARI_MODEL
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


def _number_or_none(value: Any) -> float | None:
    """Return a numeric value only when the LLM field is actually numeric."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    """Return an integer only when the LLM field is actually numeric."""
    number = _number_or_none(value)
    return int(number) if number is not None else None
