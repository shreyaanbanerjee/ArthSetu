"""NPCI DPI adapter with explicit simulation mode."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from config import DPI_MODE, NPCI_API_BASE, NPCI_MERCHANT_ID


def initiate_upi_lite_x_payment(user_upi_id: str, amount_inr: float, description: str) -> dict[str, Any]:
    """Initiate or simulate an offline UPI Lite X payment."""
    payload = _base_payload(user_upi_id, amount_inr, description, "UPI_LITE_X")
    return _post_or_simulate("/upi/lite-x/initiate", payload)


def create_upi_circle_delegation(
    delegate_upi_id: str, primary_upi_id: str, max_amount_inr: float, purpose: str
) -> dict[str, Any]:
    """Create or simulate UPI Circle delegated authority."""
    payload = {
        "merchantId": NPCI_MERCHANT_ID,
        "primaryVpa": primary_upi_id,
        "delegateVpa": delegate_upi_id,
        "maxTransactionAmount": str(int(max_amount_inr * 100)),
        "purpose": purpose[:80],
        "validityDays": 30,
        "delegationType": "FULL",
    }
    return _post_or_simulate("/upi/circle/delegate", payload)


def trigger_dynamic_autopay(user_upi_id: str, amount_inr: float, description: str) -> dict[str, Any]:
    """Create or simulate a dynamic UPI Autopay mandate."""
    payload = _base_payload(user_upi_id, amount_inr, description, "DYNAMIC_AUTOPAY")
    payload["frequency"] = "AS_PRESENTED"
    payload["startDate"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return _post_or_simulate("/upi/autopay/create", payload)


def file_udir_dispute(txn_id: str, user_upi_id: str, amount_inr: float, reason: str) -> dict[str, Any]:
    """File or simulate a UDIR dispute packet."""
    payload = {
        "merchantId": NPCI_MERCHANT_ID,
        "originalTxnId": txn_id,
        "complainantVpa": user_upi_id,
        "disputeAmount": str(int(amount_inr * 100)),
        "disputeReason": reason[:120],
        "disputeCategory": "FRAUD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return _post_or_simulate("/udir/dispute/file", payload)


def _base_payload(user_upi_id: str, amount_inr: float, description: str, txn_type: str) -> dict[str, Any]:
    """Build a common NPCI-style payload."""
    return {
        "merchantId": NPCI_MERCHANT_ID,
        "transactionId": f"ARTHSETU-{uuid.uuid4().hex[:12].upper()}",
        "amount": str(int(amount_inr * 100)),
        "currency": "INR",
        "payerVpa": user_upi_id,
        "description": description[:50],
        "txnType": txn_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _post_or_simulate(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Post to configured sandbox or return an honest simulation response."""
    if DPI_MODE != "production" or not NPCI_API_BASE:
        return {"status": "simulated", "path": path, "payload": payload, "message": "NPCI public API access is not configured."}
    try:
        response = httpx.post(
            f"{NPCI_API_BASE.rstrip('/')}{path}",
            json=payload,
            headers={"Content-Type": "application/json", "X-Merchant-Id": NPCI_MERCHANT_ID},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        return {"status": "error", "message": str(exc), "payload": payload}
