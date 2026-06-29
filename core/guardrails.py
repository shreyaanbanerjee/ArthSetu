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


import asyncio
import os
from pathlib import Path

_rails_app = None

import json
from config import GEMINI_API_KEY

def guardrail_node(state: dict[str, Any]) -> dict[str, Any]:
    """Clean final response before delivery using Gemini as a guardrail."""
    response_text = state.get("final_response", "")
    if not response_text:
        return state

    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            # Use Gemini model explicitly since VIVEK_MODEL is overridden in .env
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = f"""You are a strict Hallucination Guardrail. 
User Profile Context: {state.get('user_profile', {})}
Bot Response: {response_text}

Does the Bot Response invent financial facts, advice, or claims that contradict the User Profile Context?
(NOTE: Links to the ArthSetu App, PWA, or IP addresses are valid system messages and are NEVER hallucinations).

If YES, auto-correct the response to be safe and accurate, removing the hallucinated parts.
If NO, just return the exact same Bot Response.

Respond ONLY with a JSON object: {{"hallucinated": bool, "corrected_response": "..."}}"""

            res = model.generate_content(prompt)
            text = res.text.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines[0].startswith("```"): lines = lines[1:]
                if lines and lines[-1].startswith("```"): lines = lines[:-1]
                text = "\n".join(lines).strip()
                
            parsed = json.loads(text)
            if parsed.get("hallucinated"):
                response_text = parsed.get("corrected_response", response_text)
        except Exception as e:
            print(f"Gemini Guardrail check failed: {e}")

    # Fallback deterministic rules
    cleaned = _rule_clean(response_text)
    state["final_response"] = cleaned
    return state


def _rule_clean(response_text: str) -> str:
    """Apply deterministic safety cleanup."""
    cleaned = re.sub(r"\b(guaranteed|guarantee)\s+(returns?|profit)\b", "possible returns", response_text, flags=re.I)
    cleaned = re.sub(r"\b(buy|invest in)\s+([A-Z][A-Za-z0-9& ]{2,})\s+(now|today)\b", "compare regulated options carefully", cleaned)
    if "consult a sebi" not in cleaned.lower() and re.search(r"\b(stock|mutual fund|insurance|loan)\b", cleaned, flags=re.I):
        cleaned += "\n\nPlease verify details with a regulated professional before making a financial commitment."
    return cleaned
