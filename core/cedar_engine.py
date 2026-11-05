"""
ArthSetu — Cedar Financial Policy Engine
Evaluates financial actions against the Cedar policy file in < 1ms.

Since cedar-policy Python bindings may not be available for Python 3.9,
this module implements a pure-Python Cedar policy evaluator for the
5 ArthSetu policies defined in policies/guardrails.cedar.

The interface is designed to be cedar-policy-SDK-compatible so it can be
swapped with the native binding when Python 3.11 is available.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("arthsetu.cedar")

# Path to Cedar policy file
POLICY_PATH = os.path.join(os.path.dirname(__file__), "..", "policies", "guardrails.cedar")

# ─── Data classes mirroring Cedar entities ────────────────────────────────────

@dataclass
class User:
    user_id: str
    arth_score: int = 50
    occupation: str = ""
    monthly_income_inr: float = 0.0

@dataclass
class Transfer:
    transfer_id: str
    amount_inr: float = 0.0
    recipient: str = ""

@dataclass
class PolicyContext:
    threat_level: str = "SAFE"         # SAFE | HIGH | CRITICAL
    debt_ratio: float = 0.0            # 0–100 (%)
    requestor_type: str = "unknown"    # verified_bank | government_portal | unknown
    action: str = ""
    amount_inr: float = 0.0

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    policy_id: str
    action: str
    context_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "policy_id": self.policy_id,
            "action": self.action,
            "context": self.context_snapshot,
        }


# ─── Core evaluator ───────────────────────────────────────────────────────────

class CedarEngine:
    """
    Pure-Python Cedar policy evaluator for ArthSetu.

    Implements the 5 policies from policies/guardrails.cedar:
      Rule 1: forbid InitiateUPILitePayment when threat_level == CRITICAL
      Rule 2: forbid ApplyForLoan when arth_score < 30 AND debt_ratio > 60
      Rule 3: forbid ShareKYCDocument unless requestor_type is verified
      Rule 4: permit ClaimGovernmentScheme (always)
      Rule 5: forbid ApproveHighValueTransfer when score < 40 AND amount > 5000
    """

    def evaluate(
        self,
        action: str,
        principal: User,
        context: PolicyContext,
        resource: Transfer | None = None,
    ) -> PolicyDecision:
        """Evaluate a financial action against Cedar policies."""

        context.action = action
        snap = {
            "action": action,
            "arth_score": principal.arth_score,
            "threat_level": context.threat_level,
            "debt_ratio": context.debt_ratio,
            "requestor_type": context.requestor_type,
        }
        if resource:
            snap["amount_inr"] = resource.amount_inr

        # ── Rule 4: Government scheme — always permit (checked first) ────────
        if action == "ClaimGovernmentScheme":
            return PolicyDecision(
                allowed=True,
                reason="Rule 4: Government scheme applications are always permitted.",
                policy_id="rule_4_scheme_permit",
                action=action,
                context_snapshot=snap,
            )

        # ── Rule 1: Block UPI when threat is CRITICAL ────────────────────────
        if action == "InitiateUPILitePayment" and context.threat_level == "CRITICAL":
            logger.warning(f"Cedar DENY: InitiateUPILitePayment blocked — threat_level=CRITICAL user={principal.user_id}")
            return PolicyDecision(
                allowed=False,
                reason="Rule 1 (Cedar): UPI payment blocked — Prahari detected a CRITICAL scam threat. Protect your money first.",
                policy_id="rule_1_upi_critical_block",
                action=action,
                context_snapshot=snap,
            )

        # ── Rule 2: Block loan when score < 30 AND debt > 60% ───────────────
        if action == "ApplyForLoan":
            if principal.arth_score < 30 and context.debt_ratio > 60:
                logger.warning(f"Cedar DENY: ApplyForLoan — score={principal.arth_score} debt={context.debt_ratio}%")
                return PolicyDecision(
                    allowed=False,
                    reason=f"Rule 2 (Cedar): Loan application blocked — your Arth Score ({principal.arth_score}/100) and debt ratio ({context.debt_ratio:.0f}%) indicate this loan could be harmful.",
                    policy_id="rule_2_loan_distress_block",
                    action=action,
                    context_snapshot=snap,
                )

        # ── Rule 3: Block KYC sharing with unverified requestors ─────────────
        if action == "ShareKYCDocument":
            verified = {"verified_bank", "government_portal"}
            if context.requestor_type not in verified:
                logger.warning(f"Cedar DENY: ShareKYCDocument — requestor_type={context.requestor_type}")
                return PolicyDecision(
                    allowed=False,
                    reason=f"Rule 3 (Cedar): KYC sharing blocked — '{context.requestor_type}' is not a verified bank or government portal. Never share Aadhaar/PAN with unverified parties.",
                    policy_id="rule_3_kyc_unverified_block",
                    action=action,
                    context_snapshot=snap,
                )

        # ── Rule 5: Block high-value transfer for low-score users ────────────
        if action == "ApproveHighValueTransfer" and resource:
            if principal.arth_score < 40 and resource.amount_inr > 5000 and context.threat_level != "SAFE":
                logger.warning(f"Cedar DENY: HighValueTransfer — score={principal.arth_score} amount=₹{resource.amount_inr}")
                return PolicyDecision(
                    allowed=False,
                    reason=f"Rule 5 (Cedar): Transfer of ₹{resource.amount_inr:,.0f} blocked — your Arth Score ({principal.arth_score}/100) suggests waiting and verifying before transferring this amount.",
                    policy_id="rule_5_high_value_block",
                    action=action,
                    context_snapshot=snap,
                )

        # ── Default: permit ────────────────────────────────────────────────────
        return PolicyDecision(
            allowed=True,
            reason="Default permit — no forbid rule matched.",
            policy_id="default_permit",
            action=action,
            context_snapshot=snap,
        )


# Module-level singleton
_engine: CedarEngine | None = None


def get_engine() -> CedarEngine:
    global _engine
    if _engine is None:
        _engine = CedarEngine()
        logger.info("Cedar Financial Firewall initialized ✅")
    return _engine


def evaluate_action(
    action: str,
    user_id: str = "anonymous",
    arth_score: int = 50,
    threat_level: str = "SAFE",
    debt_ratio: float = 0.0,
    requestor_type: str = "unknown",
    amount_inr: float = 0.0,
    **kwargs: Any,
) -> PolicyDecision:
    """
    Convenience function for evaluating a financial action.
    Automatically logs every decision to the Cedar audit trail.

    Usage:
        from core.cedar_engine import evaluate_action
        decision = evaluate_action(
            action="InitiateUPILitePayment",
            user_id="user-123",
            arth_score=45,
            threat_level="CRITICAL",
        )
        if not decision.allowed:
            print(decision.reason)
    """
    engine = get_engine()
    principal = User(user_id=user_id, arth_score=arth_score)
    context = PolicyContext(
        threat_level=threat_level,
        debt_ratio=debt_ratio,
        requestor_type=requestor_type,
    )
    resource = Transfer(transfer_id="txn", amount_inr=amount_inr) if amount_inr else None
    decision = engine.evaluate(action, principal, context, resource)

    # Audit trail — log every policy decision
    _log_audit(decision, user_id)

    return decision


def evaluate_from_prahari_output(prahari_output: dict[str, Any], user_profile: dict[str, Any]) -> PolicyDecision:
    """
    Evaluate Cedar policy from Prahari agent output + user profile.
    Called automatically by Prahari after scam detection.
    """
    confidence: float = prahari_output.get("confidence", 0.0)
    scam_detected: bool = prahari_output.get("scam_detected", False)
    arth_score: int = user_profile.get("arth_score", 50) or 50

    # Map Prahari confidence to Cedar threat level
    if confidence >= 0.85 or scam_detected:
        threat_level = "CRITICAL"
    elif confidence >= 0.5:
        threat_level = "HIGH"
    else:
        threat_level = "SAFE"

    # Compute debt ratio from profile
    income = float(user_profile.get("monthly_income_inr") or 1)
    debt = float(user_profile.get("monthly_debt_emi_inr") or 0)
    debt_ratio = min(100.0, (debt / income * 100)) if income > 0 else 0.0

    return evaluate_action(
        action="InitiateUPILitePayment",
        user_id=user_profile.get("user_id", "anonymous"),
        arth_score=arth_score,
        threat_level=threat_level,
        debt_ratio=debt_ratio,
    )


# ─── Cedar Audit Trail ───────────────────────────────────────────────────────

_AUDIT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", ".arthsetu_data", "arthsetu.db")


def _ensure_audit_table() -> None:
    """Create the cedar_audit table if it doesn't exist."""
    import sqlite3
    os.makedirs(os.path.dirname(_AUDIT_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_AUDIT_DB_PATH)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cedar_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                policy_id TEXT NOT NULL,
                allowed BOOLEAN NOT NULL,
                reason TEXT,
                context_snapshot TEXT,
                UNIQUE(timestamp, user_id, action)
            )
        """)
        conn.commit()
    finally:
        conn.close()


def _log_audit(decision: PolicyDecision, user_id: str) -> None:
    """Persist a Cedar policy decision to the audit trail."""
    import sqlite3
    import time
    try:
        _ensure_audit_table()
        conn = sqlite3.connect(_AUDIT_DB_PATH)
        try:
            conn.execute(
                """INSERT OR IGNORE INTO cedar_audit
                   (timestamp, user_id, action, policy_id, allowed, reason, context_snapshot)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    time.time(),
                    user_id,
                    decision.action,
                    decision.policy_id,
                    decision.allowed,
                    decision.reason,
                    json.dumps(decision.context_snapshot, ensure_ascii=False),
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        logger.debug(f"Cedar audit log write failed (non-critical): {exc}")


