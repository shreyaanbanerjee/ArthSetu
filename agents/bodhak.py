"""Bodhak document decoder agent."""

from __future__ import annotations

import json
from typing import Any

from config import BODHAK_MODEL
from core.llm import call_llm, format_user_persona


def bodhak_node(state: dict[str, Any]) -> dict[str, Any]:
    """Decode financial document text into Saaf Bolna output."""
    language = state.get("language", "hi")
    document_text = state.get("ocr_extracted_text") or state.get("raw_input", "")
    profile = state.get("user_profile", {})
    parsed = _decode_with_llm(document_text, language, profile) or _decode_locally(document_text)
    state.setdefault("agent_outputs", {})["bodhak"] = parsed
    return state


def _decode_with_llm(document_text: str, language: str, profile: dict[str, Any]) -> dict[str, Any] | None:
    """Use Gemini or Groq to decode financial document tailored to user persona."""
    user_persona = format_user_persona(profile)
    system_prompt = f"""You are Bodhak, ArthSetu's financial document decoder. Your job is to FIRST classify the document correctly, then explain it in plain language tailored to the user.

{user_persona}

## STEP 1 — CLASSIFY THE DOCUMENT TYPE (read carefully before deciding)

Use these definitions to pick the correct document_type:

- **BalanceSheet**: A company's financial snapshot showing ASSETS (what it owns: fixed assets, current assets, inventories, trade receivables, cash) and LIABILITIES + EQUITY (what it owes: share capital, reserves, long-term borrowings, trade payables, current liabilities). Keywords: "Equity and Liabilities", "Non-current assets", "Non-current liabilities", "Share capital", "Reserves and surplus", "Trade payables", "Trade receivables", "Fixed assets", "Note No.", "As at March 31". This is a COMPANY DOCUMENT, NOT a personal tax document.

- **Form16**: A certificate issued by an EMPLOYER to an EMPLOYEE showing annual salary income and tax deducted (TDS). Keywords: "Certificate under section 203", "TAN of Employer", "PAN of Employee", "Gross Salary", "Chapter VI-A deductions", "80C", "Total Tax Deducted". This is a PERSONAL SALARY TAX document.

- **BankStatement**: A record of individual bank account transactions (credits, debits, opening/closing balance). Keywords: "Account Number", "Transaction Date", "Debit", "Credit", "Closing Balance", "IFSC", "Branch".

- **LoanAgreement**: A contract for a loan or EMI. Keywords: "EMI", "loan amount", "interest rate", "principal", "repayment schedule", "prepayment".

- **InsurancePolicy**: An insurance contract. Keywords: "premium", "sum assured", "policy number", "nominee", "maturity", "claim".

- **SalarySlip**: Monthly pay breakdown for an employee. Keywords: "basic salary", "HRA", "PF deduction", "net pay", "gross pay", "employee ID".

- **InvestmentStatement**: Mutual fund, stock, or demat account statement. Keywords: "NAV", "units", "portfolio value", "ISIN", "holdings", "returns".

- **Other**: Use only if none of the above clearly match.

**IMPORTANT**: If the document contains "Equity and Liabilities", "Non-current assets", "Trade payables", or "Note No." — it is ALWAYS a BalanceSheet, never a Form16.

## STEP 2 — EXPLAIN IN '{language}'

After classifying, explain the document in simple {language} tailored to the user's financial situation. Use their income, job and context from the user persona above.

## OUTPUT FORMAT

Return ONLY a valid JSON object (no markdown, no explanation outside the JSON):
{{
    "document_type": "<one of: BalanceSheet, Form16, BankStatement, LoanAgreement, InsurancePolicy, SalarySlip, InvestmentStatement, Other>",
    "plain_summary": "A simple, clear summary in '{language}' of what the document is and what it means for the user.",
    "three_things_to_know": ["Key insight 1 in '{language}'", "Key insight 2 in '{language}'", "Key insight 3 in '{language}'"],
    "one_action_now": "The single most important step the user should take right now (in '{language}').",
    "hidden_charges": [
        {{"name": "charge name", "amount_or_pct": "amount or percentage"}}
    ],
    "red_clauses": ["Any risky clause explained simply in '{language}', or empty list if none"],
    "jargon_explained": {{
        "JARGON_TERM": "simple explanation in '{language}'"
    }}
}}"""


    try:
        response_text = call_llm(
            prompt=document_text,
            system_prompt=system_prompt,
            response_format="json",
            model=BODHAK_MODEL
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


def _decode_locally(document_text: str) -> dict[str, Any]:
    """Generate a deterministic plain-language document summary."""
    lower = document_text.lower()
    # Check balance-sheet-specific terms FIRST — before the generic "balance" keyword
    # which would otherwise wrongly classify a balance sheet as a BankStatement.
    if any(k in lower for k in ["equity and liabilities", "shareholders' fund", "shareholders fund",
                                 "non-current liabilities", "non-current assets", "fixed assets",
                                 "capital work-in-progress", "trade payables", "trade receivables"]):
        doc_type = "BalanceSheet"
    elif "premium" in lower or "sum assured" in lower:
        doc_type = "InsurancePolicy"
    elif "loan" in lower or "emi" in lower:
        doc_type = "LoanAgreement"
    elif "form 16" in lower or "tds" in lower:
        doc_type = "Form16"
    elif "salary" in lower or "gross pay" in lower or "net pay" in lower:
        doc_type = "SalarySlip"
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
