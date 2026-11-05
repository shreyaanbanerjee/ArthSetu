"""Vernacular language flows and scam defense test suite.

Tests regional Indian language processing across Hindi, Marathi, and Hinglish
for scam detection, intent classification, and welfare program matching.
"""

from __future__ import annotations

import unittest
from tools.scam_engine import run_scam_detection, extract_loan_terms, compute_true_apr
from agents.sutradhar import _classify_locally
from tools.scheme_matcher import match_schemes


class TestVernacularFlows(unittest.TestCase):
    """Test regional language processing and fraud detection."""

    def test_hindi_otp_theft_scam(self):
        """Detect Hindi OTP and account suspension threats."""
        text = "प्रिय ग्राहक, आपका एसबीआई बैंक खाता बंद होने जा रहा है। तुरंत अपना ओटीपी और पिन शेयर करें।"
        result = run_scam_detection(text)
        self.assertGreaterEqual(result["confidence"], 0.70)
        self.assertTrue(any("otp" in f.lower() or "urgent" in f.lower() for f in result["flags"]))

    def test_marathi_electricity_disconnection_scam(self):
        """Detect Marathi electricity bill fraud with fake APK link."""
        text = "महावितरण सूचना: तुमचे मागील महिन्याचे वीज बिल भरले नाही. आज रात्री वीज खंडित केली जाईल. बिल भरण्यासाठी खालील APK फाइल डाउनलोड करा आणि संपर्क करा."
        result = run_scam_detection(text)
        self.assertGreaterEqual(result["confidence"], 0.70)
        self.assertTrue(any("electricity" in f.lower() or "apk" in f.lower() or "urgent" in f.lower() for f in result["flags"]))

    def test_hinglish_advance_fee_loan_fraud(self):
        """Detect Hinglish advance fee loan scam."""
        text = "Congratulations! Aapka 50,000 ka loan approve ho gaya hai. Loan release karne ke liye Rs 500 processing fees turant bheje."
        result = run_scam_detection(text)
        self.assertGreaterEqual(result["confidence"], 0.70)
        self.assertTrue(any("fee" in f.lower() or "loan" in f.lower() or "lottery" in f.lower() for f in result["flags"]))

    def test_hindi_pm_svanidhi_scheme_matching(self):
        """Match PM SVANidhi scheme for Hindi street vendor profile."""
        profile = {
            "occupation": "street_vendor",
            "monthly_income_inr": 12000,
            "has_bank_account": True,
            "land_ownership": False,
        }
        matches = match_schemes(profile)
        scheme_ids = [m.get("scheme_id", "") for m in matches]
        self.assertIn("PM_SVANIDHI", scheme_ids)

    def test_marathi_farmer_scheme_matching(self):
        """Match PM-KISAN and Crop Insurance for farmer profile."""
        profile = {
            "occupation": "farmer",
            "monthly_income_inr": 18000,
            "land_ownership": True,
            "has_bank_account": True,
        }
        matches = match_schemes(profile)
        scheme_ids = [m.get("scheme_id", "") for m in matches]
        self.assertTrue("PM_KISAN" in scheme_ids or "PM_FASAL_BIMA" in scheme_ids or "KCC" in scheme_ids)

    def test_vernacular_intent_classification(self):
        """Test keyword intent classification across Hindi and Marathi queries."""
        # Scheme query in Hindi
        hi_scheme = "मुझे सरकारी yojana और subsidy के बारे में बताएं"
        res_scheme = _classify_locally(hi_scheme, "hi")
        self.assertEqual(res_scheme["intent"], "scheme")

        # Scam check query
        hi_scam = "क्या यह fraud और scam मैसेज है?"
        res_scam = _classify_locally(hi_scam, "hi")
        self.assertEqual(res_scam["intent"], "scam_check")

        # Stressed emotion detection
        hi_stressed = "बहुत परेशान हूँ, मेरी मदद करें"
        res_stressed = _classify_locally(hi_stressed, "hi")
        self.assertEqual(res_stressed["emotional_register"], "stressed")

    def test_vernacular_predatory_apr_computation(self):
        """Extract terms and flag predatory rate from Hindi loan message."""
        raw_msg = "लोन राशि ₹10,000, 3 महीने बाद आपको ₹18,000 चुकाना होगा।"
        terms = extract_loan_terms(raw_msg)
        self.assertEqual(terms.get("loan_amount_inr"), 10000.0)
        self.assertEqual(terms.get("repayment_stated"), 18000.0)
        self.assertEqual(terms.get("period_months"), 3)

        apr_info = compute_true_apr(
            principal=terms["loan_amount_inr"],
            total_repayment=terms["repayment_stated"],
            months=terms["period_months"],
        )
        self.assertTrue(apr_info["predatory_warning"])
        self.assertGreater(apr_info["apr_pct"], 36.0)


if __name__ == "__main__":
    unittest.main()
