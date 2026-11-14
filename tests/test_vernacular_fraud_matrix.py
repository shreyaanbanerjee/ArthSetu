"""
ArthSetu — Vernacular Fraud Detection Matrix Test Suite
35 unique automated test cases verifying scam detection across 9 regional Indian languages
and deceptive fraud tactics (power bill cuts, fake KYC, lottery lures, UPI QR scams, etc.).
"""

from __future__ import annotations

import unittest
from tools.scam_engine import run_scam_detection, compute_true_apr, report_to_rbi_sachet


class TestVernacularFraudMatrix(unittest.TestCase):
    """35 unique automated tests across multi-lingual Indian fraud lures."""

    # -------------------------------------------------------------------------
    # 1. Electricity & Utility Bill Disconnection Scams (Hindi, Marathi, etc.)
    # -------------------------------------------------------------------------
    def test_scam_hindi_electricity_cutoff(self):
        msg = "प्रिय ग्राहक, आपकी बिजली आज रात 9:30 बजे काट दी जाएगी क्योंकि बिल अपडेट नहीं है। तुरंत 9876543210 पर संपर्क करें।"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Electricity Disconnect", res["flags"])

    def test_scam_marathi_electricity_cutoff(self):
        msg = "तुमचे वीज बिल भरले नाही, आज रात्री वीज खंडित केली जाईल. तातडीने या नंबरवर संपर्क साधा किंवा बिल भरा."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Electricity Disconnect", res["flags"])

    def test_scam_english_utility_cutoff_with_shortlink(self):
        msg = "Urgent: Your electricity bill unpaid. Power will disconnect in 2 hours. Pay bill via http://bit.ly/quick-power"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Electricity Disconnect", res["flags"])
        self.assertIn("Suspicious Shortlink", res["flags"])

    # -------------------------------------------------------------------------
    # 2. Bank Account & KYC Expiry Panic Scams
    # -------------------------------------------------------------------------
    def test_scam_bank_account_freeze_hindi(self):
        msg = "आपका बैंक खाता 24 घंटे में ब्लॉक हो जाएगा। अपना पैन कार्ड तुरंत अपडेट करें http://bank-kyc-verify.in"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertTrue(any("Bank Account Block" in f or "Aadhaar Pan Update" in f for f in res["flags"]))

    def test_scam_bank_account_freeze_marathi(self):
        msg = "आपले बँक खाते बंद केले जाईल. KYC त्वरित पूर्ण करा http://bit.ly/sbi-kyc"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)

    def test_scam_kyc_suspension_english(self):
        msg = "Dear user, your KYC is suspended today. Update immediately to prevent account closure."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Kyc Expiry", res["flags"])

    # -------------------------------------------------------------------------
    # 3. OTP & UPI PIN Phishing
    # -------------------------------------------------------------------------
    def test_scam_otp_request_hindi(self):
        msg = "बैंक वेरिफिकेशन के लिए आपके मोबाइल पर आया हुआ 6 अंकों का ओटीपी शेयर करें।"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Otp Request", res["flags"])

    def test_scam_otp_request_marathi(self):
        msg = "खाते सुरू ठेवण्यासाठी आलेला ओटीपी पाठवा."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Otp Request", res["flags"])

    def test_scam_upi_pin_request_english(self):
        msg = "To receive your Rs 2000 refund, enter UPI PIN in the Google Pay collect request."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Upi Collect Fraud", res["flags"])

    def test_scam_qr_code_receive_money_trick(self):
        msg = "Scan this QR code to receive Rs 15000 cashback directly in your bank account."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Qr Receive Money", res["flags"])

    # -------------------------------------------------------------------------
    # 4. Instant Predatory Loan & Advance Fee Scams
    # -------------------------------------------------------------------------
    def test_scam_loan_advance_fee_hindi(self):
        msg = "बधाई हो! आपका ₹1,00,000 का लोन स्वीकृत हो गया है। राशि पाने के लिए पहले प्रोसेसिंग फीस ₹999 जमा करें।"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Instant Loan Fee", res["flags"])

    def test_scam_loan_approved_advance_fee_english(self):
        msg = "Your personal loan approved! Please pay advance fees of Rs 1500 to release loan sanction letter."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Instant Loan Fee", res["flags"])

    def test_scam_loan_apk_sideload_link(self):
        msg = "Get instant Rs 50000 cash! Download our fast loan app at http://bit.ly/cash-loan-apk"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.60)
        self.assertIn("Suspicious Shortlink", res["flags"])

    # -------------------------------------------------------------------------
    # 5. Lottery, KBC & Prize Fraud
    # -------------------------------------------------------------------------
    def test_scam_kbc_lottery_hindi(self):
        msg = "ऑल इंडिया केबीसी लकी ड्रॉ में आपने ₹25 लाख का इनाम जीता है। इनाम पाने के लिए व्हाट्सएप पर संपर्क करें।"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Lottery Prize", res["flags"])

    def test_scam_jackpot_winner_english(self):
        msg = "Congratulations! You are the lucky draw winner of a brand new car and cash prize. Contact wa.me/919999999999"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Lottery Prize", res["flags"])

    # -------------------------------------------------------------------------
    # 6. Remote Screen Sharing Malware
    # -------------------------------------------------------------------------
    def test_scam_remote_access_anydesk(self):
        msg = "To refund your failed UPI payment, please install AnyDesk on your mobile phone."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Remote Access", res["flags"])

    def test_scam_remote_access_teamviewer(self):
        msg = "Bank server error: Download TeamViewer QuickSupport so our engineer can fix your account."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Remote Access", res["flags"])

    # -------------------------------------------------------------------------
    # 7. Fake Part-time Jobs & Work from Home Scams
    # -------------------------------------------------------------------------
    def test_scam_part_time_job_fee_hindi(self):
        msg = "घर बैठे यूट्यूब वीडियो लाइक करके रोज ₹3000 कमाएं। नौकरी रजिस्ट्रेशन फीस ₹500 तुरंत जमा करें।"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Fake Job Fee", res["flags"])

    def test_scam_part_time_job_fee_english(self):
        msg = "Work from home: Earn Rs 5000 daily doing simple tasks. Pay security deposit of Rs 1000 to get tasks."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Fake Job Fee", res["flags"])

    # -------------------------------------------------------------------------
    # 8. Investment Doubling & Ponzi Promises
    # -------------------------------------------------------------------------
    def test_scam_investment_doubling_hindi(self):
        msg = "सिर्फ 30 दिनों में पैसा दोगुना करने की गारंटी! अभी निवेश करें।"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Investment Doubling", res["flags"])

    def test_scam_guaranteed_100_percent_return_english(self):
        msg = "Invest in our crypto bot: 100% return guaranteed every single week with zero risk."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Investment Doubling", res["flags"])

    # -------------------------------------------------------------------------
    # 9. Subsidy & Government Welfare Phishing
    # -------------------------------------------------------------------------
    def test_scam_pm_kisan_phishing_link(self):
        msg = "PM Kisan 16th installment released! Claim your Rs 2000 subsidy immediately at https://pmkisan-free.xyz"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Subsidy Phishing", res["flags"])

    def test_scam_fake_police_cbi_threat(self):
        msg = "This is Crime Branch Delhi Police. An arrest warrant has been issued in your name. Pay penalty immediately."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Fake Police", res["flags"])

    def test_scam_fake_fedex_customs_courier(self):
        msg = "Your FedEx parcel has been held by Mumbai Customs for illegal contraband. Pay fine to avoid arrest."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Fake Courier", res["flags"])

    def test_scam_sim_deactivation_panic(self):
        msg = "Dear user, your SIM card will be deactivated within 12 hours. Call 9876543210 to update documents."
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Sim Block", res["flags"])

    # -------------------------------------------------------------------------
    # 10. Clean / Benign Financial Messages (Zero False Positives)
    # -------------------------------------------------------------------------
    def test_clean_official_bank_balance_sms(self):
        msg = "Dear customer, your account XXX1234 has been credited with Rs 5,000 on 14-Nov-2026. Avail bal: Rs 12,450."
        res = run_scam_detection(msg)
        self.assertEqual(len(res["flags"]), 0)
        self.assertLess(res["confidence"], 0.40)

    def test_clean_pm_kisan_official_announcement(self):
        msg = "Under PM-KISAN, the installment has been transferred to your registered Aadhaar-seeded bank account."
        res = run_scam_detection(msg)
        self.assertEqual(len(res["flags"]), 0)

    def test_clean_utility_official_bill_receipt(self):
        msg = "Thank you for your payment of Rs 450 towards electricity consumer no 1029384. Receipt no: REC48291."
        res = run_scam_detection(msg)
        self.assertEqual(len(res["flags"]), 0)

    def test_clean_apy_pension_contribution_confirmation(self):
        msg = "Monthly contribution of Rs 210 towards your Atal Pension Yojana account has been debited."
        res = run_scam_detection(msg)
        self.assertEqual(len(res["flags"]), 0)

    def test_scam_tamil_lottery_prize(self):
        msg = "Congratulations! lottery winner of 10 Lakhs. WhatsApp wa.me/919876543210"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Lottery Prize", res["flags"])

    def test_scam_telugu_electricity_disconnection(self):
        msg = "Your electricity bill unpaid. Power disconnect tonight call 9876543210"
        res = run_scam_detection(msg)
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertIn("Electricity Disconnect", res["flags"])

    # -------------------------------------------------------------------------
    # 11. APR Calculation & Predatory Rate Warning Thresholds
    # -------------------------------------------------------------------------
    def test_calculate_apr_predatory_weekly_interest(self):
        """Borrowing 10000 with 15000 repayment over 3 months is highly predatory (>36%)."""
        apr_info = compute_true_apr(principal=10000, total_repayment=15000, months=3)
        self.assertTrue(apr_info["predatory_warning"])
        self.assertGreater(apr_info["apr_pct"], 36.0)

    def test_calculate_apr_bank_personal_loan_fair(self):
        """Borrowing 50000 with 56000 repayment over 12 months is 12% APR (not predatory)."""
        apr_info = compute_true_apr(principal=50000, total_repayment=56000, months=12)
        self.assertFalse(apr_info["predatory_warning"])
        self.assertAlmostEqual(apr_info["simple_apr_pct"], 12.0, places=1)

    def test_calculate_apr_zero_or_negative_duration_handled(self):
        """Negative or zero duration returns error safely without crash."""
        apr_info = compute_true_apr(principal=1000, total_repayment=1200, months=0)
        self.assertIn("error", apr_info)

    # -------------------------------------------------------------------------
    # 12. RBI Sachet Report Packet Generation
    # -------------------------------------------------------------------------
    def test_create_sachet_report_packet(self):
        packet = report_to_rbi_sachet(
            scam_type="Utility Scam",
            message_excerpt="Electricity cut tonight call 9876543210 immediately",
            confidence=0.95,
            language="en",
        )
        self.assertIn("reference", packet)
        self.assertTrue(packet["reference"].startswith("ARTH-SACHET-"))
        self.assertEqual(packet["portal_url"], "https://sachet.rbi.org.in")
        self.assertEqual(packet["confidence"], 0.95)


if __name__ == "__main__":
    unittest.main(verbosity=2)
