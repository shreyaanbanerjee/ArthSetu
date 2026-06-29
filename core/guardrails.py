"""ArthSetu Guardrails — layered input and output safety filters.

Layer 1 (Input):  PII redaction, prompt-injection detection, toxicity
                  filter, and input-length cap.  Runs BEFORE agents.
Layer 2 (Output): Hallucination check (Gemini), financial-safety regex,
                  PII-echo prevention, response-length cap, and
                  auto-disclaimer injection.  Runs AFTER synthesis.
"""

from __future__ import annotations

import json
import re
from typing import Any

from config import GEMINI_API_KEY, MAX_WHATSAPP_REPLY_CHARS


# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

MAX_INPUT_CHARS = 2000

# Indian PII patterns
_AADHAAR_RE = re.compile(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b")              # 12 digits starting 2-9
_PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")                          # ABCDE1234F
_BANK_ACCT_RE = re.compile(r"\b\d{9,18}\b")                              # 9-18 digit account numbers
_CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")                  # 13-19 digits with optional spaces/dashes
_IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")                       # SBIN0001234
_UPI_PIN_RE = re.compile(r"\b(?:upi\s*pin|pin)\s*(?:is|:)?\s*(\d{4,6})\b", re.I)

# Prompt injection patterns
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+(?:instructions?|prompts?|rules?)", re.I),
    re.compile(r"you\s+are\s+now\s+(?:DAN|evil|unfiltered|jailbroken)", re.I),
    re.compile(r"(?:forget|disregard|override)\s+(?:your|all|the)\s+(?:rules?|instructions?|guidelines?|system\s*prompt)", re.I),
    re.compile(r"pretend\s+(?:you\s+are|to\s+be)\s+(?:a\s+)?(?:different|new|unrestricted)", re.I),
    re.compile(r"system\s*prompt\s*[:=]", re.I),
    re.compile(r"(?:reveal|show|print|output)\s+(?:your\s+)?(?:system\s*prompt|instructions?|rules?)", re.I),
    re.compile(r"\[(?:SYSTEM|INST|SYS)\]", re.I),
    re.compile(r"<<\s*(?:SYS|SYSTEM)\s*>>", re.I),
]

# Toxicity/abuse keywords (kept minimal to avoid false positives on
# legitimate financial queries)
_TOXIC_PATTERNS = [
    re.compile(r"\b(?:kill\s+(?:yourself|urself|you)|suicide\s+(?:method|how))\b", re.I),
    re.compile(r"\b(?:bomb\s+(?:making|threat)|terrorist)\b", re.I),
    re.compile(r"\b(?:child\s+(?:porn|abuse|exploitation))\b", re.I),
]

# Financial safety patterns for output
_GUARANTEED_RETURN_RE = re.compile(r"\b(?:guaranteed?|100%\s*(?:safe|sure|certain))\s+(?:returns?|profit|gains?)\b", re.I)
_BUY_NOW_RE = re.compile(r"\b(?:buy|invest\s+in|purchase)\s+([A-Z][A-Za-z0-9& ]{2,})\s+(?:now|today|immediately)\b", re.I)
_BRAND_ENDORSE_RE = re.compile(
    r"\b(?:I\s+recommend|you\s+(?:should|must)\s+(?:buy|get|use))\s+"
    r"(?:(?:HDFC|SBI|ICICI|LIC|Bajaj|Paytm|PhonePe|Groww|Zerodha|Upstox|Angel)\s+\w+)",
    re.I,
)

# Products that need a disclaimer
_FINANCIAL_PRODUCT_RE = re.compile(
    r"\b(?:stock|share|mutual\s+fund|insurance|loan|fixed\s+deposit|"
    r"SIP|debenture|bond|NPS|PPF|ELSS|UPI\s+mandate)\b",
    re.I,
)

_DISCLAIMER_EN = (
    "\n\n⚠️ Please verify details with a SEBI/IRDAI registered professional "
    "before making any financial commitment."
)


# ──────────────────────────────────────────────────────────────────────
# Layer 1 — Input Guardrails
# ──────────────────────────────────────────────────────────────────────

def input_guardrail_node(state: dict[str, Any]) -> dict[str, Any]:
    """Sanitize user input before it reaches agents.

    Mutates ``state["raw_input"]`` and ``state["ocr_extracted_text"]``
    in place.  Sets ``state["guardrail_flags"]`` with audit metadata.
    If a hard block is triggered, sets ``state["final_response"]`` and
    ``state["guardrail_blocked"]`` so the graph can skip agents.
    """
    raw = state.get("raw_input", "")
    flags: list[str] = []

    # 1. Length cap
    if len(raw) > MAX_INPUT_CHARS:
        raw = raw[:MAX_INPUT_CHARS]
        flags.append("input_truncated")

    # 2. Prompt injection detection
    for pat in _INJECTION_PATTERNS:
        if pat.search(raw):
            flags.append("prompt_injection_blocked")
            state["raw_input"] = "[blocked]"
            state["ocr_extracted_text"] = "[blocked]"
            state["final_response"] = (
                "I wasn't able to process that message. "
                "Please ask me a genuine question about your finances."
            )
            state["guardrail_blocked"] = True
            state["guardrail_flags"] = flags
            return state

    # 3. Toxicity filter
    for pat in _TOXIC_PATTERNS:
        if pat.search(raw):
            flags.append("toxic_content_blocked")
            state["raw_input"] = "[blocked]"
            state["ocr_extracted_text"] = "[blocked]"
            state["final_response"] = (
                "I'm here to help with financial questions only. "
                "If you're in distress, please contact iCall (9152987821) "
                "or Vandrevala Foundation (1860-2662-345)."
            )
            state["guardrail_blocked"] = True
            state["guardrail_flags"] = flags
            return state

    # 4. PII redaction — mask sensitive data before it reaches LLMs
    raw, pii_found = _redact_pii(raw)
    if pii_found:
        flags.append("pii_redacted")

    state["raw_input"] = raw
    if state.get("ocr_extracted_text"):
        state["ocr_extracted_text"], _ = _redact_pii(state["ocr_extracted_text"])
    state["guardrail_flags"] = flags
    state["guardrail_blocked"] = False
    return state