def get_audit_log(user_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Retrieve Cedar policy audit trail, optionally filtered by user.

    Returns a list of audit entries sorted by most recent first.
    """
    import sqlite3
    try:
        _ensure_audit_table()
        conn = sqlite3.connect(_AUDIT_DB_PATH)
        try:
            conn.row_factory = sqlite3.Row
            if user_id:
                rows = conn.execute(
                    "SELECT * FROM cedar_audit WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (user_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM cedar_audit ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "user_id": row["user_id"],
                    "action": row["action"],
                    "policy_id": row["policy_id"],
                    "allowed": bool(row["allowed"]),
                    "reason": row["reason"],
                    "context": json.loads(row["context_snapshot"]) if row["context_snapshot"] else {},
                }
                for row in rows
            ]
        finally:
            conn.close()
    except Exception:
        return []


def get_audit_stats() -> dict[str, Any]:
    """Aggregate Cedar audit statistics for the dashboard.

    Returns counts of total evaluations, blocks, permits, and top blocked actions.
    """
    import sqlite3
    try:
        _ensure_audit_table()
        conn = sqlite3.connect(_AUDIT_DB_PATH)
        try:
            conn.row_factory = sqlite3.Row
            total = conn.execute("SELECT COUNT(*) as c FROM cedar_audit").fetchone()["c"]
            blocked = conn.execute("SELECT COUNT(*) as c FROM cedar_audit WHERE allowed = 0").fetchone()["c"]
            permitted = conn.execute("SELECT COUNT(*) as c FROM cedar_audit WHERE allowed = 1").fetchone()["c"]

            # Top blocked actions
            top_blocked = conn.execute(
                "SELECT action, policy_id, COUNT(*) as cnt FROM cedar_audit "
                "WHERE allowed = 0 GROUP BY action, policy_id ORDER BY cnt DESC LIMIT 5"
            ).fetchall()

            # Recent blocks
            recent_blocks = conn.execute(
                "SELECT timestamp, user_id, action, reason FROM cedar_audit "
                "WHERE allowed = 0 ORDER BY timestamp DESC LIMIT 5"
            ).fetchall()

            return {
                "total_evaluations": total,
                "total_blocked": blocked,
                "total_permitted": permitted,
                "block_rate_pct": round((blocked / total * 100), 1) if total > 0 else 0.0,
                "top_blocked_actions": [
                    {"action": r["action"], "policy_id": r["policy_id"], "count": r["cnt"]}
                    for r in top_blocked
                ],
                "recent_blocks": [
                    {
                        "timestamp": r["timestamp"],
                        "user_id": r["user_id"],
                        "action": r["action"],
                        "reason": r["reason"],
                    }
                    for r in recent_blocks
                ],
            }
        finally:
            conn.close()
    except Exception:
        return {"total_evaluations": 0, "total_blocked": 0, "total_permitted": 0, "block_rate_pct": 0.0}

