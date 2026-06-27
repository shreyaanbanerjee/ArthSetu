"""Bodhak document decoder agent."""

from __future__ import annotations

import json
from typing import Any

import requests

from config import BODHAK_MODEL, OLLAMA_HOST


def bodhak_node(state: dict[str, Any]) -> dict[str, Any]:
    """Decode financial document text into Saaf Bolna output."""
    language = state.get("language", "hi")
    document_text = state.get("ocr_extracted_text") or state.get("raw_input", "")
    parsed = _decode_with_ollama(document_text, language) or _decode_locally(document_text)
    state.setdefault("agent_outputs", {})["bodhak"] = parsed
    return state


def _decode_with_ollama(document_text: str, language: str) -> dict[str, Any] | None:
    """Use local Ollama for document decoding when available."""
    prompt = f"""
You are Bodhak, ArthSetu's financial document decoder.
Return valid JSON with document_type, plain_summary, three_things_to_know, one_action_now,
hidden_charges, red_clauses, jargon_explained. Use language {language}.
"""
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": BODHAK_MODEL,
                "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": document_text}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1, "num_predict": 800},
            },
            timeout=20,
        )
        response.raise_for_status()
        return json.loads(response.json().get("message", {}).get("content", "{}"))
    except Exception:
        return None


def _decode_locally(document_text: str) -> dict[str, Any]:
    """Generate a deterministic plain-language document summary."""
    lower = document_text.lower()
    if "premium" in lower or "sum assured" in lower:
        doc_type = "InsurancePolicy"
    elif "loan" in lower or "emi" in lower:
        doc_type = "LoanAgreement"
    elif "form 16" in lower or "tds" in lower:
        doc_type = "Form16"
    elif "bank" in lower or "balance" in lower:
        doc_type = "BankStatement"
    else:
        doc_type = "Other"
    charges = []
    for token in ["processing fee", "late fee", "surrender charge", "prepayment charge"]:
        if token in lower:
            charges.append({"name": token.title(), "amount_or_pct": "mentioned in document"})
    return {
        "document_type": doc_type,
        "plain_summary": "This appears to be a financial document. I found the main type and highlighted charges or clauses that need attention.",
        "three_things_to_know": [
            "Check the total amount you must pay, not only the monthly amount.",
            "Look for fees, penalties, lock-in periods, and cancellation rules.",
            "Keep a copy before signing or paying.",
        ],
        "one_action_now": "Ask the provider to explain every fee in writing before you agree.",
        "hidden_charges": charges,
        "red_clauses": [clause for clause in ["lock-in", "penalty", "auto debit"] if clause in lower],
        "jargon_explained": {"APR": "The yearly cost of borrowing after including interest and charges."},
    }
