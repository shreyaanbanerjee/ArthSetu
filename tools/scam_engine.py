"""Rule-based scam detection, APR calculation, and Sachet report packets."""

from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime, timezone
from typing import Any

from config import APR_WARNING_THRESHOLD, RBI_SACHET_URL


SCAM_PATTERNS: list[dict[str, Any]] = [
    {"name": "kyc_expiry", "weight": 0.86, "regex": r"\bkyc\b.*\b(block|expire|suspend|band| बंद|ब्लॉक)"},
    {"name": "otp_request", "weight": 0.95, "regex": r"\b(otp|one time password|cvv|pin|upi pin)\b.*\b(share|send|बताओ|भेज)"},
    {"name": "remote_access", "weight": 0.92, "regex": r"\b(anydesk|teamviewer|screen share|remote access|quicksupport)\b"},
    {"name": "instant_loan_fee", "weight": 0.82, "regex": r"\b(processing fee|advance fee|पहले.*फीस|loan approved)\b"},
    {"name": "lottery_prize", "weight": 0.82, "regex": r"\b(lottery|prize|winner|इनाम|लॉटरी)\b"},
    {"name": "cashback_link", "weight": 0.76, "regex": r"\b(cashback|reward|refund)\b.*https?://"},
    {"name": "urgent_payment", "weight": 0.74, "regex": r"\b(urgent|immediately|within 10 minutes|अभी|तुरंत)\b.*\b(pay|transfer|भुगतान)\b"},
    {"name": "fake_job_fee", "weight": 0.78, "regex": r"\b(job|work from home|नौकरी)\b.*\b(registration fee|security deposit|fees)\b"},
    {"name": "investment_doubling", "weight": 0.9, "regex": r"\b(double|guaranteed|100% return|दोगुना|गारंटी)\b"},
    {"name": "upi_collect_fraud", "weight": 0.84, "regex": r"\b(receive money|refund)\b.*\b(approve|enter upi pin|collect)\b"},
    {"name": "suspicious_shortlink", "weight": 0.63, "regex": r"\b(bit\.ly|tinyurl|cutt\.ly|shorturl|t\.ly|wa\.me)\b"},
    {"name": "bank_account_block", "weight": 0.83, "regex": r"\b(account|card|wallet)\b.*\b(blocked|freeze|suspend|बंद)\b"},
    {"name": "subsidy_phishing", "weight": 0.72, "regex": r"\b(subsidy|pm kisan|ujjwala|सरकारी योजना)\b.*https?://"},
    {"name": "aadhaar_pan_update", "weight": 0.8, "regex": r"\b(aadhaar|pan|आधार|पैन)\b.*\b(update|verify|link)\b.*https?://"},
    {"name": "insurance_refund", "weight": 0.7, "regex": r"\b(insurance|policy|premium)\b.*\b(refund|bonus|maturity)\b"},
    {"name": "loan_app_harassment", "weight": 0.74, "regex": r"\b(contact list|gallery|photo|blackmail|defaulter)\b"},
    {"name": "qr_receive_money", "weight": 0.88, "regex": r"\b(scan qr|qr code)\b.*\b(receive|get money|refund)\b"},
    {"name": "tax_refund_phishing", "weight": 0.78, "regex": r"\b(income tax|itr|tax refund)\b.*https?://"},
    {"name": "electricity_disconnect", "weight": 0.76, "regex": r"\b(electricity|bill|bijli)\b.*\b(disconnect|cut|बंद)\b"},
    {"name": "sim_block", "weight": 0.76, "regex": r"\b(sim|mobile number)\b.*\b(block|deactivate| बंद)\b"},
    {"name": "fake_courier", "weight": 0.72, "regex": r"\b(courier|parcel|customs|fedex|delivery)\b.*\b(pay|kyc|illegal)\b"},
    {"name": "crypto_forex", "weight": 0.78, "regex": r"\b(crypto|forex|trading)\b.*\b(guaranteed|daily profit|signal)\b"},
    {"name": "charity_pressure", "weight": 0.58, "regex": r"\b(donation|help child|medical emergency)\b.*\b(upi|pay)\b"},
    {"name": "fake_police", "weight": 0.86, "regex": r"\b(police|cbi|rbi|crime branch)\b.*\b(arrest|case|warrant)\b"},
    {"name": "merchant_refund_pin", "weight": 0.84, "regex": r"\b(refund|merchant)\b.*\b(upi pin|otp)\b"},
    {"name": "card_limit_increase", "weight": 0.7, "regex": r"\b(credit card|limit)\b.*\b(increase|upgrade)\b.*https?://"},
    {"name": "emi_moratorium_fee", "weight": 0.68, "regex": r"\b(emi|loan)\b.*\b(moratorium|holiday)\b.*\b(fee|charge)\b"},
]