def _redact_pii(text: str) -> tuple[str, bool]:
    """Replace Indian PII patterns with safe placeholders.

    Returns the cleaned text and a boolean indicating whether any PII
    was found.
    """
    found = False

    # UPI PIN (must run before generic digit patterns)
    if _UPI_PIN_RE.search(text):
        text = _UPI_PIN_RE.sub(r"[UPI_PIN_REDACTED]", text)
        found = True

    # Aadhaar (12 digits)
    if _AADHAAR_RE.search(text):
        text = _AADHAAR_RE.sub("[AADHAAR_REDACTED]", text)
        found = True

    # PAN card
    if _PAN_RE.search(text):
        text = _PAN_RE.sub("[PAN_REDACTED]", text)
        found = True

    # IFSC code (not truly PII but often accompanies account numbers)
    if _IFSC_RE.search(text):
        text = _IFSC_RE.sub("[IFSC_REDACTED]", text)
        found = True

    return text, found


# ──────────────────────────────────────────────────────────────────────
# Layer 2 — Output Guardrails
# ──────────────────────────────────────────────────────────────────────

def output_guardrail_node(state: dict[str, Any]) -> dict[str, Any]:
    """Clean the final response before delivery."""
    response_text = state.get("final_response", "")
    if not response_text:
        return state

    flags: list[str] = state.get("guardrail_flags", [])

    # 1. NeMo Guardrails hallucination check
    checked = _nemo_hallucination_check(response_text, state)
    if checked is not None:
        response_text = checked
        flags.append("hallucination_checked")

    # 2. Financial safety regex cleanup
    response_text = _financial_safety_clean(response_text)

    # 3. PII echo prevention — make sure the LLM didn't reflect PII back
    response_text, pii_echoed = _redact_pii(response_text)
    if pii_echoed:
        flags.append("pii_echo_stripped")

    # 4. Auto-disclaimer for financial products
    if _FINANCIAL_PRODUCT_RE.search(response_text):
        if "verify details" not in response_text.lower() and "sebi" not in response_text.lower():
            response_text += _DISCLAIMER_EN
            flags.append("disclaimer_added")

    # 5. Response length cap
    max_len = MAX_WHATSAPP_REPLY_CHARS
    if len(response_text) > max_len:
        response_text = response_text[:max_len - 3] + "..."
        flags.append("response_truncated")

    state["final_response"] = response_text
    state["guardrail_flags"] = flags
    return state

_nemo_rails = None

def _get_nemo_rails():
    """Lazily initialize NeMo Guardrails."""
    global _nemo_rails
    if _nemo_rails is None:
        import os
        from nemoguardrails import LLMRails, RailsConfig
        from config import GROQ_API_KEY
        
        # We use Groq API key dynamically here just in case it wasn't loaded in env
        if not os.getenv('GROQ_API_KEY'):
            os.environ['GROQ_API_KEY'] = GROQ_API_KEY or ""
            
        config = RailsConfig.from_path(os.path.join(os.path.dirname(__file__), "nemo_config"))
        _nemo_rails = LLMRails(config)
    return _nemo_rails

def _nemo_hallucination_check(response_text: str, state: dict[str, Any]) -> str | None:
    """Use NeMo Guardrails to detect and block hallucinated financial facts."""
    try:
        rails = _get_nemo_rails()

        profile_summary = {
            k: v for k, v in state.get("user_profile", {}).items()
            if k in {
                "monthly_income_inr", "monthly_expenses_inr",
                "emergency_fund_inr", "monthly_debt_emi_inr",
                "savings_rate_pct", "occupation", "age",
                "has_bank_account", "has_informal_debt",
            }
        }

        # NeMo Guardrails provides a synchronous wrapper
        import asyncio
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(
            rails.generate_async(
                messages=[
                    {"role": "user", "content": state.get("raw_input", "Hello")},
                    {"role": "assistant", "content": response_text}
                ]
            )
        )
        loop.close()
        
        new_text = res.get("content", response_text)
        if new_text != response_text:
            return new_text
        return None
    except Exception as e:
        print(f"NeMo Guardrails check failed (non-critical): {e}")
        return None


def _financial_safety_clean(text: str) -> str:
    """Apply deterministic financial safety rules."""
    # Remove guaranteed return claims
    text = _GUARANTEED_RETURN_RE.sub("possible returns (subject to market risk)", text)

    # Remove direct buy/invest recommendations
    text = _BUY_NOW_RE.sub("compare regulated options carefully", text)

    # Remove brand endorsements
    text = _BRAND_ENDORSE_RE.sub("consider comparing regulated financial products", text)

    return text
