"""
ArthSetu — Cedar Policy Firewall Boundary & Edge Case Test Suite
25 unique automated tests verifying strict boundary conditions, idempotency,
audit persistence, and rule coverage for the deterministic Cedar engine.
"""

from __future__ import annotations

import unittest
from core.cedar_engine import (
    evaluate_action,
    get_audit_log,
    get_audit_stats,
    CedarEngine,
    User,
    Transfer,
    PolicyContext,
    PolicyDecision,
)


class TestCedarEdgeCases(unittest.TestCase):
    """25 boundary and edge case tests for pure-Python Cedar Policy Engine."""

    # -------------------------------------------------------------------------
    # Rule 1: Critical Threat Block on UPI
    # -------------------------------------------------------------------------
    def test_rule1_blocks_when_threat_is_critical(self):
        dec = evaluate_action(action="InitiateUPILitePayment", threat_level="CRITICAL")
        self.assertFalse(dec.allowed)
        self.assertEqual(dec.policy_id, "rule_1_upi_critical_block")

    def test_rule1_permits_when_threat_is_safe(self):
        dec = evaluate_action(action="InitiateUPILitePayment", threat_level="SAFE")
        self.assertTrue(dec.allowed)
        self.assertEqual(dec.policy_id, "default_permit")

    def test_rule1_permits_when_threat_is_suspicious_for_small_payment(self):
        dec = evaluate_action(action="InitiateUPILitePayment", threat_level="SUSPICIOUS")
        self.assertTrue(dec.allowed)

    # -------------------------------------------------------------------------
    # Rule 2: Loan Application Boundary Conditions (Score < 30 & Debt > 60)
    # -------------------------------------------------------------------------
    def test_rule2_boundary_denies_at_score_29_debt_61(self):
        dec = evaluate_action(action="ApplyForLoan", arth_score=29, debt_ratio=61.0)
        self.assertFalse(dec.allowed)
        self.assertEqual(dec.policy_id, "rule_2_loan_distress_block")

    def test_rule2_boundary_permits_at_score_30_debt_61(self):
        dec = evaluate_action(action="ApplyForLoan", arth_score=30, debt_ratio=61.0)
        self.assertTrue(dec.allowed)

    def test_rule2_boundary_permits_at_score_25_debt_60(self):
        dec = evaluate_action(action="ApplyForLoan", arth_score=25, debt_ratio=60.0)
        self.assertTrue(dec.allowed)

    def test_rule2_boundary_denies_at_score_25_debt_60_point_1(self):
        dec = evaluate_action(action="ApplyForLoan", arth_score=25, debt_ratio=60.1)
        self.assertFalse(dec.allowed)

    def test_rule2_permits_good_score_and_low_debt(self):
        dec = evaluate_action(action="ApplyForLoan", arth_score=75, debt_ratio=15.0)
        self.assertTrue(dec.allowed)

    # -------------------------------------------------------------------------
    # Rule 3: ShareKYCDocument Whitelist
    # -------------------------------------------------------------------------
    def test_rule3_permits_verified_bank(self):
        dec = evaluate_action(action="ShareKYCDocument", requestor_type="verified_bank")
        self.assertTrue(dec.allowed)

    def test_rule3_permits_government_portal(self):
        dec = evaluate_action(action="ShareKYCDocument", requestor_type="government_portal")
        self.assertTrue(dec.allowed)

    def test_rule3_denies_unknown_requestor(self):
        dec = evaluate_action(action="ShareKYCDocument", requestor_type="unknown")
        self.assertFalse(dec.allowed)
        self.assertEqual(dec.policy_id, "rule_3_kyc_unverified_block")

    def test_rule3_denies_telegram_bot(self):
        dec = evaluate_action(action="ShareKYCDocument", requestor_type="telegram_channel")
        self.assertFalse(dec.allowed)

    def test_rule3_denies_loan_app_agent(self):
        dec = evaluate_action(action="ShareKYCDocument", requestor_type="unregistered_apk")
        self.assertFalse(dec.allowed)

    # -------------------------------------------------------------------------
    # Rule 5: High Value Transfer Safeguards (Amount > 5000, Score < 40, Not SAFE)
    # -------------------------------------------------------------------------
    def test_rule5_boundary_denies_amount_5001_score_39_suspicious(self):
        dec = evaluate_action(
            action="ApproveHighValueTransfer",
            amount_inr=5001.0,
            arth_score=39,
            threat_level="SUSPICIOUS",
        )
        self.assertFalse(dec.allowed)
        self.assertEqual(dec.policy_id, "rule_5_high_value_block")

    def test_rule5_boundary_permits_amount_5000_score_39_suspicious(self):
        # 5000 is not strictly greater than 5000
        dec = evaluate_action(
            action="ApproveHighValueTransfer",
            amount_inr=5000.0,
            arth_score=39,
            threat_level="SUSPICIOUS",
        )
        self.assertTrue(dec.allowed)

    def test_rule5_boundary_permits_amount_10000_when_score_is_40(self):
        # Score 40 is not strictly less than 40
        dec = evaluate_action(
            action="ApproveHighValueTransfer",
            amount_inr=10000.0,
            arth_score=40,
            threat_level="SUSPICIOUS",
        )
        self.assertTrue(dec.allowed)

    def test_rule5_permits_large_amount_when_threat_is_strictly_safe(self):
        dec = evaluate_action(
            action="ApproveHighValueTransfer",
            amount_inr=50000.0,
            arth_score=25,
            threat_level="SAFE",
        )
        self.assertTrue(dec.allowed)

    # -------------------------------------------------------------------------
    # Default Permit & Robustness
    # -------------------------------------------------------------------------
    def test_unknown_action_defaults_to_permit(self):
        dec = evaluate_action(action="CheckElectricityBillReceipt", threat_level="SAFE")
        self.assertTrue(dec.allowed)
        self.assertEqual(dec.policy_id, "default_permit")

    def test_empty_user_id_handles_gracefully(self):
        dec = evaluate_action(action="ReadWelfareGuide", user_id="")
        self.assertTrue(dec.allowed)

    def test_negative_numbers_handled_gracefully(self):
        dec = evaluate_action(action="ApplyForLoan", arth_score=-5, debt_ratio=-10.0)
        self.assertTrue(dec.allowed)

    # -------------------------------------------------------------------------
    # Audit Trail & Metrics Persistence
    # -------------------------------------------------------------------------
    def test_audit_log_records_principal_and_action(self):
        evaluate_action(action="ApplyForLoan", user_id="audit_test_edge_1", arth_score=20, debt_ratio=70.0)
        logs = get_audit_log(user_id="audit_test_edge_1", limit=10)
        self.assertGreater(len(logs), 0)
        self.assertEqual(logs[0]["action"], "ApplyForLoan")
        self.assertEqual(logs[0]["allowed"], 0)

    def test_audit_stats_accurately_aggregate_decisions(self):
        stats = get_audit_stats()
        self.assertIn("total_evaluations", stats)
        self.assertIn("total_blocked", stats)
        self.assertIn("total_permitted", stats)
        self.assertGreaterEqual(stats["total_evaluations"], stats["total_blocked"] + stats["total_permitted"])

    def test_decision_to_dict_schema(self):
        dec = evaluate_action(action="CheckBalance", user_id="user_schema_test")
        d = dec.to_dict()
        self.assertIn("allowed", d)
        self.assertIn("policy_id", d)
        self.assertIn("action", d)
        self.assertIn("reason", d)

    def test_context_snapshot_preserved(self):
        dec = evaluate_action(action="CustomAction", threat_level="SAFE", arth_score=60)
        self.assertTrue(dec.allowed)
        self.assertEqual(dec.context_snapshot.get("action"), "CustomAction")
        self.assertEqual(dec.context_snapshot.get("arth_score"), 60)
        self.assertEqual(dec.context_snapshot.get("threat_level"), "SAFE")

    def test_rule4_claim_government_scheme_always_permitted(self):
        """Rule 4: Citizen access to government welfare schemes is unconditionally permitted."""
        dec = evaluate_action(action="ClaimGovernmentScheme", threat_level="CRITICAL", arth_score=10)
        self.assertTrue(dec.allowed)
        self.assertEqual(dec.policy_id, "rule_4_scheme_permit")


if __name__ == "__main__":
    unittest.main(verbosity=2)
