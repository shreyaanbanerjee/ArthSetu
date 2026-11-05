"""Unit tests for the Cedar Policy Financial Firewall."""

from __future__ import annotations

import unittest
from core.cedar_engine import (
    CedarEngine,
    PolicyContext,
    User,
    Transfer,
    evaluate_action,
    evaluate_from_prahari_output,
    get_audit_log,
    get_audit_stats,
)


class TestCedarEngine(unittest.TestCase):
    def setUp(self):
        self.engine = CedarEngine()

    def test_rule_1_upi_critical_threat_blocked(self):
        """Rule 1: UPI payments must be blocked when threat_level is CRITICAL."""
        user = User(user_id="user_1", arth_score=75)
        ctx = PolicyContext(threat_level="CRITICAL")
        decision = self.engine.evaluate("InitiateUPILitePayment", user, ctx)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.policy_id, "rule_1_upi_critical_block")
        self.assertIn("Rule 1 (Cedar)", decision.reason)

    def test_rule_1_upi_safe_permitted(self):
        """Rule 1: UPI payments should be permitted when threat_level is SAFE."""
        user = User(user_id="user_1", arth_score=75)
        ctx = PolicyContext(threat_level="SAFE")
        decision = self.engine.evaluate("InitiateUPILitePayment", user, ctx)
        self.assertTrue(decision.allowed)

    def test_rule_2_loan_in_distress_blocked(self):
        """Rule 2: Block loan when arth_score < 30 AND debt_ratio > 60%."""
        user = User(user_id="distressed_user", arth_score=25)
        ctx = PolicyContext(debt_ratio=65.0)
        decision = self.engine.evaluate("ApplyForLoan", user, ctx)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.policy_id, "rule_2_loan_distress_block")

    def test_rule_2_loan_healthy_permitted(self):
        """Rule 2: Permit loan when arth_score is healthy (>=30) or debt <= 60%."""
        user = User(user_id="healthy_user", arth_score=60)
        ctx = PolicyContext(debt_ratio=30.0)
        decision = self.engine.evaluate("ApplyForLoan", user, ctx)
        self.assertTrue(decision.allowed)

    def test_rule_3_kyc_unverified_blocked(self):
        """Rule 3: KYC document sharing blocked for unverified third parties."""
        user = User(user_id="user_3", arth_score=50)
        ctx = PolicyContext(requestor_type="random_agent_app")
        decision = self.engine.evaluate("ShareKYCDocument", user, ctx)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.policy_id, "rule_3_kyc_unverified_block")

    def test_rule_3_kyc_verified_bank_permitted(self):
        """Rule 3: KYC sharing permitted for verified banks and government portals."""
        user = User(user_id="user_3", arth_score=50)
        ctx_bank = PolicyContext(requestor_type="verified_bank")
        ctx_gov = PolicyContext(requestor_type="government_portal")
        self.assertTrue(self.engine.evaluate("ShareKYCDocument", user, ctx_bank).allowed)
        self.assertTrue(self.engine.evaluate("ShareKYCDocument", user, ctx_gov).allowed)

    def test_rule_4_government_scheme_always_permitted(self):
        """Rule 4: Government welfare claims are ALWAYS permitted."""
        user = User(user_id="user_4", arth_score=10)
        ctx = PolicyContext(threat_level="CRITICAL", debt_ratio=95.0)
        decision = self.engine.evaluate("ClaimGovernmentScheme", user, ctx)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.policy_id, "rule_4_scheme_permit")

    def test_rule_5_high_value_transfer_vulnerable_user_blocked(self):
        """Rule 5: High value transfer (>₹5,000) blocked for score < 40 under threat."""
        user = User(user_id="vulnerable_user", arth_score=35)
        ctx = PolicyContext(threat_level="HIGH")
        transfer = Transfer(transfer_id="t1", amount_inr=7500.0)
        decision = self.engine.evaluate("ApproveHighValueTransfer", user, ctx, transfer)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.policy_id, "rule_5_high_value_block")

    def test_rule_5_high_value_transfer_safe_permitted(self):
        """Rule 5: High value transfer permitted if threat_level is SAFE."""
        user = User(user_id="user_5", arth_score=35)
        ctx = PolicyContext(threat_level="SAFE")
        transfer = Transfer(transfer_id="t2", amount_inr=7500.0)
        decision = self.engine.evaluate("ApproveHighValueTransfer", user, ctx, transfer)
        self.assertTrue(decision.allowed)

    def test_evaluate_action_convenience_and_audit(self):
        """Test evaluate_action helper writes to audit trail."""
        decision = evaluate_action(
            action="InitiateUPILitePayment",
            user_id="test_audit_user",
            arth_score=40,
            threat_level="CRITICAL",
        )
        self.assertFalse(decision.allowed)
        # Check audit trail retrieval
        log = get_audit_log(user_id="test_audit_user", limit=5)
        self.assertGreater(len(log), 0)
        self.assertEqual(log[0]["action"], "InitiateUPILitePayment")
        self.assertFalse(log[0]["allowed"])

        # Check audit stats
        stats = get_audit_stats()
        self.assertIn("total_evaluations", stats)
        self.assertIn("total_blocked", stats)
        self.assertGreater(stats["total_evaluations"], 0)

    def test_evaluate_from_prahari_output(self):
        """Test Cedar decision from Prahari scam sentinel outputs."""
        prahari_scam = {
            "scam_detected": True,
            "confidence": 0.95,
            "scam_type": "otp_theft",
        }
        profile = {"user_id": "prahari_test_user", "arth_score": 55, "monthly_income_inr": 20000}
        decision = evaluate_from_prahari_output(prahari_scam, profile)
        self.assertFalse(decision.allowed)

        prahari_safe = {
            "scam_detected": False,
            "confidence": 0.1,
            "scam_type": "clean",
        }
        decision_safe = evaluate_from_prahari_output(prahari_safe, profile)
        self.assertTrue(decision_safe.allowed)


if __name__ == "__main__":
    unittest.main()

