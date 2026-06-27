"""Final response guardrails."""

from __future__ import annotations

import json
import re
from typing import Any

import requests

from config import OLLAMA_HOST


GUARDRAIL_VIOLATIONS = [
    "specific product recommendation",
    "brand name endorsement",
    "guaranteed return claim",
    "unlicensed investment advice",
    "personal financial data request",
]


def guardrail_node(state: dict[str, Any]) -> dict[str, Any]:
    """Clean final response before delivery."""
    response_text = state.get("final_response", "")
    if not response_text:
        return state
    cleaned = _ollama_guardrail(response_text) or _rule_clean(response_text)
    state["final_response"] = cleaned
    return state


def _ollama_guardrail(response_text: str) -> str | None:
    """Use LlamaGuard through Ollama when available."""
    try:
        result = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": "llama-guard3:8b",
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Check this financial advice response for violations: "
                            f"{response_text}\nViolation types: {GUARDRAIL_VIOLATIONS}\n"
                            'Return JSON: {"safe": bool, "violation": str or null, "cleaned_response": str}'
                        ),
                    }
                ],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.0},
            },
            timeout=8,
        )
        result.raise_for_status()
        parsed = json.loads(result.json().get("message", {}).get("content", "{}"))
        if parsed.get("safe", True):
            return response_text
        return parsed.get("cleaned_response") or _rule_clean(response_text)
    except Exception:
        return None


def _rule_clean(response_text: str) -> str:
    """Apply deterministic safety cleanup."""
    cleaned = re.sub(r"\b(guaranteed|guarantee)\s+(returns?|profit)\b", "possible returns", response_text, flags=re.I)
    cleaned = re.sub(r"\b(buy|invest in)\s+([A-Z][A-Za-z0-9& ]{2,})\s+(now|today)\b", "compare regulated options carefully", cleaned)
    if "consult a sebi" not in cleaned.lower() and re.search(r"\b(stock|mutual fund|insurance|loan)\b", cleaned, flags=re.I):
        cleaned += "\n\nPlease verify details with a regulated professional before making a financial commitment."
    return cleaned