def run_scam_detection(text: str) -> dict[str, Any]:
    """Detect known scam signals using weighted regex patterns."""
    lowered = text.lower()
    matches: list[dict[str, Any]] = []
    flags: list[str] = []

    for pattern in SCAM_PATTERNS:
        if re.search(pattern["regex"], lowered, flags=re.IGNORECASE):
            matches.append({"name": pattern["name"], "weight": pattern["weight"]})
            flags.append(_humanise_pattern(pattern["name"]))

    link_count = len(re.findall(r"https?://|www\.", lowered))
    phone_count = len(re.findall(r"\b\d{10}\b", lowered))
    urgency_bonus = 0.08 if re.search(r"\b(now|urgent|immediately|तुरंत|जल्दी|last chance)\b", lowered) else 0.0
    link_bonus = min(0.12, link_count * 0.04)
    phone_bonus = min(0.06, phone_count * 0.03)

    if not matches:
        confidence = min(0.35, urgency_bonus + link_bonus + phone_bonus)
        matched_pattern = None
    else:
        strongest = max(item["weight"] for item in matches)
        support = min(0.16, (len(matches) - 1) * 0.04)
        confidence = min(0.99, strongest + support + urgency_bonus + link_bonus + phone_bonus)
        matched_pattern = max(matches, key=lambda item: item["weight"])["name"]

    return {
        "confidence": round(confidence, 3),
        "matched_pattern": matched_pattern,
        "flags": flags,
        "matches": matches,
    }


def compute_true_apr(principal: float, total_repayment: float, months: int) -> dict[str, Any]:
    """Compute simple and effective annual APR from stated repayment terms."""
    if principal <= 0 or total_repayment <= 0 or months <= 0:
        return {"error": "principal, total_repayment and months must be positive"}

    interest = max(0.0, total_repayment - principal)
    simple_apr = (interest / principal) * (12 / months) * 100
    monthly_rate = (total_repayment / principal) ** (1 / months) - 1 if total_repayment > principal else 0
    effective_apr = ((1 + monthly_rate) ** 12 - 1) * 100

    return {
        "principal": round(principal, 2),
        "total_repayment": round(total_repayment, 2),
        "interest": round(interest, 2),
        "months": months,
        "apr_pct": round(effective_apr, 2),
        "simple_apr_pct": round(simple_apr, 2),
        "predatory_warning": effective_apr >= APR_WARNING_THRESHOLD,
    }


def report_to_rbi_sachet(scam_type: str, message_excerpt: str, confidence: float, language: str) -> dict[str, Any]:
    """Create an RBI Sachet-ready report packet for manual filing."""
    digest = hashlib.sha256(f"{scam_type}|{message_excerpt}|{datetime.now(timezone.utc).date()}".encode()).hexdigest()
    return {
        "status": "prepared_for_manual_filing",
        "reference": f"ARTH-SACHET-{digest[:12].upper()}",
        "portal_url": RBI_SACHET_URL,
        "scam_type": scam_type,
        "confidence": round(confidence, 3),
        "language": language,
        "message_excerpt": message_excerpt,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "note": "Sachet does not expose a general public complaint API; this packet can be filed on the portal.",
    }


def extract_loan_terms(text: str) -> dict[str, float | int | None]:
    """Extract rough loan terms from natural text for APR calculation."""
    amounts = [float(value.replace(",", "")) for value in re.findall(r"(?:rs\.?|inr|₹)\s*([0-9][0-9,]*(?:\.\d+)?)", text, flags=re.I)]
    months_match = re.search(r"(\d{1,3})\s*(month|months|mahine|महीने|माह)", text, flags=re.I)
    months = int(months_match.group(1)) if months_match else None
    principal = amounts[0] if amounts else None
    repayment = amounts[1] if len(amounts) > 1 else None
    return {"loan_amount_inr": principal, "repayment_stated": repayment, "period_months": months}


def _humanise_pattern(name: str) -> str:
    """Convert a pattern identifier into a readable red flag."""
    return name.replace("_", " ").title()
