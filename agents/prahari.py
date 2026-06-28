"""Prahari fraud sentinel agent."""

from __future__ import annotations

import json
from typing import Any

from config import GROQ_API_KEY, PRAHARI_MODEL, SCAM_CONFIDENCE_THRESHOLD
from tools.scam_engine import compute_true_apr, extract_loan_terms, report_to_rbi_sachet, run_scam_detection


PRAHARI_SYSTEM = """
You are Prahari, ArthSetu's fraud sentinel. Analyse financial messages for scam patterns.
Return valid JSON with scam_probability, scam_type, red_flags, loan_amount_inr, repayment_stated, period_months.
"""


def prahari_node(state: dict[str, Any]) -> dict[str, Any]:
    """Run LLM and rule-based fraud checks, then store the verdict."""
    raw = state.get("raw_input", "")
    language = state.get("language", "hi")
    triage = _llm_triage(raw) or {"scam_probability": 0.0, "scam_type": None, "red_flags": []}
    rule_result = run_scam_detection(raw)
    final_confidence = max(float(triage.get("scam_probability") or 0.0), float(rule_result["confidence"]))
    scam_detected = final_confidence >= SCAM_CONFIDENCE_THRESHOLD

    terms = extract_loan_terms(raw)

    def _parse_num(v: Any) -> float | None:
        import re
        if v is None: return None
        if isinstance(v, (int, float)): return float(v)
        m = re.search(r"(\d+(?:,\d+)*(?:\.\d+)?)", str(v))
        return float(m.group(1).replace(",", "")) if m else None

    principal = _parse_num(triage.get("loan_amount_inr") or terms.get("loan_amount_inr"))
    repayment = _parse_num(triage.get("repayment_stated") or terms.get("repayment_stated"))
    months = _parse_num(triage.get("period_months") or terms.get("period_months"))
    
    apr_info = compute_true_apr(principal, repayment, int(months)) if principal and repayment and months else None

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


def _llm_triage(raw: str) -> dict[str, Any] | None:
    """Use Groq for fraud triage when configured."""
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq

        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=PRAHARI_MODEL,
            messages=[{"role": "system", "content": PRAHARI_SYSTEM}, {"role": "user", "content": raw}],
            temperature=0.1,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content or "{}")
    except Exception:
        return None
