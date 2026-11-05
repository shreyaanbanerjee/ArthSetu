"""Unit tests for the Prahari Scam Detection Engine and APR Calculator."""

from __future__ import annotations

import unittest
from tools.scam_engine import (
    compute_true_apr,
    extract_loan_terms,
    report_to_rbi_sachet,
    run_scam_detection,
)


class TestScamEngine(unittest.TestCase):
    def test_detect_otp_phishing(self):
        """Detect OTP and UPI PIN theft attempts."""
        text = "URGENT: Please share your UPI PIN or OTP immediately to claim your refund."
        res = run_scam_detection(text)
        self.assertGreaterEqual(res["confidence"], 0.85)
        self.assertEqual(res["matched_pattern"], "otp_request")
        self.assertIn("matches", res)

    def test_detect_electricity_disconnect_scam(self):
        """Detect electricity bill disconnection scam."""
        text = "Dear customer, your electricity power will be disconnect tonight at 9:30 PM. Pay bill at http://bill.in"
        res = run_scam_detection(text)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("electricity_disconnect", [m["name"] for m in res["matches"]])

    def test_detect_kyc_expiry_scam(self):
        """Detect fake KYC expiry and account blocking scam."""
        text = "Your bank account has been blocked due to KYC expire. Click https://kyc-update.com to verify."
        res = run_scam_detection(text)
        self.assertGreaterEqual(res["confidence"], 0.80)
        self.assertIn("kyc_expiry", [m["name"] for m in res["matches"]])

    def test_detect_remote_access_scam(self):
        """Detect AnyDesk / TeamViewer remote access fraud."""
        text = "Customer care agent here, please install AnyDesk on your mobile for bank verification."
        res = run_scam_detection(text)
        self.assertGreaterEqual(res["confidence"], 0.85)
        self.assertEqual(res["matched_pattern"], "remote_access")

    def test_detect_guaranteed_return_scam(self):
        """Detect 100% guaranteed double money schemes."""
        text = "Invest ₹10,000 today and get 100% return guaranteed double in 3 days!"
        res = run_scam_detection(text)
        self.assertGreaterEqual(res["confidence"], 0.85)
        self.assertEqual(res["matched_pattern"], "investment_doubling")

    def test_clean_financial_query_no_scam(self):
        """Ensure legitimate financial inquiries are not flagged as scams."""
        text = "What is the current interest rate for Post Office Public Provident Fund (PPF)?"
        res = run_scam_detection(text)
        self.assertLess(res["confidence"], 0.40)
        self.assertIsNone(res["matched_pattern"])

    def test_apr_calculator_predatory_loan(self):
        """Flag predatory loans exceeding 36% APR."""
        # Borrow 5000, repay 7500 in 1 month = predatory
        apr = compute_true_apr(principal=5000.0, total_repayment=7500.0, months=1)
        self.assertTrue(apr["predatory_warning"])
        self.assertGreater(apr["apr_pct"], 36.0)
        self.assertEqual(apr["interest"], 2500.0)

    def test_apr_calculator_fair_loan(self):
        """Fair institutional bank loan within standard limits."""
        # Borrow 100,000, repay 110,000 over 12 months = ~10% APR
        apr = compute_true_apr(principal=100000.0, total_repayment=110000.0, months=12)
        self.assertFalse(apr["predatory_warning"])
        self.assertLess(apr["apr_pct"], 36.0)

    def test_apr_calculator_invalid_inputs(self):
        """Handle zero or negative inputs safely."""
        res = compute_true_apr(principal=-100.0, total_repayment=200.0, months=6)
        self.assertIn("error", res)

    def test_extract_loan_terms(self):
        """Extract principal and repayment amounts from natural language."""
        text = "I took a loan of ₹10,000 and have to repay ₹14,000 in 3 months"
        terms = extract_loan_terms(text)
        self.assertEqual(terms.get("loan_amount_inr"), 10000.0)
        self.assertEqual(terms.get("repayment_stated"), 14000.0)
        self.assertEqual(terms.get("period_months"), 3)

    def test_report_to_rbi_sachet(self):
        """Generate structured RBI Sachet report packet with reference code."""
        packet = report_to_rbi_sachet(
            scam_type="electricity_disconnect",
            message_excerpt="Electricity bill scam with phishing link",
            confidence=0.88,
            language="en",
        )
        self.assertIn("reference", packet)
        self.assertTrue(packet["reference"].startswith("ARTH-SACHET-"))
        self.assertEqual(packet["status"], "prepared_for_manual_filing")
        self.assertEqual(packet["confidence"], 0.88)


if __name__ == "__main__":
    unittest.main()
